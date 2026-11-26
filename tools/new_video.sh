#!/usr/bin/env bash
# Create a new video project from templates/video.
# Usage: tools/new_video.sh <slug> <format> ["Working title"]
set -euo pipefail
slug="${1:?usage: new_video.sh <slug> <format> [title]}"
format="${2:?format: concept|tutorial|comparison|architecture|short}"
title="${3:-$slug}"

case "$format" in concept|tutorial|comparison|architecture|short) ;;
  *) echo "unknown format: $format" >&2; exit 2 ;; esac
[[ "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "slug must be lowercase-kebab-case" >&2; exit 2; }

root="$(cd "$(dirname "$0")/.." && pwd)"
id="$(date +%Y-%m)-$slug"
dest="$root/videos/$id"
[[ -e "$dest" ]] && { echo "already exists: videos/$id" >&2; exit 1; }

mkdir -p "$root/videos"
cp -R "$root/templates/video" "$dest"
mkdir -p "$dest/media"/{audio,visuals,build,raw}

# Escape characters special to sed replacement.
esc() { printf '%s' "$1" | sed -e 's/[\/&|]/\\&/g'; }
find "$dest" -type f ! -path '*/media/*' -print0 | while IFS= read -r -d '' f; do
  sed -i.bak -e "s|__ID__|$(esc "$id")|g" -e "s|__FORMAT__|$format|g" \
             -e "s|__TITLE__|$(esc "$title")|g" -e "s|__DATE__|$(date +%F)|g" "$f"
  rm -f "$f.bak"
done

echo "created videos/$id"
if git -C "$root" rev-parse --git-dir >/dev/null 2>&1 && [[ "${NO_BRANCH:-0}" != 1 ]]; then
  git -C "$root" switch -c "video/$slug" && echo "switched to branch video/$slug"
fi
