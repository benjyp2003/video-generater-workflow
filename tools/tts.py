"""Narration: script.md scenes -> media/audio/<scene>.wav, one file per scene.

Usage: python3 -m tools.tts videos/<id> [--scenes s01,s03] [--force] [--provider NAME]

Providers (video.yaml `providers.tts`, overridable with --provider):
  kokoro       local Kokoro-82M TTS (pip install -r requirements-audio.txt)
  placeholder  silent WAV sized at ~150 words/min — preview timing/assembly
               before the real voice exists
  human        you record media/audio/<scene>.wav yourself; this command lists
               missing recordings and scenes whose text changed since recording

Only scenes whose (provider, voice, speed, spoken text) changed are regenerated:
fingerprints live in media/audio/.fingerprints.json. Writes are atomic.

Provider calls are isolated in PROVIDERS. Add a function there to add a provider;
a formal adapter interface is deliberately not built yet (ADR-006).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import wave
from pathlib import Path
from typing import Callable

from tools.scriptdoc import load_script, load_yaml

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 24_000
WORDS_PER_MIN = 150

Synth = Callable[[str, Path, dict], None]


def apply_pronunciations(text: str, mapping: dict[str, str]) -> str:
    for word, spoken in mapping.items():
        text = re.sub(rf"(?<![\w-]){re.escape(word)}(?![\w-])", spoken, text)
    # Inline code backticks are for the script reader, not the voice.
    return text.replace("`", "")


def fingerprint(provider: str, cfg: dict, text: str) -> str:
    key = json.dumps({"p": provider, "v": cfg.get("tts_voice"), "s": cfg.get("tts_speed"),
                      "t": text}, sort_keys=True)
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def write_wav(path: Path, samples: bytes, rate: int = SAMPLE_RATE) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples)


def synth_placeholder(text: str, out: Path, cfg: dict) -> None:
    seconds = max(1.0, len(text.split()) / WORDS_PER_MIN * 60 / float(cfg.get("tts_speed") or 1))
    write_wav(out, b"\x00\x00" * int(seconds * SAMPLE_RATE))


_kokoro_pipeline = None


def synth_kokoro(text: str, out: Path, cfg: dict) -> None:
    global _kokoro_pipeline
    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except ImportError as e:  # pragma: no cover - depends on optional deps
        raise SystemExit(f"kokoro not installed ({e}); pip install -r requirements-audio.txt")
    if _kokoro_pipeline is None:
        _kokoro_pipeline = KPipeline(lang_code=cfg.get("tts_lang", "a"))  # 'a' = American English
    chunks = [audio for _, _, audio in _kokoro_pipeline(
        text, voice=cfg.get("tts_voice", "af_heart"), speed=float(cfg.get("tts_speed") or 1))]
    sf.write(str(out), np.concatenate(chunks), SAMPLE_RATE, format="WAV")


PROVIDERS: dict[str, Synth] = {
    "kokoro": synth_kokoro,
    "placeholder": synth_placeholder,
}


def run(video_dir: Path, scenes: list[str] | None, force: bool, provider: str | None) -> int:
    manifest = load_yaml(video_dir / "video.yaml")
    cfg = dict(manifest.get("providers") or {})
    provider = provider or cfg.get("tts", "kokoro")
    pron = load_yaml(ROOT / "channel" / "pronunciations.yaml")
    script = load_script(video_dir)
    out_dir = video_dir / "media" / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    fp_file = out_dir / ".fingerprints.json"
    fps: dict[str, str] = json.loads(fp_file.read_text()) if fp_file.exists() else {}

    unknown = set(scenes or []) - {s.id for s in script.scenes}
    if unknown:
        print(f"unknown scene(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2

    problems = 0
    for scene in script.scenes:
        if scenes and scene.id not in scenes:
            continue
        if not scene.narration:
            continue
        spoken = apply_pronunciations(scene.narration, pron)
        fp = fingerprint(provider, cfg, spoken)
        out = out_dir / f"{scene.id}.wav"

        if provider == "human":
            if not out.exists():
                print(f"record: {out}  ({scene.word_count} words)")
                problems += 1
            elif scene.id in fps and fps[scene.id] != fp:
                print(f"re-record: {out}  (narration changed since it was recorded)")
                problems += 1
            else:
                fps[scene.id] = fp
            continue

        if not force and out.exists() and fps.get(scene.id) == fp:
            print(f"up to date: {scene.id}")
            continue
        synth = PROVIDERS.get(provider)
        if synth is None:
            print(f"unknown tts provider {provider!r}; known: {sorted(PROVIDERS)} or human",
                  file=sys.stderr)
            return 2
        tmp = out.with_suffix(".tmp.wav")
        synth(spoken, tmp, cfg)
        os.replace(tmp, out)
        fps[scene.id] = fp
        print(f"generated: {out}")

    tmp_fp = fp_file.with_suffix(".tmp")
    tmp_fp.write_text(json.dumps(fps, indent=2, sort_keys=True))
    os.replace(tmp_fp, fp_file)
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video_dir", type=Path)
    ap.add_argument("--scenes", help="comma-separated scene ids")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--provider")
    a = ap.parse_args(argv)
    scenes = [s.strip() for s in a.scenes.split(",")] if a.scenes else None
    return run(a.video_dir, scenes, a.force, a.provider)


if __name__ == "__main__":
    sys.exit(main())
