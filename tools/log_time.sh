#!/usr/bin/env bash
# Append a production-log row: tools/log_time.sh <video_dir> <stage> <minutes> [cost_usd] [notes]
set -euo pipefail
dir="${1:?video dir}"; stage="${2:?stage}"; min="${3:?minutes}"
cost="${4:-0}"; notes="${5:-}"
[[ "$min" =~ ^[0-9]+$ ]] || { echo "minutes must be an integer" >&2; exit 2; }
root="$(cd "$(dirname "$0")/.." && pwd)"
printf '%s,%s,%s,%s,%s,"%s"\n' "$(date +%F)" "$(basename "$dir")" "$stage" "$min" "$cost" \
  "${notes//\"/\"\"}" >> "$root/production-log.csv"
echo "logged $min min for $(basename "$dir")/$stage"
