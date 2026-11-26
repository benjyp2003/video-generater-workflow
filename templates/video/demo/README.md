# Demo sandbox

- `commands.sh` — the exact commands shown on screen, in order.
- `run.sh` — runs `commands.sh` inside a disposable container and saves a timestamped
  log to `logs/`. Use `make demo V=videos/<id>`.
- `*.tape` — optional VHS scripts for reproducible terminal recordings.

Rules
- Never run demo commands on your host shell. Everything goes through the sandbox.
- No real credentials. Use obviously fake values (`EXAMPLE_TOKEN`).
- The prompt shown on screen is `user@demo:~$`.
- Cloud demos: dedicated account, budget alert, tags `video=<id>`, written teardown
  script, approval before provisioning (docs/architecture.md ADR-008).
