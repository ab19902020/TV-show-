"""Which recording each line of the v5 script comes from (`python3 -m studio.film the-undercard lines` re-cuts every
line and the film retimes to it). In order of preference:

  1. the v5 recordings, one file per character with their lines read in script order (voiceovers/v5/, any name with
     the character's id in it: eddie, dana, attendant, security, joshua, referee, announcer, tyson), and the new
     Tyson Fury take (09-tyson-fury-v5.mp3), which has all seven of his lines;
  2. lines whose words are unchanged from the v4 script (REUSE): cut from the v4 takes they were recorded in, found
     there with the v4 script (voiceovers/v4-script.md) for context;
  3. TEMPORARY stand-ins (voiceovers/stand-in/<id>.wav, tools/stand_in_voices.py) for lines not recorded yet, so
     the edit can be timed. The film is never delivered with a stand-in in it: `lines` lists every one it used.

A line is cut from a recording only when the recording is allowed to have it (a v5 file: its own character's lines;
a v4 take: the REUSE lines only), so an old take with similar words can never stand in for a changed line.

The v5 files are read with little silence between lines (and a steady noise floor), so a file is heard in pieces of
at most 8 s split at its quietest moments rather than at silences; where a file holds two readings of a line (the
announcer read both wordings of his optional lines, with a spoken note between them), TAKES names the one used,
as it does a line Whisper mishears too far for the search to find."""
import hashlib
import json
import re
import shutil

import librosa
import numpy as np
import soundfile as sf

from studio.film import ep
from studio.film import voices as V

SPEAKER = {"EDDIE": "eddie", "DANA": "dana", "SECURITY": "security", "ATTENDANT": "attendant", "TYSON": "tyson",
           "JOSHUA": "joshua", "ANNOUNCER": "announcer", "REFEREE": "referee"}
SCRIPT = ep.DIR / "script.md"
VO = ep.DIR / "voiceovers"
MAXGAP = 0.24          # pauses inside a line are trimmed to this (the announcer's dramatic pauses get their own)
GAPS = {"L044": 0.45, "L045": 0.45, "L069": 0.45}
TEMPO = 1.0
EXTRA = {"undercard": "AH N D ER K AA R D", "pillowcase": "P IH L OW K EY S", "podcast": "P AA D K AE S T",
         "medicals": "M EH D IH K AH L Z", "pussy": "P UH S IY", "hearn": "HH ER N", "dunno": "D AH N OW",
         "fifty": "F IH F T IY", "sixty": "S IH K S T IY", "unqualified": "AH N K W AA L AH F AY D",
         "parachutes": "P EH R AH SH UW T S", "anticipation": "AE N T IH S AH P EY SH AH N", "them's": "DH EH M Z", "who've": "HH UW V",
         "pay-per-view": "P EY P ER V Y UW", "jab's": "JH AE B Z", "load-bearing": "L OW D B EH R IH NG",
         "fifty-fifty": "F IH F T IY F IH F T IY", "sixty-forty": "S IH K S T IY F AO R T IY",
         "two-minute": "T UW M IH N AH T", "journey's": "JH ER N IY Z"}

# v5 line <- v4 line: the same words, already recorded
REUSE = {"L020": "L018", "L026": "L024", "L033": "L028", "L035": "L030", "L016": "L009", "L071": "L054",
         "L072": "L055", "L065": "L045", "L043": "L034", "L055": "L040", "L070": "L053"}
# line -> (v5 file, from s, to s): the reading used where the file has two
TAKES = {"L045": ("announcer", 12.55, 20.98), "L069": ("announcer", 28.50, 31.75),
         "L025": ("dana", 12.25, 14.10)}             # (Whisper hears "you security shit": found by hand)
V4_RECORDINGS = [(VO / "01-dana-white-take2-L030.wav", "dana"), (VO / "01-dana-white-take2-L058.wav", "dana"),
                 (VO / "01-dana-white-take1.mp3", "dana"),
                 (VO / "02-eddie-hearn.mp3", "eddie"), (VO / "03-ring-announcer.mp3", "announcer"),
                 (VO / "04-security-guard.mp3", "security"), (VO / "05-boxing-referee.mp3", "referee"),
                 (VO / "06-laundry-attendant.mp3", "attendant"), (VO / "07-tyson-fury.mp3", "tyson"),
                 (VO / "08-anthony-joshua.mp3", "joshua")]


def _parse(path):
    return [(lid, SPEAKER[spk], text) for lid, spk, text in
            re.findall(r"^\[(L\d+)\]\s+([A-Z]+):\s*(?:\([^)]*\)\s*)?(.+)$", path.read_text(), re.M)]


def script():
    return _parse(SCRIPT)


IDS = [lid for lid, _, _ in script()]


def v5_recordings():
    out = [(VO / "09-tyson-fury-v5.mp3", "tyson")]
    for p in sorted((VO / "v5").glob("*")) if (VO / "v5").exists() else []:
        if p.suffix.lower() not in (".mp3", ".wav", ".m4a", ".flac", ".ogg"):
            continue
        who = next((w for w in SPEAKER.values() if w in p.name.lower()), None)
        if who:
            out.append((p, who))
    return out


RECORDINGS = v5_recordings()


def heard_fine(path, y16, maxlen=8.0):
    """Whisper's transcript of a recording in pieces of at most maxlen s, split at the quietest 150 ms (cached)"""
    from studio.episode.asr import recognizer
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    cf = ep.BUILD / "asr" / f"fine-{sha}.json"
    if cf.exists():
        return json.loads(cf.read_text())
    hop = 160
    e = librosa.feature.rms(y=y16, frame_length=400, hop_length=hop)[0]
    e = np.convolve(e, np.ones(15) / 15, mode="same")

    def split(a, b):
        if b - a <= maxlen:
            return [[a, b]]
        i0, i1 = int((a + 0.2 * (b - a)) * 16000 / hop), int((b - 0.2 * (b - a)) * 16000 / hop)
        t = (i0 + int(np.argmin(e[i0:i1]))) * hop / 16000
        return split(a, t) + split(t, b)

    out = []
    for a, b in [p for s_ in V.stretches(y16) for p in split(*s_)]:
        x = np.concatenate([np.zeros(4000, np.float32), y16[int(a * 16000):int(b * 16000)], np.zeros(8000, np.float32)])
        st = recognizer().create_stream()
        st.accept_waveform(16000, x)
        recognizer().decode_stream(st)
        out.append([round(a, 3), round(b, 3), st.result.text.strip()])
    cf.parent.mkdir(parents=True, exist_ok=True)
    cf.write_text(json.dumps(out, indent=1))
    return out          # (the CLI passes these on; the work is done in from_recordings below)


def cut_from(out_dir, path, spk, script_, allow, maxgap, gaps, k, extra, rename=None, whole=False, fine=False,
             span=None):
    """the allowed lines found in one recording -> {id: line data}, each written to out_dir/lines/<id>.wav (the
    engine's from_recordings, for one file, keeping what it finds instead of failing on what it does not).
    whole: the file (or its span (from, to) s) is the one allowed line; fine: heard in short pieces"""
    y, _ = librosa.load(str(path), sr=V.SR, mono=True)
    t0 = 0.0
    if span:
        t0 = span[0]
        y = y[int(span[0] * V.SR):int(span[1] * V.SR)]
    y16 = librosa.resample(y, orig_sr=V.SR, target_sr=16000)
    mine = [(lid, text) for lid, sp, text in script_ if sp == spk]
    if whole or span:                                # one line: no search, the whole file (or span) is the line
        chunks = [[0.0, len(y) / V.SR, ""]]
        where = {lid: (0, 0, 1.0) for lid in allow}
    else:
        chunks = heard_fine(path, y16) if fine else V.heard(path, y16, ep.BUILD / "asr")
        where = V.locate(chunks, mine)               # every line found (the neighbours of an allowed line are
    order = [lid for lid, _ in mine if lid in where]  # aligned with it: a stretch often holds several lines)
    groups = []
    for lid in order:
        if groups and where[lid][0] <= where[groups[-1][-1]][1]:
            groups[-1].append(lid)
        else:
            groups.append([lid])
    text = dict(mine)
    found = {}
    for g in groups:
        if not any(lid in allow for lid in g):
            continue
        c0, c1 = where[g[0]][0], max(where[lid][1] for lid in g)
        a = max(chunks[c0 - 1][1] + 0.02 if c0 > 0 else 0.0, chunks[c0][0] - 0.15)
        b = min(chunks[c1 + 1][0] - 0.02 if c1 + 1 < len(chunks) else len(y) / V.SR, chunks[c1][1] + 0.15)
        yg = y[int(a * V.SR):int(b * V.SR)]
        ws = [V.words_of(text[lid]) for lid in g]
        al = V.align_samples(y16[int(a * 16000):int(b * 16000)], sum(ws, []), extra)
        W, P = al["words"], al["phones"]
        i = 0
        for lid, w in zip(g, ws):
            seg, wl, pl = V.cut(yg, W, P, i, i + len(w) - 1, (gaps or {}).get(lid, maxgap), k)
            i += len(w)
            if lid not in allow:
                continue
            nid = (rename or {}).get(lid, lid)
            sf.write(out_dir / "lines" / f"{nid}.wav", seg.astype(np.float32), V.SR)
            found[nid] = dict(speaker=spk, dur=round(len(seg) / V.SR, 3), text=text[lid], words=wl, phones=pl,
                              source=f"{path.name} {t0 + a + wl[0]['s']:.2f}s")
            print(f"{nid:8s} {spk:9s} {len(seg) / V.SR:5.2f}s  {path.name} @{t0 + a:6.2f}s  {text[lid]}")
    return found


def from_recordings(out_dir, recordings, script_, want, maxgap=0.2, gaps=None, k=1.0, extra=None):
    (out_dir / "lines").mkdir(parents=True, exist_ok=True)
    spk_of = {lid: sp for lid, sp, _ in script_}
    found = {}
    # 1. the v5 recordings: each character's file may give any of that character's lines (the chosen readings first)
    recs = v5_recordings()
    for lid, (who, a, b) in TAKES.items():
        path = next((p for p, s_ in recs if s_ == who), None)
        if lid in want and path:
            found.update(cut_from(out_dir, path, who, script_, {lid}, maxgap, gaps, k, extra, span=(a, b)))
    for path, spk in recs:
        allow = {lid for lid in want if spk_of[lid] == spk and lid not in found and lid not in TAKES}
        if allow:
            found.update(cut_from(out_dir, path, spk, script_, allow, maxgap, gaps, k, extra,
                                  fine=path.parent.name == "v5"))
    # 2. unchanged lines from the v4 takes, found with the v4 script round them
    old = _parse(VO / "v4-script.md")
    back = {o: n for n, o in REUSE.items() if n in want and n not in found}
    for path, spk in V4_RECORDINGS:
        allow = {o for o in back if dict((l, s) for l, s, _ in old)[o] == spk and back[o] not in found}
        if allow and path.exists():
            found.update(cut_from(out_dir, path, spk, old, allow, maxgap, gaps, k, extra, rename=back))
    # 3. temporary stand-ins
    temp = []
    for lid in want:
        p = VO / "stand-in" / f"{lid}.wav"
        if lid not in found and p.exists():
            got = cut_from(out_dir, p, spk_of[lid], script_, {lid}, maxgap, gaps, k, extra, whole=True)
            if lid in got:
                got[lid]["temp"] = True
                found.update(got)
                temp.append(lid)
    missing = [lid for lid in want if lid not in found]
    if missing:
        raise KeyError(f"not found in any recording: {missing}")
    out = {lid: found[lid] for lid, *_ in script_ if lid in found}
    (out_dir / "lines.json").write_text(json.dumps(out, indent=1))
    print(f"\n{len(out) - len(temp)} lines from recordings, {len(temp)} TEMPORARY stand-ins: {' '.join(temp)}")
    return out


V.from_recordings = from_recordings          # the CLI's `lines` calls voices.from_recordings with RECORDINGS
