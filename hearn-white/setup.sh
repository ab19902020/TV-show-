#!/usr/bin/env bash
# Rebuild the editable project for The Undercard (Hearn v White): the studio engine at the exact commit this film was
# made with, the library overlay (the eight characters, the seven boxing sets, the props) copied over its library,
# one engine file (tools/index_library.py: the boxing sets folder), and the episode.
#   ./setup.sh [DIR]        (default: ./animnationstuido-)   then follow DIR/episodes/the-undercard/README.md
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DIR="${1:-animnationstuido-}"
ENGINE_COMMIT=1213ed0aa2c79bd2da19b4a2230171296a6a67a6

if [ ! -d "$DIR/.git" ]; then
  git clone https://github.com/ab19902020/AnimnationStuido-.git "$DIR"
fi
git -C "$DIR" checkout "$ENGINE_COMMIT"
cp -a "$HERE/library-overlay/." "$DIR/library/"
cp -a "$HERE/engine-overlay/." "$DIR/"
mkdir -p "$DIR/episodes/the-undercard"
cp -a "$HERE/episode/." "$DIR/episodes/the-undercard/"
echo "ready: $DIR/episodes/the-undercard (README.md there has the render steps)"
