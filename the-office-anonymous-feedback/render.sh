#!/usr/bin/env bash
# Render "Anonymous Feedback": sound mix, picture in parallel chunks, then the final MP4.
#   ./render.sh [out.mp4]            whole film (1920x1080, 25 fps)
#   ./render.sh clip T0 T1 out.mp4   a section with its sound, for checking
set -euo pipefail
cd "$(dirname "$0")"
J=${J:-4}
mkdir -p build/chunks
[ -f build/mix.wav ] && [ build/mix.wav -nt direction.py ] && [ build/mix.wav -nt sound.py ] || python3 sound.py
if [ "${1:-}" = "clip" ]; then
  T0=$2; T1=$3; OUT=$4
  A=$(python3 -c "print(int(round($T0*25)))"); B=$(python3 -c "print(int(round($T1*25)))")
else
  OUT=${1:-anonymous_feedback.mp4}
  A=0; B=$(python3 -c "import direction as D; print(int(round(D.TOTAL*D.FPS)))")
fi
for i in $(seq 0 $((J-1))); do
  a=$((A+(B-A)*i/J)); b=$((A+(B-A)*(i+1)/J))
  python3 render.py --chunk $a $b build/chunks/c$i.mp4 > build/chunks/c$i.log 2>&1 &
done
wait
: > build/chunks/list.txt
for i in $(seq 0 $((J-1))); do echo "file 'c$i.mp4'" >> build/chunks/list.txt; done
T0S=$(python3 -c "print($A/25)"); DUR=$(python3 -c "print(($B-$A)/25)")
# chunks are a near-lossless intermediate (CRF 17); the delivery is one even encode that stays under GitHub's 100 MB
ffmpeg -v error -y -f concat -safe 0 -i build/chunks/list.txt -ss "$T0S" -t "$DUR" -i build/mix.wav \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf ${CRF:-21} -pix_fmt yuv420p -g 50 \
  -c:a aac -b:a 256k -movflags +faststart "$OUT"
echo "wrote $OUT"
