#!/usr/bin/env bash
# Render the film (1080x1920, 30 fps) in 4 parallel chunks and mux the ORIGINAL audio, untouched in timing.
#   ./render_film.sh [out.mp4]
# The audio comes from the original clip (src/audio/original_clip_audio.opus, extracted from the uploaded video without re-timing);
# it is encoded once to AAC 320k for MP4 players. The picture's word timings were measured on the same audio (zero offset).
set -euo pipefail
cd "$(dirname "$0")"
OUT=${1:-micah_richards_50_caps.mp4}
N=$(python3 -c "import perf; print(int(round(perf.DUR * 30)))")
Q=$(( (N + 3) / 4 ))
mkdir -p build/render
for k in 0 1 2 3; do
  a=$((k * Q)); b=$(( (k + 1) * Q )); [ $b -gt $N ] && b=$N
  python3 render.py chunk $a $b build/render/part$k.mp4 > build/render/log$k.txt 2>&1 &
done
wait
printf "file 'part%d.mp4'\n" 0 1 2 3 > build/render/parts.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i build/render/parts.txt -i src/audio/original_clip_audio.opus \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -c:a aac -b:a 320k -ar 48000 \
  -movflags +faststart "$OUT"
echo "done -> $OUT"
