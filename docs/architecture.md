# AI-Assisted Technical Video Production System — Architecture

> Status: Accepted v1, Stage 0 + Stage 1 implemented (see §P) · Date: 2026-11-26 · Owner: solo creator
> Scope: design only. Nothing here provisions infrastructure, buys services, or publishes content.

---

## A. Executive Summary

**Recommendation:** Run the channel from **one Git repository holding a folder per video**. Treat the content as data: Markdown and YAML files that a person writes and reviews are the source of truth. Every video, audio clip, and image can be regenerated from those files plus a small set of tools that run locally.

The system grows in four stages, and each step up has to be justified by measured pain:

| Stage | What it is | Orchestration | Monthly cost |
|---|---|---|---|
| **0 – Manual MVP** | Folder template + checklists + LLM in a chat UI + OBS + a desktop video editor | You, following `CHECKLIST.md` | $0 (optional ~$6–20) |
| **1 – Assisted** | ~6 small Python/shell scripts + a `Makefile` as the command index | `make <target>` | $0–30 |
| **2 – Modular pipeline** | One CLI (`studio`) with stage modules, file contracts, content-hash caching, and a status file | `studio run <video> --from <stage>` | $10–50 |
| **3 – Scalable** (optional) | The same modules, run by CI or a scheduler, with object storage and API publishing/analytics | GitHub Actions or a small workflow engine | $50–300 |

Core philosophy:

1. **Technical accuracy comes before automation.** Every factual claim gets a source, and every command runs in a sandbox before it appears on screen.
2. **Files are the interface.** Modules read and write files in the video's folder. No databases, queues, or services until volume proves a need.
3. **People approve; machines repeat.** AI drafts. A person approves the claims, the script, any paid resource, and every publish.
4. **Diagrams, terminal recordings, and simple slides do most of the visual work.** For a technical audience they explain more clearly than generative video, and they are cheaper and reproducible.
5. **Automate what the production log shows is expensive and repetitive.** Nothing else.

---

## B. Assumptions and Requirements

### B.1 Explicit requirements (from the brief)
- Solo, faceless, English, beginner-focused DevOps/cloud/security/Linux content.
- Five formats: concept, tutorial, comparison, architecture breakdown, short.
- Budget of $0–50/month initially, possibly $100–300/month later.
- Local-first. Open source preferred. Low vendor lock-in.
- Human approval before destructive commands, paid resources, publishing, or other irreversible external changes.
- Every claim is traceable to a source. Commands are validated. Versions are recorded.
- Stages can be rerun safely, and providers can be replaced with limited changes.
- Production metrics drive what gets automated.

### B.2 Assumptions (stated defaults; change them if wrong)
| # | Assumption | Effect if wrong |
|---|---|---|
| A1 | A mid-range laptop/desktop (8–16 GB RAM, **no dedicated GPU**), Linux/macOS/Windows+WSL2 | With a GPU, local TTS/STT is faster. Nothing else changes. |
| A2 | Docker Desktop or Docker Engine can be installed | Without Docker, use Multipass/VirtualBox VMs for demos (slower and heavier). |
| A3 | Narration **defaults to local TTS (Kokoro)**, with your own recorded voice as the main alternative | Recording your own voice adds about 1–2 h per video, needs a mic (~$50–100 one-time), and avoids AI-voice policy questions. |
| A4 | The free tier of a chat LLM (Claude.ai, ChatGPT, Gemini) is good enough for Stage 0. API keys come in Stage 1 or 2. | A paid chat subscription (~$20/mo, **verify**) improves context length and limits. |
| A5 | 5–10 hours a week of production time | This sets the cadence: about one long video every 1–2 weeks, plus shorts made from the same material. |
| A6 | You are comfortable with Git, a shell, basic Python, and YAML (you are studying DevOps) | — |
| A7 | 1080p 16:9 for long-form and 1080×1920 for shorts | — |

### B.3 Unresolved questions (they don't block Stage 0)
1. **Voice:** your own voice or synthetic? This is the biggest quality and retention lever and has policy implications. Default: try Kokoro on video 1, compare against a 60-second sample of your own voice, and decide by video 3.
2. **Editor familiarity:** have you used Kdenlive, DaVinci Resolve, or Shotcut? The default is Kdenlive. If you already know another editor, use it.
3. **Monetization goal:** is YPP monetization a near-term goal? If so, the "inauthentic / mass-produced content" policy shapes how much templating you can do (see N).
4. **OS:** Windows users should do all tooling inside WSL2 so the scripts stay POSIX.

---

## C. Minimal Viable Workflow (Stage 0)

The goal is **one published, technically correct, 6–10 minute concept video**, using only the free tools listed in O.2.

```
 1. Pick topic           -> topics.md (backlog)                          [you]
 2. Create project       -> copy templates/video -> videos/<id>/         [you]
 3. Research             -> research.md (sources + claims ledger)        [LLM drafts, you verify]
 4. Outline              -> outline.md                                   [LLM drafts, you edit]
 5. Script               -> script.md (narration + [VISUAL] cues)        [LLM drafts, you rewrite]
 6. Fact-check gate      -> every claim in script maps to a verified source  ✅ HUMAN GATE 1
 7. Demo                 -> demo/ (Dockerfile/commands) run in container  [you]
 8. Visuals              -> diagrams/*.mmd -> PNG/SVG; OBS terminal recordings
 9. Voice                -> audio/sNN.wav per scene (Kokoro or your mic)
10. Assemble             -> Kdenlive project; export final.mp4
11. Subtitles            -> Whisper on final audio -> final.srt; fix terms
12. Thumbnail + metadata -> thumbnail.png, publish.yaml                   [LLM drafts titles]
13. Final QA             -> CHECKLIST.md: watch full video at 1x          ✅ HUMAN GATE 2
14. Publish              -> upload manually as PRIVATE -> check -> schedule/public  ✅ HUMAN GATE 3
15. Log                  -> production-log.csv (minutes per stage, cost)
16. Review at +7 / +28 days -> analytics notes in video.yaml
```

Stage 0 deliberately skips: APIs, scripts, a standalone storyboard file (the `[VISUAL]` cues in `script.md` serve as the storyboard), separate keyword tooling, and automated uploads.

---

## D. Architecture

### D.1 High-level architecture

```
                         ┌──────────────────────────────────────────┐
                         │        Git repository  ("studio")        │
                         │  templates/  tools/  channel/  docs/     │
                         │  videos/<id>/  (source files only)       │
                         └──────────────┬───────────────────────────┘
                                        │ reads/writes files
  ┌─────────────────────────────────────▼──────────────────────────────────────┐
  │                           PRODUCTION MODULES                               │
  │                                                                            │
  │  PLAN ──► RESEARCH ──► SCRIPT ──► VALIDATE ──► VISUALS ─┐                  │
  │  topic     sources,     outline,   claims +     diagrams,│                  │
  │  backlog   claims       script     commands     demos,   ├─► RENDER ─► QA ─► PUBLISH ─► ANALYTICS
  │                                    (sandbox)    slides   │   (assemble,           │          │
  │                                                 AUDIO ───┘   subtitles,           │          │
  │                                                 (TTS/mic)    thumbnail)           │          │
  │                                                                                   ▼          │
  │                                         ◄──────── feedback: topics, format, automation ◄────┘
  └────────────────────────────────────────────────────────────────────────────┘
          │                    │                    │                   │
     LLM provider        Docker sandbox        TTS / STT          YouTube Studio
   (chat UI → API)      (local container)   (local models)     (manual → API, Stage 3)

  Outside Git: media/ (raw recordings, renders) → external disk / synced folder
  Outside Git: .env (API keys) → local only, never committed
```

### D.2 Module boundaries

These are logical modules, not services. In Stage 0 each one is a checklist section. In Stage 1 most become a script. In Stage 2 each becomes a Python module behind a single CLI.

| Module | Owns | Writes to |
|---|---|---|
| **plan** | Topic backlog, format choice, target audience/keyword | `topics.md`, `video.yaml` |
| **research** | Sources, versions, claims ledger | `research.md`, `sources.yaml` |
| **script** | Outline, narration, visual cues | `outline.md`, `script.md` |
| **validate** | Claim-to-source coverage, command execution in sandbox | `validation.md`, `demo/logs/` |
| **visuals** | Diagrams, slides, terminal/screen recordings | `diagrams/`, `media/visuals/` |
| **audio** | Narration per scene | `media/audio/` |
| **render** | Assembly, subtitles, thumbnail | `media/build/`, `final.srt`, `thumbnail.*` |
| **qa** | Checklist, final review record | `video.yaml: approvals` |
| **publish** | Metadata, upload | `publish.yaml`, `video.yaml: publish` |
| **analytics** | Post-publish metrics, retrospectives | `video.yaml: metrics`, `channel/metrics.csv` |

### D.3 Data flow

```
topics.md ─► video.yaml (format, version pins, status)
                │
sources.yaml ◄──┤
research.md ────┴─► outline.md ─► script.md ──┬─► [Stage 1+] storyboard.yaml (generated)
   (claims C1..Cn)                (cites C#)  │
                                              ├─► narration text per scene ─► media/audio/sNN.wav
                                              ├─► [VISUAL] cues ─► diagrams/*.mmd ─► media/visuals/*.png
                                              └─► demo commands ─► demo/ ─► sandbox run ─► demo/logs/
                                                                                     │
                           all of the above ─► assemble ─► media/build/final.mp4 ─► STT ─► final.srt
                                                                   │
                                     publish.yaml + thumbnail ─► YouTube (manual)
```

### D.4 Control flow and approval gates

```
 [plan] → [research] → [script] ─► GATE 1: Technical approval
                                    (all claims verified, versions recorded,
                                     commands passed in sandbox)
                                    │ fail → back to research/script
                                    ▼
          [visuals] ∥ [audio]  (independent; can run in either order)
                                    ▼
                               [render]
                                    ▼
                                 GATE 2: Final QA (full watch-through, checklist)
                                    │ fail → rerun only the affected stage
                                    ▼
                                 GATE 3: Publish approval (upload private → review → public)

 Additional ad-hoc gates (always human):
   • any cloud resource with cost  → approve + set budget alert + cleanup plan first
   • any destructive command outside a disposable container
   • any LLM-proposed command → runs only inside the sandbox
```

### D.5 External dependencies

| Dependency | Stage introduced | Replaceable by |
|---|---|---|
| LLM (chat UI, then API) | 0 | Any LLM. Prompts are plain Markdown files. |
| Docker | 0 | VM (Multipass/Vagrant), cloud sandbox |
| Kokoro TTS (local) | 0 | Piper, ElevenLabs, your own mic |
| Whisper / faster-whisper (local) | 0 | Any STT, or the editor's auto-captions |
| Mermaid CLI | 0 | D2, Graphviz, Excalidraw |
| OBS Studio | 0 | VHS (scripted terminal), the OS screen recorder |
| Kdenlive | 0 (dropped by Stage 2 for most formats) | DaVinci Resolve, Shotcut, FFmpeg scripts |
| FFmpeg | 1 | MoviePy (wraps FFmpeg), Remotion |
| YouTube Studio / Data API | 0 / 3 | Manual upload, other platforms' APIs |

---

## E. Repository Structure

### E.1 Stage 0 (create today)

```
studio/
├── README.md                    # how to start a video (5 lines)
├── .gitignore                   # media/, .env, *.mp4, *.wav, *.mov ...
├── topics.md                    # backlog: idea | format | audience | priority
├── channel/
│   ├── style.md                 # voice/tone rules, glossary, banned phrases
│   ├── brand.md                 # colours, fonts, thumbnail rules
│   └── metrics.csv              # one row per published video
├── prompts/                     # reusable LLM prompts (provider-agnostic text)
│   ├── research.md
│   ├── outline.md
│   ├── script.md
│   ├── fact-check.md
│   └── metadata.md
├── templates/
│   └── video/                   # copied for every new video
│       ├── video.yaml
│       ├── research.md
│       ├── sources.yaml
│       ├── outline.md
│       ├── script.md
│       ├── CHECKLIST.md
│       ├── publish.yaml
│       ├── diagrams/.gitkeep
│       └── demo/README.md
├── videos/
│   └── 2026-12-docker-run/      # <yyyy-mm>-<slug>; self-contained
│       ├── video.yaml
│       ├── research.md
│       ├── sources.yaml
│       ├── outline.md
│       ├── script.md
│       ├── validation.md
│       ├── diagrams/*.mmd
│       ├── demo/{Dockerfile,commands.sh,logs/}
│       ├── publish.yaml
│       ├── final.srt
│       ├── thumbnail.png        # small; OK in git
│       └── media/               # GITIGNORED: recordings, audio, renders
├── production-log.csv           # video_id, stage, minutes, cost_usd, notes
└── docs/
    └── architecture.md          # this document
```

### E.2 Stage 1 (add when the transition criteria are met)

```
+ Makefile                       # make new, diagrams, audio, subs, video, check
+ tools/
+   new_video.sh                 # copy template, fill id/date
+   render_diagrams.sh           # mmdc over diagrams/*.mmd
+   tts.py                       # script.md → media/audio/sNN.wav (Kokoro)
+   subtitles.py                 # final audio → final.srt (faster-whisper)
+   assemble.py                  # storyboard → ffmpeg concat (slideshow formats)
+   check_claims.py              # every [C#] in script exists & is verified
+ templates/video/demo.tape      # VHS scripted terminal recording
+ channel/assets/                # intro sting, lower-third, fonts (licensed)
+ .env.example                   # names of keys, never values
+ requirements.txt  (or pyproject.toml with uv)
```

### E.3 Stage 2

```
- tools/*.py   → moved into a package
+ studio/                        # python package, single CLI entrypoint
+   cli.py                       # studio new|run|status|clean
+   manifest.py                  # load/validate video.yaml (schema_version)
+   stages/{research,script,validate,visuals,audio,render,publish,analytics}.py
+   providers/{llm,tts,stt}/     # adapters ONLY for categories with ≥2 real providers
+   cache.py                     # content-hash stamps
+ schemas/*.json                 # JSON Schema for each contract
+ tests/                         # contract tests + golden-file tests
+ .github/workflows/check.yml    # lint, schema validation, claim coverage on PR
+ videos/<id>/.state.json        # gitignored: per-stage hashes, timestamps, status
```

### E.4 Stage 3 (only if needed)
- Split `studio` (tooling) and `content` (videos) into **two repos**. Content pins a tooling version.
- Media goes to object storage (S3/R2/B2) under `s3://bucket/<video_id>/<sha>/...`. `video.yaml` references URIs.
- Workflows run on GitHub Actions/self-hosted runners or Prefect. Infrastructure is defined with Terraform (a good learning project at that point, not before).

### E.5 What goes in Git

| Category | Examples | Git? | Where instead |
|---|---|---|---|
| Human-authored sources | `script.md`, `research.md`, `*.mmd`, `video.yaml`, prompts, `demo/` | ✅ Yes | — |
| AI-generated intermediates **after human edit** | outline, script drafts you accepted | ✅ Yes (they become sources) | — |
| Raw AI output you didn't accept | discarded drafts | ❌ No | delete, or keep in `media/scratch/` |
| Reproducible generated files | diagram PNGs, TTS wavs, renders, storyboard.yaml (Stage 1+) | ❌ No | regenerate. `media/` is gitignored. |
| Small finals worth versioning | `final.srt`, `thumbnail.png` (<1 MB), `publish.yaml` | ✅ Yes | — |
| Large binaries | screen recordings, final.mp4 | ❌ No | external disk + one off-site copy (e.g. a synced cloud folder) |
| Secrets | API keys, OAuth tokens, `client_secret.json` | ❌ **Never** | `.env` (local), OS keychain, later a secrets manager |

Git LFS is rejected for now (ADR-004). Raw recordings aren't reproducible, so they need a **backup**, not version control.

---

## F. Data Contracts

All contracts carry `schema_version`. Rules for evolving them: **add optional fields freely. Never rename or remove a field without bumping the major version and adding a tiny migration in `manifest.py` (Stage 2).** Readers ignore unknown fields.

### F.1 `video.yaml` — project manifest

```yaml
schema_version: 1
id: 2026-12-docker-run
title_working: "What happens when you run docker run?"
format: concept            # concept | tutorial | comparison | architecture | short
status: scripting          # idea|research|scripting|approved|production|qa|published
audience: "beginners who have installed Docker but don't know how it works"
target_length_min: 8
keywords: [docker run, docker architecture, containerd, runc]

tech_versions:             # recorded at research time, shown in description
  docker_engine: "29.x"    # VERIFY at research time; example only
  containerd: "2.x"
  os: "Ubuntu 24.04 (container)"

providers:                 # config, not code: change here to switch
  llm: claude-chat         # free text in Stage 0; adapter key in Stage 2
  tts: kokoro              # kokoro | piper | elevenlabs | human
  tts_voice: af_heart
  stt: faster-whisper-small

approvals:                 # human gates; name + date, never auto-filled
  technical: null          # {by: me, at: 2026-12-03, notes: "..."}
  final_qa: null
  publish: null

publish:
  youtube_id: null
  published_at: null
  ai_disclosure: reviewed  # see N: policy reviewed for this video

metrics:                   # filled at +7d and +28d
  production_minutes: null
  cost_usd: null
  corrections_after_publish: 0
  d7:  {views: null, ctr: null, avg_view_pct: null}
  d28: {views: null, ctr: null, avg_view_pct: null, subs_gained: null}
```

### F.2 Research output — `sources.yaml` + claims ledger in `research.md`

```yaml
# sources.yaml
schema_version: 1
sources:
  - id: S1
    title: "Docker Engine overview"
    url: https://docs.docker.com/engine/
    type: official_docs        # official_docs | spec | source_code | blog | video
    accessed: 2026-12-01
    version: "Docker Engine 29"    # example; record what the page states
  - id: S2
    title: "containerd architecture"
    url: https://github.com/containerd/containerd/blob/main/docs/historical/design/architecture.md
    type: source_code
    accessed: 2026-12-01
```

```markdown
<!-- research.md (excerpt) -->
## Claims ledger
| id | claim | sources | status | notes |
|----|-------|---------|--------|-------|
| C1 | The docker CLI talks to dockerd over a REST API (unix socket by default on Linux) | S1 | verified | |
| C2 | dockerd delegates container lifecycle to containerd | S1,S2 | verified | |
| C3 | runc creates namespaces and cgroups, then exec's the process | S3 | verified | |
| C4 | "Docker is a lightweight VM" | — | **rejected** | misconception; address explicitly |
| C5 | Default bridge network is docker0 | S4 | assumption | verify in demo output |
```
Status values: `verified` (checked against a primary source by you), `assumption` (must be verified or cut before Gate 1), `rejected`, `deprecated`.

### F.3 Script — `script.md`

Markdown with stable scene IDs. The narration is the prose. `[VISUAL]` and `[CLAIM]` are machine-parsable markers:

```markdown
---
schema_version: 1
video: 2026-12-docker-run
---
## s01 Hook
[VISUAL] slide:title "docker run hello-world" + terminal flash
You type one command. In about a second, a whole isolated Linux process is running.
What actually happened?

## s02 The client and the daemon
[VISUAL] diagram:cli-daemon
[CLAIM] C1
The `docker` command you type is just a client. It sends an API request to a
background service called the Docker daemon...

## s05 Live demo
[VISUAL] terminal:demo/run-hello.tape
[CMD] docker run --rm hello-world
```
Rules: one `##` per scene. Scene IDs never get renumbered. Insert `s02a` instead, which keeps per-scene caching stable. Each scene has at most about 120 words of narration.

### F.4 Storyboard — `storyboard.yaml` (Stage 1+, generated from script.md, editable overrides)

```yaml
schema_version: 1
resolution: 1920x1080
scenes:
  - id: s02
    narration: media/audio/s02.wav       # duration taken from audio
    visual:
      type: diagram                      # diagram | slide | terminal | screen | image
      src: media/visuals/cli-daemon.png
      motion: ken_burns_slow             # none | ken_burns_slow | reveal_steps
    captions: true
    pad_after_s: 0.4
```

### F.5 Asset references — `assets.yaml` (provenance and licensing)

```yaml
schema_version: 1
assets:
  - path: media/visuals/cli-daemon.png
    kind: diagram
    generated_from: diagrams/cli-daemon.mmd
    tool: mermaid-cli@11          # record version actually used
    input_sha256: 3f9a...         # Stage 2: written automatically
    license: own
  - path: channel/assets/music/bed-01.mp3
    kind: music
    source_url: https://...       # where it came from
    license: "CC BY 4.0"          # must permit commercial use
    attribution: "Artist — Title" # copied into description if required
```

### F.6 Publishing metadata — `publish.yaml`

```yaml
schema_version: 1
platform: youtube
title: "What Actually Happens When You Run docker run? (Beginner Friendly)"
title_alternatives: ["...", "..."]       # for later A/B testing
description: |
  You type `docker run`. Here's every step between your keyboard and a running container.

  00:00 The command
  00:40 Client and daemon
  ...
  Versions shown: Docker Engine 29.x on Ubuntu 24.04.
  Sources:
  - Docker Engine overview: https://docs.docker.com/engine/
tags: [docker, containers, devops, beginner]
category: Education
language: en
visibility: private                      # ALWAYS private at upload; flipped by a human
made_for_kids: false
altered_or_synthetic: false              # decided per video against YouTube policy (see N)
thumbnail: thumbnail.png
captions: final.srt
playlist: "Docker from Zero"
```

---

## G. Tool Stack

### G.1 Decision table — major tools

| Need | **Recommended** | Why | Simpler alternative | OSS alternative | Cost | Limitations | Docs |
|---|---|---|---|---|---|---|---|
| LLM (research/outline/script drafts) | **Any chat LLM, free tier → API later** (e.g. Claude) | Best leverage per dollar; prompts kept as files so provider is swappable | — | Local LLM via Ollama (needs RAM/GPU; weaker on accuracy) | $0 free tier; API Sonnet-class ≈ $3/$15 per MTok in/out (**verified on official page Nov 2026; confirm current**); Haiku-class ≈ $1/$5 | Hallucinations → claims ledger is mandatory; free tiers have limits | https://platform.claude.com/docs/en/about-claude/pricing |
| Sandbox for demos | **Docker** (+ `kind` for K8s topics) | Disposable, reproducible, matches content domain | Plain VM | Podman | $0 | Docker Desktop licensing applies to larger companies (**verify** if relevant); some topics (kernel, networking) need a VM | https://docs.docker.com/ · https://kind.sigs.k8s.io/ |
| Diagrams | **Mermaid CLI (`mmdc`)** | Text-based → diffable, LLM-friendly, renders headless | Excalidraw (manual, hand-drawn look) | D2, Graphviz | $0 (MIT) | Layout control is limited; use Excalidraw for hero diagrams | https://github.com/mermaid-js/mermaid-cli |
| Terminal recording | **OBS** (Stage 0) → **VHS** (Stage 1) | OBS records anything; VHS turns a `.tape` text file into a deterministic, re-renderable terminal video | OS screen recorder | asciinema + agg | $0 (GPL / MIT) | VHS can't record GUIs/browsers | https://obsproject.com/kb · https://github.com/charmbracelet/vhs |
| Narration | **Kokoro-82M (local)** | Apache-2.0 weights, commercial use allowed, runs on CPU, per-scene regeneration is free | Your own voice + Audacity | Piper (GPL-3.0 code; per-voice dataset licences) | $0 | Less expressive than premium TTS; espeak-ng dependency is GPL-3.0 (fine for using, matters only if you redistribute) | https://huggingface.co/hexgrad/Kokoro-82M |
| Narration (upgrade) | **ElevenLabs Starter** | Higher quality; commercial licence starts at Starter | — | — | **$6/mo, 30k credits** (official pricing page, Nov 2026; verify) | Free tier has no commercial rights; vendor lock-in for cloned voices | https://elevenlabs.io/pricing |
| Subtitles | **faster-whisper** (local) | Accurate, CPU-capable, outputs timestamps; you already have the script for term correction | YouTube auto-captions | openai-whisper | $0 (MIT, **verify**) | Technical terms (e.g. "containerd", "runc") need a glossary pass | https://github.com/SYSTRAN/faster-whisper |
| Video editing (Stage 0) | **Kdenlive** | Free, OSS, cross-platform, adequate for diagrams + terminal + voice | Shotcut | — | $0 (GPL) | Manual; not reproducible | https://docs.kdenlive.org/ |
| Video assembly (Stage 1+) | **FFmpeg** (driven by Python) | Ubiquitous, scriptable, every format | MoviePy | — | $0 (LGPL/GPL builds) | Complex filters get cryptic → keep to concat/overlay/subtitle burn | https://ffmpeg.org/documentation.html |
| Slides/title cards | **Marp CLI** (Markdown → PNG) | Templated, themeable via CSS, text-in-git | Excalidraw/Inkscape | reveal.js | $0 (MIT) | Static; animation comes from editor/ffmpeg | https://github.com/marp-team/marp-cli |
| Thumbnail | **Inkscape or Canva free** (Stage 0) → HTML/Marp template (Stage 2) | Fast to start | Canva | Inkscape, GIMP | $0 | Canva = vendor lock-in for templates | https://inkscape.org/learn/ |
| Animated explanations (Stage 3, optional) | **Remotion** or **Manim** | Code-driven animation | — | Manim (MIT) | Remotion free for individuals/≤3-person teams (**verified Nov 2026**) | Learning curve; Remotion needs Node/React | https://www.remotion.dev/docs/license · https://docs.manim.community/ |
| Secret scanning | **gitleaks** pre-commit hook | Stops the most likely real-world incident (a committed key) | `.gitignore` alone | — | $0 | Regex-based | https://github.com/gitleaks/gitleaks |
| Upload / analytics (Stage 3) | **YouTube Data API v3 + Analytics API** | Only official option | Manual Studio | — | $0. Default 10,000 units/day. `videos.insert` cost is documented inconsistently (1 unit in its own upload bucket, max 100/day, on current page vs 1,600 units on older pages) → **check your project's Quotas page** | Unverified API projects may have uploads forced private until audit (**verify**) | https://developers.google.com/youtube/v3/docs/videos/insert · https://developers.google.com/youtube/v3/determine_quota_cost |

### G.2 Stacks

**Minimal (Stage 0) — install only these:** Git, Docker, a chat LLM, OBS, Kdenlive, Python 3.11+ with `kokoro` and `faster-whisper`, Mermaid CLI (needs Node), Audacity (only if recording your own voice), Inkscape/Canva.

**Intermediate (Stage 1–2):** + FFmpeg, VHS, Marp CLI, Make, `uv` (Python env), gitleaks + pre-commit, the LLM API (one provider), optionally ElevenLabs.

**Advanced (Stage 3, optional):** + GitHub Actions, object storage (Cloudflare R2/Backblaze B2/S3), YouTube Data/Analytics APIs, Remotion or Manim, Terraform for the cloud bits, a scheduler (cron → GitHub Actions schedule → Prefect if needed).

---

## H. Workflow Execution

### H.1 Create a new video project
- **Stage 0:** `cp -r templates/video videos/2026-12-docker-run`, then edit `video.yaml`.
- **Stage 1:** `make new SLUG=docker-run FORMAT=concept` copies the template, fills in id/date/format, and creates a git branch `video/docker-run`.
- **Stage 2:** `studio new docker-run --format concept`.

One branch per video keeps work in progress isolated. Merge to `main` when the video is published, which records its final state.

### H.2 Execute stages
- **Stage 0:** Follow `CHECKLIST.md` top to bottom and tick boxes. LLM work happens in the chat UI using `prompts/*.md`. Paste the outputs into the files and edit them.
- **Stage 1:** Make targets carry the dependencies:
  ```make
  V ?= $(error set V=videos/<id>)
  diagrams: ; tools/render_diagrams.sh $(V)
  audio:    ; python tools/tts.py $(V)            # only scenes whose text changed
  subs:     ; python tools/subtitles.py $(V)
  video:    audio diagrams ; python tools/assemble.py $(V)
  check:    ; python tools/check_claims.py $(V)   # Gate-1 helper, not a replacement
  ```
- **Stage 2:** `studio run <id>` runs every stage whose inputs have changed. `studio run <id> --only audio --scenes s03,s04`.

### H.3 Store artifacts
- Sources go in git in the video folder. Generated files go to `videos/<id>/media/` (gitignored), mirrored to backup storage.
- Every generated file has a deterministic path, such as `media/audio/<scene>.wav` or `media/visuals/<diagram>.png`. Reruns overwrite in place, so they are **idempotent**.
- Stage 2 adds `.state.json` with `{stage: {input_sha256, output_paths, finished_at, status}}`.

### H.4 Rerun failed stages
- Each stage reads only files and writes only its own outputs, so rerunning a stage is always safe.
- Write to `*.tmp` and then rename atomically. A crash never leaves a half-written file looking valid.
- **Per-scene granularity:** changing scene s03's narration regenerates only `s03.wav` and re-assembles. Assembly takes minutes, not hours.
- Stage 2 caching: skip a stage if `sha256(inputs + stage config + tool version)` matches the stamp. `--force` overrides it.

### H.5 Replace a component
| Change | What to touch |
|---|---|
| Different LLM | Nothing in code at Stage 0–1 (prompts are text). At Stage 2, one adapter file plus `providers.llm` in config. |
| Kokoro → ElevenLabs | Stage 1: one `if` branch in `tts.py`. Stage 2: a `providers/tts/elevenlabs.py` adapter (justified now that you have two real providers). |
| Mermaid → D2 | Add `render_d2.sh`. Diagram files declare their type by extension. Nothing downstream changes, because the contract is "a PNG at `media/visuals/<name>.png`". |
| Kdenlive → FFmpeg assembly | Both consume the same `media/` files. Switch per video format. |
| YouTube → another platform | Add a `publish/<platform>` step that reads `publish.yaml`. Platform-specific fields go under a `platform_overrides:` key. |

**Adapter rule:** add a provider interface only when **two providers are actually in use**, or a switch is planned within the next month. Until then, the provider name in config plus one isolated function is enough.

### H.6 Produce the final video
Visuals and audio are ready → assemble (Kdenlive in Stage 0, `assemble.py` in Stage 1+) → `media/build/final.mp4` → STT → `final.srt` → corrections against the glossary → Gate 2 watch-through → upload **private** with srt and thumbnail → review on a phone → Gate 3 → schedule or make public.

---

## I. Automation Roadmap

### I.1 What to automate first (expected ranking; confirm with your `production-log.csv`)

| Rank | Task | Frequency | Time saved/video (est.) | Effort | Quality risk | Verdict |
|---|---|---|---|---|---|---|
| 1 | Per-scene TTS from `script.md` | every video, many reruns | 30–60 min | 2–3 h | low | **Stage 1, first** |
| 2 | Diagram rendering (`mmdc` batch) | every video | 15–30 min | 30 min | none | Stage 1 |
| 3 | Subtitle generation + glossary fix | every video | 20–40 min | 1–2 h | low | Stage 1 |
| 4 | Project init from template | every video | 5–10 min | 30 min | none | Stage 1 (cheap) |
| 5 | Claim-coverage check | every video | 15 min + fewer misses | 1–2 h | **reduces** risk | Stage 1 |
| 6 | Scripted terminal demos (VHS) | tutorials | 30–90 min per re-record | 2 h learning | low | Stage 1 |
| 7 | Slideshow assembly via FFmpeg | concept/short | 1–2 h | 4–8 h | medium (pacing) | Stage 1 end / Stage 2 |
| 8 | Metadata drafts (title/desc/chapters) via API | every video | 15 min | 1 h | low (human edits) | Stage 2 |
| 9 | Short cut-downs from long-form | per long video | 1 h | 4 h | medium | Stage 2 |
| 10 | Upload via API (private) | per video | 10 min | 4–6 h + OAuth/audit | **high** (accidental publish) | Stage 3 |
| 11 | Analytics pull | weekly | 15 min | 3–4 h | none | Stage 3 |
| ✗ | Topic selection, fact-checking, final QA, publish decision | — | — | — | — | **Never fully automated** |

Priority score = `(minutes saved × videos/month) ÷ (build hours + monthly maintenance hours)`, penalised for quality risk. Re-rank after every 3 videos.

### I.2 Transition criteria

| Transition | Move when **all** of these hold | Don't move if |
|---|---|---|
| **0 → 1** | ≥ 2 videos published · the same manual step is logged ≥ 2 times at ≥ 20 min each · format and voice decided | You haven't finished video 1 |
| **1 → 2** | ≥ 8–10 videos published · ≥ 3 formats or ≥ 4 videos/month · ≥ 1 incident/month of rerunning the wrong stage, stale artifacts, or forgotten steps · `tools/` > ~800 lines or scripts duplicate logic | Scripts still fit in your head |
| **2 → 3** | ≥ 2 videos in production at once regularly · local render/TTS time > ~3 h/week **or** the machine is blocking other work · budget ≥ $100/mo approved · a second channel/platform is planned or analytics review costs > 1 h/week | It's "for learning only". Do that in a separate lab, not in the production path. |

---

## J. Cost Analysis

### J.1 Verified prices (checked 2026-11-26 via official pages where noted. Re-check before purchase.)
| Item | Price | Source |
|---|---|---|
| Claude API, Sonnet-class | $3 in / $15 out per MTok (Batch API −50%) | platform.claude.com pricing page |
| Claude API, Haiku-class | $1 in / $5 out per MTok | platform.claude.com pricing page (third-party listing; confirm) |
| ElevenLabs Starter | $6/mo, 30k credits, commercial licence | elevenlabs.io/pricing |
| ElevenLabs Creator | $22/mo (credit amount varies by source, ~100k–121k) | elevenlabs.io/pricing — **verify** |
| Remotion | Free for individuals / ≤3-person teams | remotion.dev/docs/license |
| YouTube Data API | Free, 10,000 units/day default | developers.google.com |
| Kokoro, Whisper, FFmpeg, OBS, Kdenlive, Mermaid, Marp, VHS | $0 (open source) | project repos |

### J.2 Estimates (not verified prices)
| Item | Estimate | Basis |
|---|---|---|
| Initial setup cost | $0 software. Optional USB mic $50–100, one-time. | |
| LLM API per long video (Stage 2) | ~$0.50–2 | ~150–300k input + 30–60k output tokens across research/outline/script/metadata at Sonnet-class rates |
| TTS per video (Kokoro) | $0 + ~5–15 min CPU | 8 min of narration |
| TTS per video (ElevenLabs) | 8 min ≈ ~8–10k characters ≈ fits Starter for ~3 videos/month | credits ≈ characters for standard models (**verify**) |
| Cloud demo per tutorial | $0–2 if run < 2 h on small instances and destroyed | requires budget alerts (H/N) |
| Storage backup | $0–5/mo (external disk or ~100–500 GB object storage) | |
| **Monthly, Stage 0** | **$0** (maybe $20 if you choose a chat subscription) | |
| **Monthly, Stage 1–2** | **$10–40** | API + optional ElevenLabs + storage |
| **Monthly, Stage 3** | **$50–150** | + CI minutes, storage, more API |

### J.3 Human time (estimates; measure and replace)
| Format | Video 1 | Stage 1 target | Stage 2 target |
|---|---|---|---|
| Concept (8 min) | 15–25 h | 8–12 h | 5–8 h |
| Tutorial (12 min) | 20–30 h | 12–16 h | 8–12 h |
| Comparison | 12–20 h | 8–10 h | 5–7 h |
| Architecture breakdown | 20–30 h | 12–15 h | 8–10 h |
| Short (60 s) | 4–6 h standalone; 1–2 h if cut from long-form | 1–2 h | 0.5–1 h |

Research and verification stay roughly constant (about 3–6 h per long video). That time is the quality floor, and automation should not shrink it.

---

## K. Implementation Roadmap

Each milestone ends with something usable.

### Day 1 — "repo + first draft" (≈ 4–6 h)
1. Create the repo with the E.1 structure, `.gitignore`, `templates/video/*`, `prompts/*`, `channel/style.md`.
2. Install Docker, OBS, Kdenlive, Node+`mmdc`, Python with `kokoro` + `faster-whisper`. Run each once on a "hello" input.
3. Create `videos/2026-12-docker-run`. Draft `research.md` and the source list from official docs.
4. **Usable result:** a tool-checked environment and a research ledger for video 1.

### Week 1 — "first video published" (≈ 15–25 h)
- Days 2–3: outline, then script. Fact-check (Gate 1). Run the demo in a container and save the logs.
- Day 4: diagrams, OBS terminal recordings, Kokoro narration per scene. Compare against your own voice for 60 s.
- Day 5: Kdenlive assembly, subtitles, thumbnail, metadata.
- Day 6: Gate 2 watch-through. Upload private, then Gate 3, then publish.
- **Usable result:** one public video plus a filled `production-log.csv`.

### Month 1 — "repeatable process + Stage 1 basics" (3–4 videos)
- Videos 2–3 in two formats (e.g. a short from video 1's material, plus a comparison).
- After video 2: `tools/tts.py`, `render_diagrams.sh`, `subtitles.py`, `new_video.sh`, `Makefile`, gitleaks pre-commit.
- After video 3: `check_claims.py` and VHS `.tape` demos.
- First retro: which stage took longest? Update the I.1 ranking.
- **Usable result:** `make audio diagrams subs` works on any video folder.

### Months 2–3 — "templated formats"
- Generate the storyboard from script.md. FFmpeg slideshow assembly for concept and short formats (Kdenlive stays for tutorials).
- Marp themes for title and comparison cards. Thumbnail template.
- An LLM API for metadata drafts (key in `.env`).
- **Usable result:** a concept video's assembly from approved script to draft MP4 is a single command.

### Months 3–6 — "Stage 2, only if criteria met"
- Consolidate into the `studio` CLI. JSON Schemas for contracts. Content-hash caching. Contract tests. A CI check on PRs (schema + claim coverage).
- **Usable result:** `studio status` shows every video's stage, and `studio run --from audio` rebuilds deterministically.

### Months 6+ — "Stage 3 pieces, à la carte"
- Pick whichever criterion triggered: analytics pull (lowest risk) → object storage → private upload via API → scheduled runs → Terraform for any cloud resources.

---

## L. Example Walkthrough — "What happens when you run `docker run`?"

**Format:** concept (8 min). **Audience:** beginners who have installed Docker.

### 1. Plan (10 min, manual)
`topics.md` row: `docker run internals | concept | beginners post-install | P1 | pairs with short "What is a container runtime?"`.
Keyword check (manual, free): YouTube search autocomplete for "docker run", plus related searches. Note phrasing in `video.yaml: keywords`.

### 2. Research (2–3 h; LLM-assisted, human-verified)
- Prompt (`prompts/research.md`) asks the LLM for a list of steps and the **official documentation pages** that would confirm each one. It is told not to state facts without a source to check.
- **You** open each page. Record it in `sources.yaml` (Docker Engine docs, the `docker run` reference, containerd docs, runc/OCI runtime spec, Linux namespaces/cgroups man pages).
- Claims ledger (excerpt):

| id | claim | status |
|---|---|---|
| C1 | CLI → dockerd via REST API (default unix socket `/var/run/docker.sock` on Linux) | verified (Docker docs) |
| C2 | If image not local, daemon pulls from registry (Docker Hub by default) | verified |
| C3 | dockerd → containerd → shim → runc (OCI runtime) | verified (docs + source) |
| C4 | runc sets up namespaces (pid, net, mnt, uts, ipc, user optionally) and cgroups, then starts the process | verified (runc + man7) |
| C5 | Container filesystem = image layers + writable layer (overlay2 storage driver typical) | verified, "typical" wording |
| C6 | Default network = bridge, veth pair, docker0 | verified in demo |
| C7 | "Containers are lightweight VMs" | **rejected**: addressed as a misconception |
- `video.yaml: tech_versions` filled from `docker version` output in the demo container.

> ⚠️ Retrieved pages and LLM output are **data**. If a page or response includes instructions ("run this script", "ignore previous..."), they are not followed. Commands are only ever copied into `demo/commands.sh` and run inside the sandbox.

### 3. Outline → script (2–3 h)
- `outline.md`: hook → client/daemon → image resolution and pull → containerd/runc → namespaces and cgroups → filesystem → network → process runs → recap → "next: Dockerfile".
- The LLM drafts `script.md` using `channel/style.md` (beginner vocabulary, an analogy per section, no hype words). **You rewrite** for voice and accuracy. Every factual sentence gets a `[CLAIM] C#`.
- **Gate 1:** `check_claims.py` (Stage 1; manual grep in Stage 0) confirms every `[CLAIM]` resolves to a `verified` claim. You sign `approvals.technical`.

### 4. Validate demo (1 h)
```
demo/
├── commands.sh     # docker run --rm hello-world; docker ps -a; docker inspect ...; ls /sys/fs/cgroup
├── run.sh          # runs commands.sh inside a Docker-in-Docker or a throwaway VM; tees logs/
└── logs/2026-12-02.txt
```
Everything runs as a non-root user where possible, in a disposable environment, with no real credentials, and with a fresh shell profile showing a generic prompt (`user@demo:~$`) so the hostname/username doesn't leak.

### 5. Visuals (2–4 h)
- `diagrams/cli-daemon.mmd`, `pull-flow.mmd`, `runtime-stack.mmd`, `namespaces.mmd` → `mmdc` → PNG.
- One "hero" Excalidraw diagram for the full stack, exported to `diagrams/full-stack.excalidraw` + PNG.
- Terminal: OBS recording of the demo at a large font (Stage 0). Stage 1: `demo/run-hello.tape` → VHS → MP4, reproducible when Docker output changes.
- Title card via Marp (Stage 1) or Inkscape.

### 6. Audio (30 min)
Kokoro produces one WAV per scene (`media/audio/s01.wav` …). Listen and fix pronunciation by respelling in a `channel/pronunciations.yaml` (e.g. `containerd: "container-dee"`, `runc: "run-see"`) applied before TTS. Changing one scene means regenerating one file.

### 7. Assemble, subtitles, thumbnail (3–5 h in Stage 0)
- Kdenlive: one track for visuals, one for narration, one optional music bed (licence logged in `assets.yaml`). Export `media/build/final.mp4`.
- `faster-whisper` → `final.srt`. Glossary pass to fix "container D" → "containerd".
- Thumbnail: dark background, a large `docker run` in monospace, a short label of 3 words max ("What Happens?"), brand colours from `channel/brand.md`.
- `publish.yaml`: LLM proposes 5 titles + a description with chapters. You pick one and edit. Sources and versions go in the description.

### 8. QA → publish → measure
- **Gate 2** checklist: watched at 1×; every command on screen matches the logs; no secrets/hostnames visible; audio levels around −14 LUFS (**verify** YouTube loudness target); captions synced; versions stated; the misconception is handled correctly.
- **Gate 3:** upload private → check on a phone → set the AI-disclosure field per policy review → schedule.
- `production-log.csv` rows per stage. At +7d and +28d, fill in `metrics` from YouTube Studio.

**What becomes automated later for this same video:** steps 6 and 7 (subtitles, assembly of diagram scenes), diagram rendering, the VHS terminal, metadata drafting, the claim check. **What never does:** choosing claims, accepting sources, approving, publishing.

---

## M. Architectural Decision Records

### ADR-001 — File-based content-as-data instead of a database/CMS
- **Problem:** Video state and artifacts need a home that is traceable and easy to change.
- **Decision:** One folder per video. Markdown + YAML as sources. Git for history.
- **Alternatives:** Notion/Airtable; SQLite; a headless CMS.
- **Reasoning:** Diffable, works offline, LLM-friendly, zero ops, teaches Git workflows.
- **Trade-offs:** No cross-video queries beyond grep/scripts. Concurrent editing is weak (irrelevant for one person).
- **Reconsider when:** > ~100 videos with frequent cross-video queries, or collaborators who don't use Git.

### ADR-002 — Single repo, logical modules, no services
- **Problem:** Need modularity without operational overhead.
- **Decision:** Modules are folders, scripts, or Python modules talking through files. One process.
- **Alternatives:** Microservices; n8n workflows; queues.
- **Reasoning:** All work is batch and done by one person. Network boundaries add failure modes with no benefit.
- **Trade-offs:** No parallel execution across machines.
- **Reconsider when:** The Stage 2→3 criteria hold (parallel videos, remote execution).

### ADR-003 — Make as the Stage 1 orchestrator (not n8n/Prefect/Airflow)
- **Problem:** Running steps in the right order and skipping unchanged ones.
- **Decision:** A Makefile as the command index and simple dependency runner. Stage 2 moves to a Python CLI with content hashes.
- **Alternatives:** n8n (visual, needs a server), Prefect/Airflow (Python, needs a scheduler/DB/UI), Dagger, just `bash`.
- **Reasoning:** Zero install, self-documenting targets, and core DevOps literacy.
- **Trade-offs:** Timestamp-based. Awkward with per-scene fan-out and on Windows (use WSL).
- **Reconsider when:** Scheduled/remote runs, retries with backoff, or a UI for run history are needed (Stage 3 → Prefect or GitHub Actions).

### ADR-004 — Large binaries outside Git; no Git LFS initially
- **Problem:** Recordings and renders are GBs.
- **Decision:** `media/` is gitignored. Raw recordings are backed up to an external disk plus one off-site copy. Generated files are reproducible.
- **Alternatives:** Git LFS; DVC; object storage from day 1.
- **Reasoning:** LFS has quota costs and adds friction for files that are either reproducible or don't need history.
- **Trade-offs:** Backup is a manual discipline in Stage 0.
- **Reconsider when:** Multiple machines need the same media, or the backup step is skipped twice → object storage + `rclone` sync (Stage 2/3).

### ADR-005 — Visual strategy: diagrams + terminal + slides; no generative video
- **Problem:** Faceless technical video needs clear, cheap, accurate visuals.
- **Decision:** Mermaid/Excalidraw diagrams, OBS → VHS terminal capture, Marp cards, FFmpeg motion (pan/zoom/reveal).
- **Alternatives:** AI video generators; stock footage; Manim/Remotion from the start.
- **Reasoning:** Generative video is expensive, inaccurate for technical detail, and raises policy and authenticity risks. Diagrams are the content.
- **Trade-offs:** Less "cinematic". Pacing must come from the editing.
- **Reconsider when:** Retention data shows drop-offs at static segments that edit-level motion doesn't fix → introduce Manim/Remotion for specific animations.

### ADR-006 — Local TTS default, provider as config, adapter only at two providers
- **Problem:** Voice quality vs cost vs lock-in.
- **Decision:** Kokoro locally. `providers.tts` in `video.yaml`. Isolate provider calls in one function. Build an adapter interface only when a second provider is actually used.
- **Alternatives:** ElevenLabs from day 1; own voice; abstract provider framework up front.
- **Reasoning:** $0, unlimited regeneration, commercial-use licence on the weights.
- **Trade-offs:** Lower expressiveness; possible "AI voice" perception by viewers.
- **Reconsider when:** Retention or comments flag the voice, or average view percentage trails comparable videos → test ElevenLabs Starter or your own voice.

### ADR-007 — Human gates are mandatory and recorded in the manifest
- **Problem:** Misinformation, accidental publishing, leaked secrets.
- **Decision:** Three gates (technical, QA, publish) recorded in `video.yaml: approvals`. Any automation refuses to proceed without them. Uploads are always private.
- **Alternatives:** Trust automated checks.
- **Reasoning:** Technical credibility is the channel's main asset, and you can't take back a published mistake.
- **Trade-offs:** About 1–2 h of review per video that won't go away.
- **Reconsider when:** Never removed. Checks may make the gates faster.

### ADR-008 — Sandboxed demos, cloud only with guardrails
- **Problem:** Tutorials need real environments, and cloud costs money and can leak secrets.
- **Decision:** Docker (or kind) first, then a local VM, and the cloud only when the topic is the cloud service itself. Cloud demos need: a dedicated account/project, budget alerts, resources tagged `video=<id>`, a written teardown script run on camera or right after, and least-privilege throwaway credentials that never appear on screen.
- **Reconsider when:** Never relaxed. Terraform-managed demo stacks (`apply` → record → `destroy`) are a Stage 2+ improvement.

---

## N. Risks and Limitations

| Area | Risk | Likelihood | Mitigation |
|---|---|---|---|
| Educational | LLM-introduced factual errors or outdated info | High | Claims ledger, primary sources, versions in description, Gate 1, pinned comment for corrections, `corrections_after_publish` metric |
| Educational | Commands that are deprecated or dangerous for beginners | Medium | Sandbox execution logs; deprecation check on official docs; warn on screen about destructive commands |
| Platform | **YouTube altered/synthetic content disclosure:** applies to realistic altered/synthetic content. A synthetic voice that imitates a real person is an example. | Medium | Never clone anyone else's voice. Review [the policy](https://support.google.com/youtube/answer/14328491) per video and disclose when in doubt. YouTube states disclosure doesn't affect monetization eligibility. |
| Platform | **YPP "inauthentic" (formerly "repetitious") content policy** targets mass-produced templated content. Details are reported by third parties, so **verify** on [YouTube's channel monetization policies](https://support.google.com/youtube/answer/1311392). | Medium (if monetizing) | Original explanations, real demos, human-written scripts, varied structure. Templates are for production, not for content. |
| Platform | API upload restrictions for unverified projects; quota | Low (Stage 3 only) | Manual upload until volume justifies it; compliance audit if needed |
| Legal | Music/images without commercial licence; trademark logos | Medium | `assets.yaml` with licence per asset; use own diagrams; official logo usage guidelines only |
| Security | API keys committed or shown on screen | Medium | `.env` + gitignore + gitleaks pre-commit; demo shell with clean env; QA checklist item to scan frames |
| Security | Prompt injection via retrieved pages → harmful command copied into demo | Low–Med | Retrieved content is data; commands only run in disposable sandbox; human reads every command |
| Financial | Forgotten cloud resources | Medium | Budget alerts, tags, teardown script, next-day check of the billing page |
| Operational | Data loss of raw recordings/projects | Medium | Git for sources (pushed to remote); 3-2-1-ish backup for `media/raw` |
| Operational | Burnout / over-engineering the pipeline instead of publishing | **High** | Stage criteria; a rule: no tooling work in a week with no video progress |
| Technical | Local TTS/STT slow on CPU | Low–Med | Per-scene caching; small Whisper models; run overnight |
| Technical | Tool licence changes (e.g. Remotion v5, Piper GPL move) | Low | Record tool versions; prefer permissive licences; isolate per ADR-006 |

**Unresolved limitations of this design:**
- The time estimates are educated guesses until `production-log.csv` has data.
- Kokoro's voice quality hasn't been tested against your audience. ADR-006 sets up the test.
- Prices and policies were checked on 2026-11-26 from search results. Pages marked **verify** need a direct check before you rely on them.
- Stage 0 assembly in Kdenlive isn't reproducible. This is accepted until the format stabilizes.

---

## O. Final Recommendation

### O.1 Build first
The **repository skeleton plus templates, prompts, and checklist**, then **video 1 manually**. No scripts until video 2.

### O.2 Install
Git · Docker · OBS Studio · Kdenlive · Node.js + `@mermaid-js/mermaid-cli` · Python 3.11+ with `kokoro` and `faster-whisper` · Inkscape (or Canva free) · Audacity (only for your own voice). Use a free chat LLM account.

### O.3 Create these files
`README.md`, `.gitignore`, `topics.md`, `production-log.csv`, `channel/{style.md,brand.md,metrics.csv}`, `prompts/{research,outline,script,fact-check,metadata}.md`, `templates/video/{video.yaml,research.md,sources.yaml,outline.md,script.md,publish.yaml,CHECKLIST.md}`.

### O.4 Do manually
Topic choice, source verification, script rewriting, demo execution, assembly (Stage 0), QA, upload, publish decision, analytics review.

### O.5 Automate first (after video 2)
1. Per-scene TTS. 2. Diagram rendering. 3. Subtitles + glossary. 4. Project init. 5. Claim-coverage check. 6. Secret-scanning pre-commit.

### O.6 Don't build yet
Databases, n8n/Prefect/Airflow, Kubernetes for the pipeline, Terraform for the pipeline, microservices, provider-abstraction layers, automated uploads/publishing, cloud rendering, analytics dashboards, generative video, multi-channel support.

### O.7 How to know the system needs to evolve
Review `production-log.csv` every 3 videos:
- A stage is consistently > 20% of total time **and** repetitive → automate it (I.1 scoring).
- You reran the wrong thing, forgot a step, or got stale artifacts twice in a month → Stage 2 caching/state.
- The machine is the bottleneck, or videos overlap → Stage 3 pieces.
- Corrections after publishing > 0 on two videos → strengthen Gate 1 **before** any further automation.

### Acceptance-criteria check
| Criterion | Met by |
|---|---|
| Solo-operable | Stage 0 = checklist + 6 tools |
| Initial version produces a complete video | C, K (week 1) |
| Inexpensive setup | $0 required |
| No unnecessary infrastructure | ADR-002/003/004, O.6 |
| Manual execution remains possible | Every automated step has a documented manual equivalent; Make/CLI are wrappers |
| Modules evolve independently | File contracts (F), D.2 |
| Providers replaceable | Config key + isolated function → adapter at 2 providers (H.5, ADR-006) |
| Content verifiable before publish | Claims ledger, sandbox, Gate 1 |
| Artifacts traceable to inputs | `sources.yaml`, `[CLAIM]` refs, `assets.yaml`, Stage 2 hashes |
| Failed stages safely repeatable | Idempotent deterministic paths, atomic writes, per-scene granularity |
| New formats incremental | `format` field + template variants; shared modules |
| Automation grows without rewrite | Stage 0 files = Stage 2 contracts; scripts become modules |
| Understandable | One repo, plain files, ~8 ADRs |

**Known gap:** reproducibility of the *final assembly* is only reached for slideshow-style formats in Stage 1–2. Tutorials with hand-edited screen recordings stay partly manual by design.

---

### Sources consulted (2026-11-26)
- Claude API pricing: https://platform.claude.com/docs/en/about-claude/pricing
- ElevenLabs pricing: https://elevenlabs.io/pricing
- Kokoro-82M model card (Apache-2.0): https://huggingface.co/hexgrad/Kokoro-82M
- Remotion license: https://www.remotion.dev/docs/license
- YouTube Data API quota: https://developers.google.com/youtube/v3/determine_quota_cost · https://developers.google.com/youtube/v3/docs/videos/insert
- YouTube altered/synthetic disclosure: https://support.google.com/youtube/answer/14328491
- Piper licensing (secondary source, not verified against Piper's repo): https://www.assemblyai.com/blog/free-open-source-text-to-speech

---

## P. Implementation Notes (2026-11-26)

Implemented: the E.1 Stage 0 layout, the Stage 1 tools (E.2), and the safety
checks from N, all behind the Makefile. Stage 2 and 3 items are **not** built.

| Capability | Implementation | Verified here |
|------------|----------------|---------------|
| Project init | `tools/new_video.sh` (`make new`) | ✅ tests + video 1 |
| Claim coverage (Gate 1 helper) | `tools/check_claims.py` | ✅ tests; blocks video 1 as expected |
| Diagrams / slides | Mermaid CLI 12.2.0, Marp CLI 4.5.1 (pinned in package-lock) | ✅ video 1 rendered |
| Terminal recordings | VHS tapes (`make terminal`) | ⚠️ VHS not installed here; untested |
| Narration | `tools/tts.py`: kokoro / placeholder / human, per-scene fingerprints | ✅ placeholder; ⚠️ Kokoro install OK, synthesis untested (model host blocked in this environment) |
| Storyboard + assembly | `tools/storyboard.py`, `tools/assemble.py` (FFmpeg) | ✅ tests + 5-min animatic of video 1 |
| Subtitles | `tools/subtitles.py`: script-aligned (default) or faster-whisper | ✅ script mode; ⚠️ whisper untested (same reason) |
| Sandbox demos | `demo/run.sh` in docker:dind, `SANDBOX_CA_FILE` for TLS proxies | ✅ video 1 demo ran; caught a real command bug |
| Preflight (Gates 2/3) | `tools/preflight.py` | ✅ tests |
| Secrets / large files | pre-commit: gitleaks v8.29.1, pre-commit-hooks v5.0.0 | ✅ all hooks pass |

Design changes made during implementation:
- **Storyboard is generated, overrides are authored.** `storyboard.yaml` is
  gitignored; hand edits live in `storyboard.overrides.yaml`. This keeps script.md
  as the single source of truth (refines F.4).
- **Subtitles default to the script, not STT.** For TTS videos the exact text and
  scene timing are already known, so no model is needed and jargon is always
  spelled right. Whisper stays for human narration and hand-edited videos.
- **A `placeholder` TTS provider** produces timed silence. It lets you review
  pacing and assembly (`make draft`) before choosing a voice.
- **Segment fingerprints include the renderer's code.** Changing the assembler
  re-renders cached segments. A stale-cache bug found during testing prompted this.
- Mermaid CLI 12 replaced `-w/-H` with `--size`. Kokoro 0.9 requires Python ≤ 3.12.

Findings from video 1 that feed back into content:
- The sandbox's Engine 29.10.1 uses the **containerd image store** (`overlayfs`),
  not `overlay2`. The script says "an overlay filesystem" (claim C5).
- The default bridge subnet differs per machine (172.18.0.0/16 here). Never state a
  fixed range.
