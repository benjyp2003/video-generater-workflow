#!/usr/bin/env bash
# demo/*.tape (VHS) -> media/visuals/<name>.mp4, only when newer.
# VHS executes the commands in the tape: keep tapes to sandbox-safe commands
# (e.g. run them inside `docker run` or the demo container).
# Usage: tools/render_terminal.sh videos/<id> [--force]
set -euo pipefail
dir="${1:?video dir}"; force="${2:-}"
command -v vhs >/dev/null || { echo "vhs not installed: https://github.com/charmbracelet/vhs" >&2; exit 1; }
out="$(cd "$dir" && pwd)/media/visuals"; mkdir -p "$out"
shopt -s nullglob
n=0
for src in "$dir"/demo/*.tape; do
  name="$(basename "$src" .tape)"; dst="$out/$name.mp4"
  if [[ "$force" != --force && -f "$dst" && "$dst" -nt "$src" ]]; then continue; fi
  (cd "$(dirname "$src")" && vhs -q -o "$dst" "$(basename "$src")")
  echo "rendered $dst"; n=$((n+1))
done
echo "terminal: $n updated"
