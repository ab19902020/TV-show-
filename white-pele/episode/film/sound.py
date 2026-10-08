"""The soundtrack: the supplied song, untouched and complete. Nothing is added (no narration, no crowd, no effects)
and nothing is mixed or levelled: the decoded samples go straight into the film.

    python3 -m studio.film white-pele sound -> build/episode_audio.wav (48 kHz stereo, 24-bit PCM)"""
import subprocess

from studio.film import ep


def main():
    out = ep.path("episode_audio.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(ep.DIR / "song.mp3"), "-map", "0:a:0",
                    "-c:a", "pcm_s24le", "-ar", "48000", str(out)], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(out)], capture_output=True, text=True, check=True).stdout)
    print(f"{out}  {dur:.3f} s (the song decoded whole; nothing added)")
