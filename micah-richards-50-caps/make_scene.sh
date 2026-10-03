#!/usr/bin/env bash
# Rebuild "Micah Richards: 50 Caps" from src/ (character sheets, Wing's backgrounds, the original audio).
# Needs ffmpeg and python3 with requirements.txt. Models come from GitHub releases only.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p models build
R=https://github.com/xinntao/Real-ESRGAN/releases/download
[ -f models/RealESRGAN_x4plus_anime_6B.pth ] || curl -sSL -o models/RealESRGAN_x4plus_anime_6B.pth $R/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth
[ -d models/sherpa-onnx-whisper-turbo ] || curl -sSL \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-turbo.tar.bz2 | tar xj -C models

# 1. words: Whisper for a first transcript, then the hand-corrected turns in align.py -> phones.json (word + phone timings)
[ -f transcript.json ] || python3 transcribe.py
[ -f phones.json ] || python3 align.py

# 2. art: cut every drawing out of the sheets (1x); upscale 4x (8x for the waist-up poses that are shown big); re-ink the
#    outlines; eyes; head boxes and anchors; the filming phone
python3 cut_parts.py cut
python3 cut_parts.py up
python3 cut_parts.py up8 wr_p_ m2_p_ as_p_ gy_p_talking1 gy_p_amused gy_p_pointing gy_p_talking2 cr_p_ b1_p_ b2_p_ b3_p_ b4_p_
python3 realpha.py
python3 eyes.py
python3 -c "import cast; cast.build_cache()"
python3 props.py

# 3. backgrounds: the studio (repo's red-and-black set, extended for portrait) and Wing's, 4x
python3 plates.py up

# 4. picture + the original audio
./render_film.sh micah_richards_50_caps.mp4
