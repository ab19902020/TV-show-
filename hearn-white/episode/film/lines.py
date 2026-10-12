"""Which recording each scripted line comes from: the delivered voice-overs, one file per character with their lines
read in script order (voiceovers/). Dana came as two takes: take 1 for every line except L030 and L058, which are
take 2's cleaner reads (tools/dana_picks.py cuts them to 01-dana-white-take2-L030.wav / -L058.wav, read first). A
speaker's line is taken from the first file in RECORDINGS that has it. `python3 -m studio.film the-undercard
lines` re-cuts every line and the film retimes."""
import re

from studio.film import ep

SPEAKER = {"EDDIE": "eddie", "DANA": "dana", "SECURITY": "security", "ATTENDANT": "attendant", "TYSON": "tyson",
           "JOSHUA": "joshua", "ANNOUNCER": "announcer", "REFEREE": "referee"}
SCRIPT = ep.DIR / "script.md"
VO = ep.DIR / "voiceovers"
MAXGAP = 0.24          # pauses inside a line are trimmed to this (the announcer's dramatic pauses get their own)
GAPS = {"L014": 0.45, "L034": 0.35, "L035": 0.45, "L036": 0.45, "L052": 0.45}
TEMPO = 1.0
EXTRA = {"undercard": "AH N D ER K AA R D", "pillowcase": "P IH L OW K EY S", "podcast": "P AA D K AE S T",
         "medicals": "M EH D IH K AH L Z", "pussy": "P UH S IY", "hearn": "HH ER N", "dunno": "D AH N OW",
         "fifty": "F IH F T IY", "sixty": "S IH K S T IY"}


def script():
    return [(lid, SPEAKER[spk], text) for lid, spk, text in
            re.findall(r"^\[(L\d+)\]\s+([A-Z]+):\s*(?:\([^)]*\)\s*)?(.+)$", SCRIPT.read_text(), re.M)]


IDS = [lid for lid, _, _ in script()]
RECORDINGS = [(VO / "01-dana-white-take2-L030.wav", "dana"), (VO / "01-dana-white-take2-L058.wav", "dana"),
              (VO / "01-dana-white-take1.mp3", "dana"),
              (VO / "02-eddie-hearn.mp3", "eddie"), (VO / "03-ring-announcer.mp3", "announcer"),
              (VO / "04-security-guard.mp3", "security"), (VO / "05-boxing-referee.mp3", "referee"),
              (VO / "06-laundry-attendant.mp3", "attendant"), (VO / "07-tyson-fury.mp3", "tyson"),
              (VO / "08-anthony-joshua.mp3", "joshua")]
