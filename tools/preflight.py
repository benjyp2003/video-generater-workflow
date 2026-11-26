"""Gate 2/3 helper: is this video safe to upload?

Usage: python3 -m tools.preflight videos/<id>

Checks (all must pass; exit 1 otherwise):
  - claim check passes (tools.check_claims) and approvals.technical is set
  - approvals.final_qa is set (you watched the whole video)
  - publish.yaml: title, description with Sources, visibility == private,
    altered_or_synthetic decided (true/false), made_for_kids decided
  - thumbnail and captions exist; final.mp4 exists
  - every asset in assets.yaml has a licence
  - no obvious secrets in human-authored text files

It never uploads anything. Upload stays manual and private (ADR-007).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from tools.check_claims import check as check_claims
from tools.scriptdoc import load_yaml

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                       # AWS access key id
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),                  # common API key prefix
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),             # GitHub tokens
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"xox[abpr]-[A-Za-z0-9-]{10,}"),            # Slack tokens
]
TEXT_GLOBS = ("*.md", "*.yaml", "*.srt", "demo/*.sh", "demo/*.tape", "diagrams/*.mmd", "slides/*.md")


def scan_secrets(video_dir: Path) -> list[str]:
    hits = []
    for pattern in TEXT_GLOBS:
        for f in video_dir.glob(pattern):
            text = f.read_text(encoding="utf-8", errors="ignore")
            for rx in SECRET_PATTERNS:
                if rx.search(text):
                    hits.append(f"possible secret ({rx.pattern[:20]}…) in {f.relative_to(video_dir)}")
    return hits


def preflight(video_dir: Path) -> list[str]:
    problems: list[str] = []
    manifest = load_yaml(video_dir / "video.yaml")
    publish = load_yaml(video_dir / "publish.yaml")
    approvals = manifest.get("approvals") or {}

    errors, _ = check_claims(video_dir)
    problems += [f"claims: {e}" for e in errors]
    for gate in ("technical", "final_qa"):
        if not approvals.get(gate):
            problems.append(f"video.yaml approvals.{gate} is not filled in")

    if not (publish.get("title") or "").strip():
        problems.append("publish.yaml: title is empty")
    desc = publish.get("description") or ""
    if "Sources:" not in desc or not re.search(r"https?://", desc):
        problems.append("publish.yaml: description must list Sources with URLs")
    if publish.get("visibility") != "private":
        problems.append("publish.yaml: visibility must be 'private' for upload")
    if publish.get("altered_or_synthetic") not in (True, False):
        problems.append("publish.yaml: altered_or_synthetic must be decided (true/false)")
    if publish.get("made_for_kids") not in (True, False):
        problems.append("publish.yaml: made_for_kids must be decided (true/false)")

    for key, default in (("thumbnail", "thumbnail.png"), ("captions", "final.srt")):
        if not (video_dir / (publish.get(key) or default)).exists():
            problems.append(f"missing {publish.get(key) or default}")
    if not (video_dir / "media" / "build" / "final.mp4").exists():
        problems.append("missing media/build/final.mp4 (or export your editor's render there)")

    for a in (load_yaml(video_dir / "assets.yaml").get("assets") or []):
        if not a.get("license"):
            problems.append(f"assets.yaml: {a.get('path')} has no licence")

    problems += scan_secrets(video_dir)
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    problems = preflight(Path(argv[1]))
    for p in problems:
        print(f"FAIL: {p}")
    print("preflight OK — upload as PRIVATE, review on a phone, then fill approvals.publish"
          if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
