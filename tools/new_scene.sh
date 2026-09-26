#!/usr/bin/env bash
# Start a new scene folder from an existing scene's pipeline code (no build products, no video, no source art).
#   tools/new_scene.sh <new-scene-slug> [base scene dir, default jim-ratcliffe-ineos-office]
# Then put the character sheet(s), background and voice clips in <slug>/src/ (see .claude/skills/new-scene).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NEW="$ROOT/$1"; BASE="$ROOT/${2:-jim-ratcliffe-ineos-office}"
[ -e "$NEW" ] && { echo "$NEW already exists"; exit 1; }
mkdir -p "$NEW/src"
cd "$BASE"
git ls-files | grep -vE '^src/|\.mp4$|^(transcript|phones|timeline)\.json$|^README\.md$' | while read -r f; do
  mkdir -p "$NEW/$(dirname "$f")"; cp "$f" "$NEW/$f"
done
echo "created $NEW from $(basename "$BASE"):"; ls "$NEW"
