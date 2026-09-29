#!/usr/bin/env bash
# Build Episode 1 ("Not Ideal"), scenes 1-4, from the character sheets, backgrounds and voice clips in this repo.
# Needs ffmpeg and python3 with requirements.txt. Models come from GitHub releases (Real-ESRGAN, Whisper turbo).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p models build
R=https://github.com/xinntao/Real-ESRGAN/releases/download
[ -f models/RealESRGAN_x4plus.pth ] || curl -sSL -o models/RealESRGAN_x4plus.pth $R/v0.1.0/RealESRGAN_x4plus.pth
[ -f models/RealESRGAN_x4plus_anime_6B.pth ] || curl -sSL -o models/RealESRGAN_x4plus_anime_6B.pth $R/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth
[ -d models/sherpa-onnx-whisper-turbo ] || curl -sSL \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-turbo.tar.bz2 | tar xj -C models

# 1. voice clips (the uploaded pack, stored in the repo as "show TV.zip")
[ -d audio_raw ] || (mkdir -p audio_raw && cd audio_raw && unzip -oq "../../show TV.zip")
[ -f chunks.json ] || python3 transcribe_chunks.py        # what is said in every clip, split at pauses
[ -f phones.json ] || python3 align_clips.py              # word + phone timings (pocketsphinx forced alignment)
python3 lines.py                                          # the scripted lines, cut word-exact -> build/lines
python3 timeline.py                                       # the dialogue edit (pauses / beats) -> build/timeline.json

# 2. art: cut every part out of the sheets and upscale 4x; upscale the backgrounds 4x
python3 parts.py
python3 bg_upscale.py
# scenes 3-4: the props (coach, gloves, tape, Maguire's white boots) and the seated players
python3 props.py

# 3. sound: room tone, foley, crowd, whistles, score, mix -> build/episode_audio.wav
python3 audio.py

# 4. picture: 4 parallel chunks, then mux with the mix
N=$(python3 -c "import perf; print(int(round(perf.TL['total'] * 30)))")
Q=$(( (N + 3) / 4 ))
for k in 0 1 2 3; do
  a=$((k * Q)); b=$(( (k + 1) * Q )); [ $b -gt $N ] && b=$N
  python3 render.py chunk $a $b build/part$k.mp4 > build/render$k.log 2>&1 &
done
wait
printf "file 'part%d.mp4'\n" 0 1 2 3 > build/parts.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i build/parts.txt -i build/episode_audio.wav \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -c:a aac -b:a 256k -shortest \
  -movflags +faststart episode1_scenes1-4.mp4
echo "done -> episode1_scenes1-4.mp4"
# scenes 3-4 on their own: ./render34.sh episode1_scenes3-4.mp4
