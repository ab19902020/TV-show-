"""Stand-in voices for The Undercard: the pack has no recordings, so every line is spoken by Kokoro (studio.episode.tts,
`tools/fetch_models.sh tts`) with a voice per character, the delivery's pace, and the take written to
voiceovers/<line id>.wav. Replace any file with the actor's recording of the same line (same name) and re-run
`python3 -m studio.film the-undercard lines`: the whole film retimes to it.

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
PACE = {"rapid negotiation": 1.22, "whispering": 1.08, "ceremonial": 0.88, "breathless": 0.95, "under breath": 1.1,
        "immediate bluff": 1.0, "outraged": 1.12, "instantly pitching": 1.15, "flat": 0.92}
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
    (EP / "voiceovers").mkdir(exist_ok=True)
    for lid, who, cue, text in lines():
        if only and lid not in only:
            continue
        v, sp = VOICE[who]
        sp *= PACE.get(cue, 1.0)
        say = text
        for a, b in SAY:
            say = say.replace(a, b)
        x = tts.speak(say, v, sp, ids)
        sf.write(EP / "voiceovers" / f"{lid}.wav", x, tts.SR, subtype="PCM_16")
        print(f"{lid} {who:9s} {len(x) / tts.SR:5.2f}s {text}")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
