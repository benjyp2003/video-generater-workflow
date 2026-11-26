#!/usr/bin/env bash
# diagrams/*.mmd -> media/visuals/<name>.png (only when the source is newer).
# diagrams/*.png|*.svg (e.g. Excalidraw exports) are copied through unchanged.
# Usage: tools/render_diagrams.sh videos/<id> [--force]
set -euo pipefail
dir="${1:?video dir}"; force="${2:-}"
root="$(cd "$(dirname "$0")/.." && pwd)"
mmdc="$root/node_modules/.bin/mmdc"
[[ -x "$mmdc" ]] || { echo "mmdc missing: run 'npm ci' in $root" >&2; exit 1; }
# shellcheck source=tools/_chrome.sh
source "$root/tools/_chrome.sh"

out="$dir/media/visuals"; mkdir -p "$out"
shopt -s nullglob
n=0
for src in "$dir"/diagrams/*.mmd; do
  name="$(basename "$src" .mmd)"; dst="$out/$name.png"
  if [[ "$force" != --force && -f "$dst" && "$dst" -nt "$src" ]]; then continue; fi
  "$mmdc" -q -i "$src" -o "$dst.tmp.png" -c "$root/channel/theme/mermaid.json" \
    -b "#0F172A" --size 1800 -s 2 "${PUPPETEER_ARGS[@]}"
  mv "$dst.tmp.png" "$dst"; echo "rendered $dst"; n=$((n+1))
done
for src in "$dir"/diagrams/*.png "$dir"/diagrams/*.svg; do
  dst="$out/$(basename "$src")"
  [[ -f "$dst" && "$dst" -nt "$src" ]] || { cp "$src" "$dst"; echo "copied $dst"; n=$((n+1)); }
done
echo "diagrams: $n updated"
