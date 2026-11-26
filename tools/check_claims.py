"""Gate-1 helper: verify every factual reference in script.md is backed.

Usage: python3 -m tools.check_claims videos/<id>

Errors (exit 1):
  - scene cites a claim that is not in research.md
  - scene cites a claim whose status is not `verified`
  - a cited claim has no sources, or cites a source id missing from sources.yaml
  - a claim has an unknown status
Warnings (exit 0):
  - scene with narration but no [CLAIM] (fine for hooks/recaps — review it)
  - scene narration over 120 words
  - [CMD] not present in demo/commands.sh (it was never run in the sandbox)

This is a helper, not the gate: a human still reads the sources.
"""
from __future__ import annotations

import sys
from pathlib import Path

from tools.scriptdoc import VALID_STATUSES, ParseError, load_claims, load_script, load_source_ids

MAX_WORDS = 120


def check(video_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    script = load_script(video_dir)
    claims = load_claims(video_dir)
    sources = load_source_ids(video_dir)
    commands_file = video_dir / "demo" / "commands.sh"
    demo_text = commands_file.read_text(encoding="utf-8") if commands_file.exists() else ""

    for c in claims.values():
        if c.status not in VALID_STATUSES:
            errors.append(f"{c.id}: unknown status {c.status!r} (use {sorted(VALID_STATUSES)})")

    cited: set[str] = set()
    for s in script.scenes:
        where = f"{s.id} (script.md:{s.line})"
        for cid in s.claims:
            cited.add(cid)
            claim = claims.get(cid)
            if claim is None:
                errors.append(f"{where}: cites {cid}, which is not in research.md")
                continue
            if claim.status != "verified":
                errors.append(f"{where}: cites {cid} with status {claim.status!r}")
            if not claim.sources:
                errors.append(f"{where}: {cid} has no sources")
            for sid in claim.sources:
                if sid not in sources:
                    errors.append(f"{where}: {cid} cites {sid}, missing from sources.yaml")
        if s.narration and not s.claims:
            warnings.append(f"{where}: narration without [CLAIM] — make sure it states no facts")
        if s.word_count > MAX_WORDS:
            warnings.append(f"{where}: {s.word_count} words (> {MAX_WORDS}); consider splitting")
        for cmd in s.commands:
            if cmd not in demo_text:
                warnings.append(f"{where}: [CMD] {cmd!r} not found in demo/commands.sh")

    for cid, c in claims.items():
        if c.status == "assumption" and cid not in cited:
            warnings.append(f"{cid}: unverified and unused — verify it or remove it")
    return errors, warnings


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    video_dir = Path(argv[1])
    try:
        errors, warnings = check(video_dir)
    except (ParseError, FileNotFoundError) as e:
        print(f"ERROR: {e}")
        return 1
    for w in warnings:
        print(f"warn:  {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
