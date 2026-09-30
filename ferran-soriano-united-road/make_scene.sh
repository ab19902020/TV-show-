#!/usr/bin/env bash
# Rebuild "Essentially, We Did It" (United Road Soriano parody) from src/: the three art sheets, the room
# backgrounds (src/rooms.png) and the five voice recordings.
# Needs ffmpeg and python3 with requirements.txt. Models come from GitHub releases only.
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -e models ]; then
  mkdir -p models
  R=https://github.com/xinntao/Real-ESRGAN/releases/download
  curl -sSL -o models/RealESRGAN_x4plus.pth $R/v0.1.0/RealESRGAN_x4plus.pth
  curl -sSL -o models/RealESRGAN_x4plus_anime_6B.pth $R/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth
  curl -sSL https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-turbo.tar.bz2 | tar xj -C models
fi

# 1. words: Whisper transcript (hand-corrected in transcript.json), pocketsphinx word + phone alignment,
#    the scene timeline (clips, beats, phrases, sighs), mouth shapes, caption cards / subtitle files, the sound
[ -f transcript.json ] || python3 transcribe.py
[ -f phones.json ] || python3 align.py
python3 timeline.py
python3 visemes.py
python3 captions.py
python3 audio.py

# 2. art: cut every drawing out using the sheets' own transparency and upscale it (gesture poses 8x), the rooms 4x
python3 parts.py
[ -f src/room_portrait_x4.png ] || python3 upscale.py src/room_portrait.png src/room_portrait_x4.png RealESRGAN_x4plus_anime_6B
[ -f src/room_landscape_x4.png ] || python3 upscale.py src/room_landscape.png src/room_landscape_x4.png RealESRGAN_x4plus_anime_6B
python3 set.py

# 3. rig: master head, mouths, eyes, registered head-less bodies, forearm pieces; then the paperwork
python3 head.py
python3 mouths.py
python3 alt_faces.py
python3 eyes.py
python3 bodies.py
python3 arms.py
python3 manifest.py
python3 cues.py
python3 preview.py

# 4. picture: portrait master first, then the separately framed landscape version
./render_all.sh portrait soriano_parody_portrait.mp4
./render_all.sh landscape soriano_parody_landscape.mp4
