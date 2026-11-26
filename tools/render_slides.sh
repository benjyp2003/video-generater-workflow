#!/usr/bin/env bash
# slides/*.md (Marp) -> media/visuals/<name>.png (first slide), only when newer.
# Usage: tools/render_slides.sh videos/<id> [--force]
set -euo pipefail
dir="${1:?video dir}"; force="${2:-}"
root="$(cd "$(dirname "$0")/.." && pwd)"
marp="$root/node_modules/.bin/marp"
[[ -x "$marp" ]] || { echo "marp missing: run 'npm ci' in $root" >&2; exit 1; }
out="$dir/media/visuals"; mkdir -p "$out"
shopt -s nullglob
n=0
for src in "$dir"/slides/*.md; do
  name="$(basename "$src" .md)"; dst="$out/$name.png"
  if [[ "$force" != --force && -f "$dst" && "$dst" -nt "$src" ]]; then continue; fi
  "$marp" --quiet --theme "$root/channel/theme/marp.css" --image png \
    ${CHROME_PATH:+--browser-path "$CHROME_PATH"} --allow-local-files \
    -o "$dst" "$src"
  echo "rendered $dst"; n=$((n+1))
done
echo "slides: $n updated"
