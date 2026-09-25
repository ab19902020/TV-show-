#!/usr/bin/env bash
# Rebuild the Roy Keane "Overlap" rant scene from src/ (studio art, character sheet, two voice clips).
# Needs: ffmpeg, espeak-ng, python3 with requirements.txt installed.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p models
[ -f models/4x-AnimeSharp.pth ] || curl -sSL -o models/4x-AnimeSharp.pth \
  https://huggingface.co/Harvey6969/4x-AnimeSharp/resolve/main/4x-AnimeSharp.pth

# 1. 4x AI upscale of the set and the character sheet (so close-ups stay crisp)
[ -f src/studio_x4.png ] || python3 upscale.py src/studio.png src/studio_x4.png 4x-AnimeSharp
[ -f src/sheet_x4.png ]  || python3 upscale.py src/sheet.png  src/sheet_x4.png  4x-AnimeSharp

# 2. speech -> words (Whisper) -> phonemes with timings (wav2vec2 phoneme CTC forced alignment)
[ -f transcript.json ] || python3 transcribe.py
[ -f phones.json ]     || python3 align.py
python3 visemes.py                 # phonemes -> the sheet's 13 mouth shapes, per video frame

# 3. cut out + register the puppet parts, table occlusion mask
python3 build_assets.py
python3 tablemask.py

# 4. render (4 parallel chunks) and mux the voice track
python3 render.py audio
N=$(python3 -c "import json;print(json.load(open('timeline.json'))['n'])")
Q=$(( (N + 3) / 4 ))
for k in 0 1 2 3; do
  a=$((k * Q)); b=$(( (k + 1) * Q )); [ $b -gt $N ] && b=$N
  python3 render.py chunk $a $b part$k.mp4 &
done
wait
printf "file 'part%d.mp4'\n" 0 1 2 3 > parts.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i parts.txt -i scene_audio.wav \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart roy_keane_overlap_rant.mp4
echo "done -> roy_keane_overlap_rant.mp4"
