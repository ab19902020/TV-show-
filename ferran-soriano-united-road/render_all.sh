#!/usr/bin/env bash
# Render one format in parallel chunks and mux it with the mix:
#   ./render_all.sh portrait|landscape [out.mp4]      JOBS=3 CHUNKS=12 CRF=18
# Needs the build products of make_scene.sh (timeline, visemes, rig, set plates, captions, soriano_audio.wav).
set -euo pipefail
cd "$(dirname "$0")"
O="$1"; OUT="${2:-soriano_parody_$O.mp4}"; J="${JOBS:-3}"; K="${CHUNKS:-12}"; CRF="${CRF:-18}"
N=$(python3 -c "import json; print(json.load(open('build/timeline.json'))['n'])")
Q=$(( (N + K - 1) / K ))
mkdir -p build/chunks
for k in $(seq 0 $((K - 1))); do
  a=$((k * Q)); b=$(( (k + 1) * Q )); [ $b -gt $N ] && b=$N
  [ -s "build/chunks/${O}_$k.mp4" ] && [ -f "build/chunks/${O}_$k.done" ] && continue
  echo "$a $b build/chunks/${O}_$k.mp4"
done | xargs -P "$J" -L 1 sh -c 'python3 render.py chunk '"$O"' $0 $1 $2 > $2.log 2>&1 && touch ${2%.mp4}.done || { echo "chunk $0-$1 failed"; tail -5 $2.log; exit 255; }'
for k in $(seq 0 $((K - 1))); do echo "file '${O}_$k.mp4'"; done > build/chunks/$O.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i build/chunks/$O.txt -i soriano_audio.wav \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf "$CRF" -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate:format=duration,size -of compact "$OUT"
