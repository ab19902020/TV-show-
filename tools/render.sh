#!/usr/bin/env bash
# Render a scene's video from its current assets (skips upscaling / cut-outs): 4 parallel chunks + the voice track.
#   tools/render.sh <scene dir> <output.mp4>
# CRF 22 keeps a ~90 s 1080p video under GitHub's 100 MB file limit.
set -euo pipefail
S="$(cd "$1" && pwd)"; OUT="$2"; J="${JOBS:-4}"
cd "$S"
python3 render.py audio
N=$(python3 -c "import json;print(json.load(open('timeline.json'))['n'])")
Q=$(( (N + J - 1) / J ))
for k in $(seq 0 $((J - 1))); do
  a=$((k * Q)); b=$(( (k + 1) * Q )); [ $b -gt $N ] && b=$N
  python3 render.py chunk $a $b part$k.mp4 > render_$k.log 2>&1 &
done
wait
for k in $(seq 0 $((J - 1))); do echo "file 'part$k.mp4'"; done > parts.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i parts.txt -i scene_audio.wav \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a aac -b:a 256k -shortest \
  -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size -of compact "$OUT"
