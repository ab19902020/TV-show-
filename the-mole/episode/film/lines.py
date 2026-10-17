"""Which recording each scripted line comes from. The voices were made in Clony AI from the actors' sheets: the
narrator in one file, Wilcox in one, Lisandro in two (voiceovers/). Every line is found in its recording and cut
word-exact (studio.film.voices.from_recordings) -> build/lines/<id>.wav and build/lines.json.
L061 (the narrator's "Next time...") and L063 (Wilcox's "We're not here.") were not recorded: the cut ends without them."""
import re

from studio.film import ep

SPEAKER = {"NARRATOR": "narrator", "LISANDRO": "licho", "WILCOX": "wilcox"}
SCRIPT = ep.DIR / "script.md"
VO = ep.DIR / "voiceovers"
RECORDINGS = [(VO / "01-narrator.mp3", "narrator"), (VO / "02-lisandro-martinez-1.mp3", "licho"),
              (VO / "02-lisandro-martinez-2.mp3", "licho"), (VO / "03-jason-wilcox.mp3", "wilcox")]
IDS = [f"L{n:03d}" for n in range(1, 64) if n not in (61, 63)]
MAXGAP = 0.22          # pauses inside a line are trimmed to this
GAPS = {"L001": 0.45, "L009": 0.3, "L010": 0.4, "L017": 0.45, "L023": 0.8, "L028": 0.5, "L040": 0.35,
        "L041": 0.5, "L054": 0.45}   # the pauses the lines are built on
TEMPO = 1.0            # the performances as recorded
EXTRA = {"lisandro": "L IH S AE N D R OW", "berrada": "B EH R AA D AH", "bielsa": "B IY EH L S AH",
         "hermano": "ER M AA N OW", "immersing": "IH M ER S IH NG", "shhh": "SH"}


def script():
    """every scripted line in order: [(id, speaker, text)]"""
    return [(lid, SPEAKER[spk], text) for lid, spk, text in
            re.findall(r"^\[(L\d+)\]\s+([A-Z]+):\s*(.+)$", SCRIPT.read_text(), re.M)]
