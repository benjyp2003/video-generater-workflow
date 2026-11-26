"""Assemble media/build/final.mp4 from the storyboard with FFmpeg.

Usage: python3 -m tools.assemble videos/<id> [--draft] [--force] [--no-loudnorm]

Pipeline:
  1. regenerate storyboard.yaml from script.md (+ overrides)
  2. per scene: render visuals for the narration's duration and mux the audio
     -> media/build/segments/<scene>.mp4  (skipped when inputs are unchanged)
  3. concat segments (stream copy) and normalise loudness -> final.mp4

Scene duration = narration + pad_after_s (images), or max(clip, narration + pad)
for video clips (the last frame is held). Several visuals in one scene share
the duration equally.

--draft replaces missing visuals with a plain card and missing narration with
silence, so you can watch an animatic before everything exists. Without it,
missing inputs are listed and nothing is rendered.

Best for diagram/slide-driven formats (concept, comparison, architecture,
short). Tutorials with heavy screen editing stay in a desktop editor (ADR-005).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from tools import storyboard as sbmod

BG = "0x0F172A"
IMAGE_MARGIN = 0.07  # safe area around stills; keeps edges visible during zoom
LOUDNESS = "loudnorm=I=-14:TP=-1.5:LRA=11"  # YouTube-style target; verify for your needs
V_CODEC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p"]
A_CODEC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def ffmpeg(*args: str) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd)}\n{r.stderr.strip()}")


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise RuntimeError(f"cannot read duration of {path}: {r.stderr.strip()}") from None


def is_video(path: Path) -> bool:
    return path.suffix.lower() in sbmod.VIDEO_EXT


def fit_filter(w: int, h: int, fps: int, margin: float = 0.0) -> str:
    """Letterbox into w x h on the brand background, keeping `margin` free on each side."""
    iw, ih = int(w * (1 - 2 * margin)) // 2 * 2, int(h * (1 - 2 * margin)) // 2 * 2
    return (f"scale={iw}:{ih}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={BG},setsar=1,fps={fps},format=yuv420p")


def render_visual(src: Path | None, dur: float, w: int, h: int, fps: int, motion: str,
                  out: Path) -> None:
    """Video-only clip of exactly `dur` seconds."""
    if src is None:
        ffmpeg("-f", "lavfi", "-i", f"color=c=0x334155:s={w}x{h}:r={fps}", "-t", f"{dur:.3f}",
               *V_CODEC, str(out))
    elif is_video(src):
        hold = max(0.0, dur - duration(src))
        vf = fit_filter(w, h, fps) + (f",tpad=stop_mode=clone:stop_duration={hold:.3f}" if hold else "")
        ffmpeg("-i", str(src), "-vf", vf, "-t", f"{dur:.3f}", "-an", *V_CODEC, str(out))
    else:
        vf = fit_filter(w, h, fps, IMAGE_MARGIN)
        if motion == "zoom":
            frames = max(1, int(dur * fps))
            vf += (f",scale={w * 2}:{h * 2},zoompan=z='1+0.08*on/{frames}':"
                   f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps={fps}")
        ffmpeg("-loop", "1", "-framerate", str(fps), "-i", str(src), "-vf", vf,
               "-t", f"{dur:.3f}", *V_CODEC, str(out))


def scene_inputs(video_dir: Path, scene: dict) -> list[Path]:
    paths = [scene.get("narration")] + [v.get("src") for v in scene["visuals"]]
    return [video_dir / p for p in paths if p]


def fingerprint(video_dir: Path, scene: dict, sb: dict) -> str:
    """Changes when the scene, its input files, or this renderer's code change."""
    h = hashlib.sha256(json.dumps([scene, sb["resolution"], sb["fps"]], sort_keys=True).encode())
    h.update(Path(__file__).read_bytes())
    for p in scene_inputs(video_dir, scene):
        if p.exists():
            st = p.stat()
            h.update(f"{p}:{st.st_size}:{st.st_mtime_ns}".encode())
    return h.hexdigest()[:16]


def render_scene(video_dir: Path, scene: dict, sb: dict, out: Path, draft: bool) -> None:
    w, h = (int(x) for x in sb["resolution"].split("x"))
    fps = int(sb["fps"])
    narr = video_dir / scene["narration"] if scene.get("narration") else None
    if narr is not None and not narr.exists():
        narr = None  # only reachable in draft mode
    audio_len = duration(narr) if narr else 0.0
    dur = max(scene["min_duration_s"], audio_len + scene["pad_after_s"])
    srcs = [video_dir / v["src"] if v.get("src") else None for v in scene["visuals"]] or [None]
    for s in srcs:
        if s is not None and is_video(s):
            dur = max(dur, duration(s))
    share = dur / len(srcs)

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        parts = []
        for i, s in enumerate(srcs):
            part = tdp / f"v{i}.mp4"
            render_visual(s, share, w, h, fps, scene.get("motion", "none"), part)
            parts.append(part)
        listing = tdp / "list.txt"
        listing.write_text("".join(f"file '{p}'\n" for p in parts))
        video_only = tdp / "video.mp4"
        ffmpeg("-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(video_only))
        audio_in = ["-i", str(narr)] if narr else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        tmp = out.with_suffix(".tmp.mp4")
        ffmpeg("-i", str(video_only), *audio_in, "-map", "0:v", "-map", "1:a",
               "-af", "apad", "-t", f"{dur:.3f}", "-c:v", "copy", *A_CODEC, str(tmp))
        os.replace(tmp, out)


def missing_inputs(video_dir: Path, sb: dict) -> list[str]:
    out = []
    for s in sb["scenes"]:
        if s.get("narration") and not (video_dir / s["narration"]).exists():
            out.append(f"{s['id']}: narration {s['narration']} (run make audio)")
        for v in s["visuals"]:
            if not v.get("src"):
                out.append(f"{s['id']}: visual {v['type']}:{v['name']}")
        if not s["visuals"]:
            out.append(f"{s['id']}: no [VISUAL] in script.md")
    return out


def assemble(video_dir: Path, draft: bool = False, force: bool = False,
             loudnorm: bool = True) -> Path:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found on PATH")
    sb = sbmod.write(video_dir)
    missing = missing_inputs(video_dir, sb)
    if missing and not draft:
        raise SystemExit("missing inputs (use --draft for placeholders):\n  " + "\n  ".join(missing))
    for m in missing:
        print(f"draft placeholder: {m}")

    seg_dir = video_dir / "media" / "build" / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    fp_file = seg_dir / ".fingerprints.json"
    fps_state = json.loads(fp_file.read_text()) if fp_file.exists() else {}
    segments = []
    for scene in sb["scenes"]:
        out = seg_dir / f"{scene['id']}.mp4"
        fp = fingerprint(video_dir, scene, sb) + ("-draft" if draft else "")
        if not force and out.exists() and fps_state.get(scene["id"]) == fp:
            print(f"up to date: {scene['id']}")
        else:
            render_scene(video_dir, scene, sb, out, draft)
            fps_state[scene["id"]] = fp
            fp_file.write_text(json.dumps(fps_state, indent=2, sort_keys=True))
            print(f"rendered: {scene['id']}")
        segments.append(out)

    final = video_dir / "media" / "build" / ("draft.mp4" if draft else "final.mp4")
    listing = seg_dir / "concat.txt"
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in segments))
    tmp = final.with_suffix(".tmp.mp4")
    audio = ["-af", LOUDNESS, *A_CODEC] if loudnorm else ["-c:a", "copy"]
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(listing), "-c:v", "copy", *audio,
           "-movflags", "+faststart", str(tmp))
    os.replace(tmp, final)
    print(f"wrote {final} ({duration(final):.1f}s)")
    return final


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video_dir", type=Path)
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-loudnorm", action="store_true")
    a = ap.parse_args(argv)
    assemble(a.video_dir, a.draft, a.force, not a.no_loudnorm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
