# Production checklist — 2026-11-docker-run

Log minutes per stage in `production-log.csv` as you go:
`make log V=videos/2026-11-docker-run STAGE=research MIN=90`

## 1. Plan
- [ ] Topic, format, audience and keywords in video.yaml
## 2. Research
- [ ] Run prompts/research.md; paste draft ledger into research.md
- [ ] Open every source; fill sources.yaml; mark claims verified/rejected
## 3. Outline & script
- [ ] prompts/outline.md → outline.md (edited)
- [ ] prompts/script.md → script.md (rewritten in my words)
## 4. Validate — GATE 1
- [ ] demo/commands.sh runs in sandbox: `make demo V=videos/2026-11-docker-run`
- [ ] `make check V=videos/2026-11-docker-run` passes
- [ ] validation.md fully ticked
- [ ] approvals.technical filled in video.yaml
## 5. Visuals
- [ ] diagrams/*.mmd → `make diagrams V=videos/2026-11-docker-run`
- [ ] Terminal recordings (OBS, or demo/*.tape → `make terminal V=...`)
- [ ] Slides / title card
## 6. Audio
- [ ] `make audio V=videos/2026-11-docker-run` (or record each scene as media/audio/sNN.wav)
- [ ] Listen to every scene; fix pronunciations in channel/pronunciations.yaml
## 7. Assemble
- [ ] Kdenlive, or `make video V=videos/2026-11-docker-run` for slideshow formats
- [ ] `make subs V=videos/2026-11-docker-run`; read final.srt for term errors
- [ ] thumbnail.png (1280×720)
- [ ] publish.yaml (prompts/metadata.md draft, edited by me)
## 8. Final QA — GATE 2
- [ ] Watched the whole video at 1× speed
- [ ] Every on-screen command matches demo/logs
- [ ] No secrets, real hostnames, usernames, IPs, account IDs, notifications on screen
- [ ] Audio clean and consistent; captions synced
- [ ] Every asset licence recorded in assets.yaml
- [ ] approvals.final_qa filled
## 9. Publish — GATE 3
- [ ] Uploaded as PRIVATE with captions + thumbnail
- [ ] Checked on a phone
- [ ] AI disclosure decided and set; recorded in video.yaml publish.ai_disclosure
- [ ] approvals.publish filled → schedule / public
- [ ] Raw recordings backed up (external disk + off-site)
## 10. Review
- [ ] +7 days: metrics.d7 · +28 days: metrics.d28 · row in channel/metrics.csv
- [ ] Retro: slowest stage? anything to automate? (docs/architecture.md §I)
