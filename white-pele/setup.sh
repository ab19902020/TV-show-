#!/usr/bin/env bash
# Rebuild the editable White Pelé project: the studio engine at the exact commit this film was made with, the
# library overlay (new and changed characters, drawings, backgrounds) copied over its library, and the episode.
#   ./setup.sh [DIR]        (default: ./animnationstuido-)   then follow DIR/episodes/white-pele/README.md
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DIR="${1:-animnationstuido-}"
ENGINE_COMMIT=9b9412663640847ff4adf3ca3381414e016eef38

if [ ! -d "$HERE/episode" ]; then
  echo "unpacking the production ZIP"
  cat "$HERE"/zip/White_Pele_production.zip.part* > "$HERE/White_Pele_production.zip"
  (cd "$HERE" && unzip -q -o White_Pele_production.zip)
fi
if [ ! -d "$DIR/.git" ]; then
  git clone https://github.com/ab19902020/AnimnationStuido-.git "$DIR"
fi
git -C "$DIR" fetch origin ccr-703a2362-lbr343 || true
git -C "$DIR" checkout "$ENGINE_COMMIT"
cp -a "$HERE/library-overlay/." "$DIR/library/"
mkdir -p "$DIR/episodes/white-pele"
cp -a "$HERE/episode/." "$DIR/episodes/white-pele/"
echo "ready: $DIR/episodes/white-pele (README.md there has the render and resume steps)"
