#!/usr/bin/env bash
# A small 720p copy of a finished video to send in chat (~20 MB for 90 s).
#   tools/preview.sh <video.mp4> <preview.mp4>
set -euo pipefail
ffmpeg -y -v error -i "$1" -vf scale=1280:720 -c:v libx264 -preset medium -crf 25 -c:a aac -b:a 128k \
  -movflags +faststart "$2"
ls -la "$2"
