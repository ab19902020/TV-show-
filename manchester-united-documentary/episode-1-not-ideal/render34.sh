#!/usr/bin/env bash
# Render scenes 3-4 (Hull away) on their own: the frames from the "s3" mark to "end", in parallel chunks, muxed
# with that stretch of the episode mix (build/episode_audio.wav, from audio.py).
#   ./render34.sh [out.mp4]         EP_RES=3840x2160 (default)  JOBS=3  CHUNKS=16  CRF=18
# A 4K match frame needs about 2.7 GB: four of them at once overran this 15 GB container, so JOBS defaults to 3.
# Needs the build products of make_episode.sh: lines, timeline, parts, backgrounds, props.py's props and seated
# players, and audio.py's mix.
set -euo pipefail
cd "$(dirname "$0")"
OUT="${1:-episode1_scenes3-4_4k_master.mp4}"; J="${JOBS:-3}"; K="${CHUNKS:-16}"; CRF="${CRF:-18}"
read A B T0 DUR < <(python3 -c "
import json; M = json.load(open('build/timeline.json'))['marks']
a, b = round(M['s3'] * 30), round(M['end'] * 30); print(a, b, a / 30, (b - a) / 30)")
Q=$(( (B - A + K - 1) / K ))
rm -f build/p34_*.mp4
for k in $(seq 0 $((K - 1))); do
  a=$((A + k * Q)); b=$((A + (k + 1) * Q)); [ $b -gt $B ] && b=$B
  echo "$a $b build/p34_$k.mp4"
done | xargs -P "$J" -L 1 sh -c 'python3 render.py chunk $0 $1 $2 > $2.log 2>&1 || { echo "chunk $0-$1 failed"; tail -5 $2.log; exit 255; }'
for k in $(seq 0 $((K - 1))); do echo "file 'p34_$k.mp4'"; done > build/p34.txt
ffmpeg -y -loglevel error -ss "$T0" -t "$DUR" -i build/episode_audio.wav -af "afade=t=in:d=0.3" build/audio34.wav
ffmpeg -y -loglevel error -f concat -safe 0 -i build/p34.txt -i build/audio34.wav \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf "$CRF" -pix_fmt yuv420p -c:a aac -b:a 256k -shortest \
  -movflags +faststart "$OUT"
ffprobe -v error -show_entries stream=width,height,r_frame_rate:format=duration,size -of compact "$OUT"
