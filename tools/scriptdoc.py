"""Parsers for the human-authored source files of a video project.

Contracts (docs/architecture.md §F):
  script.md   — YAML front matter, then `## sNN Title` scenes with optional
                [VISUAL] / [CLAIM] / [CMD] marker lines followed by narration.
  research.md — a Markdown table whose rows start with `| C<n> |`
                (id | claim | sources | status | notes).
  sources.yaml, video.yaml — plain YAML.

Pure functions, no side effects: everything else in tools/ builds on this.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SCENE_RE = re.compile(r"^##\s+(s\d+[a-z]?)\b\s*(.*)$")
MARKER_RE = re.compile(r"^\[(VISUAL|CLAIM|CMD)\]\s*(.*)$")
CLAIM_ID_RE = re.compile(r"\bC\d+\b")
SOURCE_ID_RE = re.compile(r"\bS\d+\b")
VALID_STATUSES = {"verified", "assumption", "rejected", "deprecated"}


@dataclass
class Visual:
    type: str
    name: str
    note: str = ""


@dataclass
class Scene:
    id: str
    title: str
    line: int
    visuals: list[Visual] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    narration: str = ""

    @property
    def word_count(self) -> int:
        return len(self.narration.split())


@dataclass
class Script:
    meta: dict
    scenes: list[Scene]

    def scene(self, scene_id: str) -> Scene:
        for s in self.scenes:
            if s.id == scene_id:
                return s
        raise KeyError(scene_id)


@dataclass
class Claim:
    id: str
    text: str
    sources: list[str]
    status: str
    notes: str = ""


class ParseError(ValueError):
    pass


def _split_front_matter(text: str) -> tuple[dict, list[str], int]:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                meta = yaml.safe_load("\n".join(lines[1:i])) or {}
                return meta, lines[i + 1 :], i + 1
        raise ParseError("front matter opened with '---' but never closed")
    return {}, lines, 0


def parse_visual(value: str) -> Visual:
    head, _, note = value.strip().partition(" ")
    vtype, sep, name = head.partition(":")
    if not sep or not vtype or not name:
        raise ParseError(f"[VISUAL] must look like 'type:name [note]', got {value!r}")
    return Visual(type=vtype, name=name, note=note.strip())


def parse_script(text: str) -> Script:
    meta, lines, offset = _split_front_matter(text)
    scenes: list[Scene] = []
    seen: set[str] = set()
    current: Scene | None = None
    paragraphs: list[str] = []

    def flush() -> None:
        if current is not None:
            current.narration = " ".join(" ".join(paragraphs).split())

    for idx, raw in enumerate(lines, start=offset + 1):
        line = raw.strip()
        m = SCENE_RE.match(line)
        if m:
            flush()
            sid = m.group(1)
            if sid in seen:
                raise ParseError(f"line {idx}: duplicate scene id {sid}")
            seen.add(sid)
            current = Scene(id=sid, title=m.group(2).strip(), line=idx)
            scenes.append(current)
            paragraphs = []
            continue
        if current is None or not line or line.startswith("<!--"):
            continue
        mk = MARKER_RE.match(line)
        if mk:
            kind, value = mk.groups()
            try:
                if kind == "VISUAL":
                    current.visuals.append(parse_visual(value))
                elif kind == "CLAIM":
                    current.claims.extend(CLAIM_ID_RE.findall(value))
                else:
                    current.commands.append(value.strip())
            except ParseError as e:
                raise ParseError(f"line {idx}: {e}") from None
            continue
        paragraphs.append(line)
    flush()
    return Script(meta=meta, scenes=scenes)


def parse_claims(text: str) -> dict[str, Claim]:
    claims: dict[str, Claim] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not re.match(r"^\|\s*C\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        cells += [""] * (5 - len(cells))
        cid, text_, sources, status, notes = cells[:5]
        status = status.replace("*", "").strip().lower()
        if cid in claims:
            raise ParseError(f"duplicate claim id {cid} in research.md")
        claims[cid] = Claim(cid, text_, SOURCE_ID_RE.findall(sources), status, notes)
    return claims


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_script(video_dir: Path) -> Script:
    return parse_script((video_dir / "script.md").read_text(encoding="utf-8"))


def load_claims(video_dir: Path) -> dict[str, Claim]:
    path = video_dir / "research.md"
    return parse_claims(path.read_text(encoding="utf-8")) if path.exists() else {}


def load_source_ids(video_dir: Path) -> set[str]:
    data = load_yaml(video_dir / "sources.yaml")
    return {s["id"] for s in (data.get("sources") or []) if "id" in s}
