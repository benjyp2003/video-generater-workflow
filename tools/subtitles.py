"""Captions -> videos/<id>/final.srt

Usage: python3 -m tools.subtitles videos/<id> [--mode script|whisper] [--model small]

Modes
  script  (default) Caption text comes from script.md (exact spelling, no model).
          Timing: scene boundaries from media/build/segments/<scene>.mp4 and
          narration length from media/audio/<scene>.wav; inside a scene, cues
          are spaced proportionally to their length. Needs `make video` first.
  whisper Transcribe media/build/final.mp4 (or --input FILE, e.g. a Kdenlive
          export) with faster-whisper, then apply channel/glossary.yaml fixes.
          Use for human narration or hand-edited videos.

Always read the result once: captions are part of Gate 2.
"""
from __future__ import annotations

import argparse
import re
import sys
import textwrap
from pathlib import Path

from tools.assemble import duration
from tools.scriptdoc import load_script, load_yaml

ROOT = Path(__file__).resolve().parents[1]
LINE = 42          # characters per line
LINES_PER_CUE = 2


def ts(seconds: float) -> str:
    ms = max(0, round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def to_srt(cues: list[tuple[float, float, str]]) -> str:
    return "\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n" for i, (a, b, t) in enumerate(cues, 1))


def chunk_text(text: str) -> list[str]:
    """Split narration into cues of at most two ~42-char lines, preferring sentence ends."""
    text = text.replace("`", "")
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    cues: list[str] = []
    for sentence in filter(None, sentences):
        lines = textwrap.wrap(sentence, LINE)
        for i in range(0, len(lines), LINES_PER_CUE):
            cues.append("\n".join(lines[i:i + LINES_PER_CUE]))
    return cues


def script_cues(video_dir: Path) -> list[tuple[float, float, str]]:
    script = load_script(video_dir)
    seg_dir = video_dir / "media" / "build" / "segments"
    cues: list[tuple[float, float, str]] = []
    offset = 0.0
    for scene in script.scenes:
        seg = seg_dir / f"{scene.id}.mp4"
        if not seg.exists():
            raise SystemExit(f"missing {seg}: run `make video` (or `make draft`) first")
        seg_len = duration(seg)
        audio = video_dir / "media" / "audio" / f"{scene.id}.wav"
        speech = min(duration(audio), seg_len) if audio.exists() else seg_len
        chunks = chunk_text(scene.narration) if scene.narration else []
        total = sum(len(c) for c in chunks) or 1
        t = offset
        for c in chunks:
            d = speech * len(c) / total
            cues.append((t, t + d, c))
            t += d
        offset += seg_len
    return cues


def apply_glossary(text: str, glossary: dict[str, str]) -> str:
    for wrong, right in glossary.items():
        text = re.sub(rf"\b{re.escape(wrong)}\b", right, text, flags=re.IGNORECASE)
    return text


def whisper_cues(media: Path, model_size: str, glossary: dict[str, str]
                 ) -> list[tuple[float, float, str]]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:  # pragma: no cover - optional dependency
        raise SystemExit("faster-whisper not installed: pip install -r requirements-audio.txt")
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    # Priming with the correct spellings improves recognition of jargon.
    prompt = ", ".join(sorted(set(glossary.values())))
    segments, _ = model.transcribe(str(media), language="en", initial_prompt=prompt,
                                   vad_filter=True)
    cues = []
    for seg in segments:
        text = "\n".join(textwrap.wrap(apply_glossary(seg.text.strip(), glossary), LINE))
        cues.append((seg.start, seg.end, text))
    return cues


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video_dir", type=Path)
    ap.add_argument("--mode", choices=["script", "whisper"], default="script")
    ap.add_argument("--model", default=None, help="faster-whisper model (default: video.yaml providers.stt or small)")
    ap.add_argument("--input", type=Path, help="media to transcribe in whisper mode")
    a = ap.parse_args(argv)

    if a.mode == "script":
        cues = script_cues(a.video_dir)
    else:
        manifest = load_yaml(a.video_dir / "video.yaml")
        model = a.model or (manifest.get("providers") or {}).get("stt") or "small"
        media = a.input or a.video_dir / "media" / "build" / "final.mp4"
        cues = whisper_cues(media, model, load_yaml(ROOT / "channel" / "glossary.yaml"))

    out = a.video_dir / "final.srt"
    out.write_text(to_srt(cues), encoding="utf-8")
    print(f"wrote {out} ({len(cues)} cues)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
