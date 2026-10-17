"""Which recording each scripted line comes from. The two actors' takes are one file each (voiceovers/), every
line cut from them word-exact (studio.film.voices.from_recordings) -> build/lines/<id>.wav and build/lines.json"""
import re

from studio.film import ep

SPEAKER = {"SAEED": "saeed", "RIO": "rio"}
SCRIPT = ep.DIR / "script.md"
VO = ep.DIR / "voiceovers"
RECORDINGS = [(VO / "saeed.mp3", "saeed"), (VO / "rio.mp3", "rio")]
IDS = [f"L{n:03d}" for n in range(1, 15)]
MAXGAP = 0.28
GAPS = {}
TEMPO = 1.0
EXTRA = {"saeed": "S AY IY D", "glazers": "G L EY Z ER Z", "ferdinand": "F ER D IH N AE N D",
         "pundit": "P AH N D IH T"}


def script():
    return [(lid, SPEAKER[spk], text) for lid, spk, text in
            re.findall(r"^\[(L\d+)\]\s+([A-Z]+):\s*(.+)$", SCRIPT.read_text(), re.M)]
