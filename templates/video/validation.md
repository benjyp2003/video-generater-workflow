# Validation — __TITLE__

## Gate 1: technical approval
- [ ] `make check V=videos/__ID__` passes (every [CLAIM] resolves to a verified claim)
- [ ] Every claim's source opened and read by me (not just the LLM)
- [ ] Versions recorded in video.yaml `tech_versions`
- [ ] Every [CMD] ran in the sandbox; log saved in demo/logs/
- [ ] Deprecated / changed behaviour checked
- [ ] Fact-check prompt run; every "no"/"partly" resolved

## Fact-check notes
| scene | issue | resolution |
|-------|-------|------------|
