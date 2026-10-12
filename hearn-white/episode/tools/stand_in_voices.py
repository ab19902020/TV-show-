"""TEMPORARY stand-in voices for The Undercard: a line with no recording yet is spoken by Kokoro (studio.episode.tts,
`tools/fetch_models.sh tts`) with a voice per character and the delivery's pace, written to
voiceovers/stand-in/<line id>.wav, so the edit can be timed before the actors' takes arrive. film/lines.py uses a
stand-in only for a line no recording has, and lists every one it used; the film is not delivered with them.

    python3 episodes/the-undercard/tools/stand_in_voices.py [L001 ...]"""
import re
import sys
from pathlib import Path

import soundfile as sf

from studio.episode import tts

EP = Path(__file__).resolve().parents[1]
VOICE = {   # who: (Kokoro voice, speed)
    "EDDIE": ("bm_george", 1.06), "DANA": ("am_michael", 1.02), "SECURITY": ("bm_fable", 0.96),
    "ATTENDANT": ("bf_emma", 0.92), "TYSON": ("bm_lewis", 1.0), "JOSHUA": ("bm_daniel", 1.0),
    "ANNOUNCER": ("am_onyx", 0.9), "REFEREE": ("am_eric", 1.0)}
PACE = {"rapid, covering panic": 1.22, "whisper, proposing": 1.05, "serious sports ceremony": 0.88,
        "breathing hard": 0.95, "breathing hard, inventing excuse": 0.95, "outraged": 1.12, "flat": 0.92,
        "fast recovery": 1.1, "quick correction": 1.12, "urgent, to ref": 1.12, "without looking": 0.92}
# said as it should sound (the script's wording is unchanged on screen)
SAY = [("…", ", "), ("—", ""), ("EDDIE HEARN", "Eddie Hearn"), ("DANA WHITE", "Dana White"), ("Mr White", "Mister White")]


def lines():
    out = []
    for lid, who, cue, text in re.findall(r"^\[(L\d+)\]\s+([A-Z]+):\s*(?:\(([^)]*)\)\s*)?(.+)$",
                                          (EP / "script.md").read_text(), re.M):
        out.append((lid, who, cue, text))
    return out


def main(only):
    ids = tts.speaker_ids()
    out = EP / "voiceovers" / "stand-in"
    out.mkdir(parents=True, exist_ok=True)
    for lid, who, cue, text in lines():
        if only and lid not in only:
            continue
        v, sp = VOICE[who]
        sp *= PACE.get(cue, 1.0)
        say = text
        for a, b in SAY:
            say = say.replace(a, b)
        x = tts.speak(say, v, sp, ids)
        sf.write(out / f"{lid}.wav", x, tts.SR, subtype="PCM_16")
        print(f"{lid} {who:9s} {len(x) / tts.SR:5.2f}s {text}")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
