"""Rio's clip, every line cut out of it word-exact (studio.film.voices.from_recordings) -> build/lines/"""
import re

from studio.film import ep

SPEAKER = {"RIO": "rio"}
SCRIPT = ep.DIR / "script.md"
RECORDINGS = [(ep.DIR / "voiceovers" / "01-rio-ferdinand.wav", "rio")]
IDS = [f"L{n:03d}" for n in range(1, 9)]
MAXGAP = 0.32
GAPS = {}
TEMPO = 1.0
EXTRA = {"ruben": "R UW B EH N"}


def script():
    return [(lid, SPEAKER[spk], text) for lid, spk, text in
            re.findall(r"^\[(L\d+)\]\s+([A-Z]+):\s*(.+)$", SCRIPT.read_text(), re.M)]
