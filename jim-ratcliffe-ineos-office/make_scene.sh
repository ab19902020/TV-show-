#!/usr/bin/env bash
# Rebuild the Jim Ratcliffe "INEOS office" scene from src/ (office art, character sheet, mouth sheet, 4 voice clips).
# Needs: ffmpeg, python3 with requirements.txt installed.  Models come from GitHub releases only.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p models
R=https://github.com/xinntao/Real-ESRGAN/releases/download
[ -f models/RealESRGAN_x4plus.pth ] || curl -sSL -o models/RealESRGAN_x4plus.pth $R/v0.1.0/RealESRGAN_x4plus.pth
[ -f models/RealESRGAN_x4plus_anime_6B.pth ] || curl -sSL -o models/RealESRGAN_x4plus_anime_6B.pth $R/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth
[ -d models/sherpa-onnx-whisper-turbo ] || curl -sSL \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-turbo.tar.bz2 | tar xj -C models

# 1. 4x AI upscale: painterly character sheets with the general model (keeps stubble / skin texture),
#    the clean-line office with the anime model
[ -f src/office_x4.png ] || python3 upscale.py src/office.png src/office_x4.png RealESRGAN_x4plus_anime_6B
[ -f src/sheet_x4.png ]  || python3 upscale.py src/sheet.png  src/sheet_x4.png  RealESRGAN_x4plus
[ -f src/mouths_x4.png ] || python3 upscale.py src/mouths.png src/mouths_x4.png RealESRGAN_x4plus

# 2. speech -> words (Whisper turbo) -> phones with timings (pocketsphinx forced alignment) -> mouth shapes per frame
[ -f transcript.json ] || python3 transcribe.py
[ -f phones.json ]     || python3 align.py
python3 visemes.py

# 3. cut out every part, register them into the rig, lip-sync mouth library, office occlusion matte
#    (the profile rig, walkers and made-up drawings are built from these at render time)
python3 cut_parts.py
python3 register.py
python3 mouths.py
python3 occlusion.py

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
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a aac -b:a 256k -shortest \
  -movflags +faststart jim_ratcliffe_ineos_office.mp4       # CRF 22 keeps it under GitHub's 100 MB limit
echo "done -> jim_ratcliffe_ineos_office.mp4"
