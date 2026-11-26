# Command index for the production workflow. Every target has a manual
# equivalent documented in templates/video/CHECKLIST.md.
#
#   make new SLUG=docker-run FORMAT=concept TITLE="What happens when you run docker run?"
#   make check V=videos/2026-12-docker-run
#   make help

PY ?= python3
SHELL := /bin/bash

.PHONY: help new check log test lint

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
