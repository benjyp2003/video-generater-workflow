# Command index for the production workflow. Every target has a manual
# equivalent documented in templates/video/CHECKLIST.md.
#
#   make new SLUG=docker-run FORMAT=concept TITLE="What happens when you run docker run?"
#   make check V=videos/2026-12-docker-run
#   make help

# Point PY at a venv for the audio tools, e.g. PY=.venv/bin/python
PY ?= python3
SHELL := /bin/bash
# FORCE=1 re-renders even when outputs are newer than sources.

.PHONY: help new check log test lint visuals diagrams slides terminal demo audio storyboard video draft subs

help: ## Show targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

require-v:
	@test -n "$(V)" -a -d "$(V)" || { echo "set V=videos/<id> (existing directory)"; exit 2; }

new: ## Create a video project: SLUG= FORMAT= [TITLE=]
	@tools/new_video.sh "$(SLUG)" "$(FORMAT)" "$(TITLE)"

check: require-v ## Gate-1 helper: claims, sources, commands
	$(PY) -m tools.check_claims $(V)

log: require-v ## Log time: STAGE= MIN= [COST=] [NOTES=]
	@tools/log_time.sh $(V) "$(STAGE)" "$(MIN)" "$(or $(COST),0)" "$(NOTES)"

test: ## Run tool tests
	$(PY) -m pytest -q tests

lint: ## Shellcheck scripts (if installed)
	@command -v shellcheck >/dev/null && shellcheck tools/*.sh templates/video/demo/*.sh || echo "shellcheck not installed; skipped"

diagrams: require-v ## Render diagrams/*.mmd -> media/visuals/*.png
	tools/render_diagrams.sh $(V) $(if $(FORCE),--force,)

slides: require-v ## Render slides/*.md (Marp) -> media/visuals/*.png
	tools/render_slides.sh $(V) $(if $(FORCE),--force,)

terminal: require-v ## Render demo/*.tape (VHS) -> media/visuals/*.mp4
	tools/render_terminal.sh $(V) $(if $(FORCE),--force,)

visuals: diagrams slides ## Diagrams + slides (terminal is separate: needs vhs)

demo: require-v ## Run demo/commands.sh in the disposable sandbox, log to demo/logs/
	$(V)/demo/run.sh

audio: require-v ## Narration per scene: [SCENES=s01,s02] [PROVIDER=placeholder] [FORCE=1]
	$(PY) -m tools.tts $(V) $(if $(SCENES),--scenes $(SCENES)) $(if $(PROVIDER),--provider $(PROVIDER)) $(if $(FORCE),--force)

storyboard: require-v ## Generate storyboard.yaml from script.md (+ overrides)
	$(PY) -m tools.storyboard $(V)

draft: require-v ## Animatic: media/build/draft.mp4 with placeholders for missing inputs
	$(PY) -m tools.assemble $(V) --draft $(if $(FORCE),--force)

video: require-v ## Final assembly -> media/build/final.mp4 (fails on missing inputs)
	$(PY) -m tools.assemble $(V) $(if $(FORCE),--force)

subs: require-v ## Captions -> final.srt  [MODE=whisper] [INPUT=file.mp4]
	$(PY) -m tools.subtitles $(V) $(if $(MODE),--mode $(MODE)) $(if $(INPUT),--input $(INPUT))
