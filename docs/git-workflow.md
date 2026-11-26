# Git workflow

Small enough for one person, strict enough that history explains itself.

## Branches
| Branch | Purpose | Lifetime |
|--------|---------|----------|
| `main` (trunk) | always-working tooling + published/approved videos | permanent |
| `feat/<topic>` | a tooling feature (one capability) | merge with `--no-ff`, then delete |
| `fix/<topic>` | a bug or theme fix found while producing | same |
| `docs/<topic>` | documentation only | same |
| `video/<slug>` | one video's sources, created by `make new` | merge when published (or as WIP when you need it elsewhere) |

- Tooling never changes on a `video/*` branch. Fix it on `fix/*` from trunk, merge
  to trunk, then `git merge <trunk>` into the video branch.
- `--no-ff` merges keep each feature visible as one unit: `git log --graph --first-parent`
  reads like a changelog.

## Commits
- One logical change per commit (e.g. research draft, script draft, visuals, demo fix).
- Subject in imperative mood, ≤ 72 chars; body says *why*, and what was verified.
- Video commits start with the video name: `Video 1: ...`.
- Never commit: `.env`, keys/tokens, `media/`, renders, raw recordings
  (`.gitignore` + gitleaks pre-commit enforce this).
- Commit demo logs (`demo/logs/*.log`): they are the evidence for Gate 1.

## Tags (recommended)
- `published/<video-id>` on the commit you published from, so a later correction
  can be diffed against what viewers saw.
