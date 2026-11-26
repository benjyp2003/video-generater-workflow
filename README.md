# video-generater-workflow

AI-assisted, human-verified production system for a faceless technical YouTube
channel (DevOps, cloud, Linux, beginner security).

- Design and decisions: [docs/architecture.md](docs/architecture.md)
- Git conventions: [docs/git-workflow.md](docs/git-workflow.md)
- Per-video checklist: [templates/video/CHECKLIST.md](templates/video/CHECKLIST.md)

## Setup

```bash
# Core tools (claim checks, storyboard, assembly, tests)
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# Diagram + slide renderers (pinned)
npm ci
# Local speech (Kokoro TTS + faster-whisper); Kokoro needs Python 3.10–3.12 and espeak-ng
.venv/bin/pip install -r requirements-audio.txt
# Secret scanning and checks on every commit
pip install pre-commit && pre-commit install
```

Also install: Docker, FFmpeg, OBS, Kdenlive. Optional: [VHS](https://github.com/charmbracelet/vhs).
If puppeteer can't find a browser, set `CHROME_PATH=/path/to/chrome`.
Use `make ... PY=.venv/bin/python` (or activate the venv).

## Making a video

```bash
make new SLUG=docker-run FORMAT=concept TITLE="What happens when you run docker run?"
V=videos/2026-11-docker-run          # created + branch video/docker-run

# research.md / sources.yaml / outline.md / script.md  ← prompts/*.md + your edits
make demo V=$V        # run demo/commands.sh in a throwaway sandbox, log to demo/logs/
make check V=$V       # Gate 1 helper: every [CLAIM] verified and sourced
make visuals V=$V     # diagrams/*.mmd + slides/*.md -> media/visuals/
make terminal V=$V    # demo/*.tape -> terminal recordings (needs vhs)
make audio V=$V       # narration per scene (kokoro | placeholder | human)
make draft V=$V       # animatic with placeholders for anything missing
make video V=$V       # media/build/final.mp4
make subs V=$V        # final.srt from the script (MODE=whisper for edited videos)
make preflight V=$V   # Gate 2/3 helper before a PRIVATE upload
make log V=$V STAGE=research MIN=90   # time tracking -> production-log.csv
```

Change one scene and rerun `make audio video subs`: only that scene's
narration and segment are regenerated.

`make help` lists every target. Each one has a manual equivalent in the checklist.

## Layout

| Path | What | In git |
|------|------|--------|
| `videos/<id>/` | one self-contained project per video | sources yes, `media/` no |
| `templates/` | new-video template, format structures | yes |
| `prompts/` | provider-agnostic LLM prompts | yes |
| `channel/` | style, brand, themes, pronunciations, glossary, metrics | yes |
| `tools/` | small Python/shell tools behind the Makefile | yes |
| `tests/` | pytest suite for the tools (`make test`) | yes |

## Status

Stage 0 + Stage 1 tooling (docs/architecture.md §I) is implemented. Video 1
(`videos/2026-11-docker-run`) is at *scripting*: research draft, script,
diagrams, slides and a sandbox-validated demo exist; **every claim still needs
human verification** before Gate 1.
