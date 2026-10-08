"""The song analysis with this song's own words added to the pronouncing dictionary, then the engine's analyser:

    python3 -m film.analyse      (run from the repo root with PYTHONPATH=episodes/white-pele:.)

Writes build/song.json. After checking it, it is reviewed and corrected (film/retime.py) into song-timing.json."""
from studio.film import ep, song, voices

WORDS = {
    "croxteth": "K R AA K S T AH TH",
    "defences": "D IH F EH N S IH Z",
    "merseyside": "M ER Z IY S AY D",
    "pele": "P EH L EY",
}


def main():
    ep.use("white-pele")
    voices.EXTRA.update(WORDS)
    song.analyse(ep.DIR / "song.mp3", ep.BUILD)


if __name__ == "__main__":
    main()
