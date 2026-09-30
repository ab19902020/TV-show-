"""Caption cards (spoken dialogue only, never the performance tags) and the subtitle files.

Each phrase of the script is split into cards of at most two lines at the portrait caption size, preferring breaks
at punctuation; a card is on screen from its first word to its last (held on through short pauses, at least 0.9 s).
The wording is the script's, with the recording's own words where they differ (build/timeline.json).

-> build/captions.json, soriano_parody.srt, soriano_parody.vtt"""
import json, re
from PIL import Image, ImageDraw
import graphics as G

W, H = 1080, 1920                      # cards are fitted at the portrait size (the narrower one)

def fits(d, text):
    f = G.font("Inter", 50, 800)
    return len(G.wrap(d, text, f, W * 0.80)) <= 2

def split_phrase(d, text):
    toks = text.split()
    cards, cur = [], []
    for tok in toks:
        if not cur or fits(d, " ".join(cur + [tok])):
            cur.append(tok); continue
        # break at the last punctuation in the second half of the card if there is one
        cut = None
        for i in range(len(cur) - 1, len(cur) // 2 - 1, -1):
            if re.search(r"[,.;:?!]$", cur[i]): cut = i + 1; break
        if cut and cut < len(cur):
            cards.append(cur[:cut]); cur = cur[cut:] + [tok]
        else:
            cards.append(cur); cur = [tok]
    if cur: cards.append(cur)
    return [" ".join(c) for c in cards]

def norm(tok):
    from script import SAID
    ws = []
    for w in re.sub(r"[^a-z0-9' ]", " ", tok.lower().replace("-", " ")).split():
        ws += SAID.get(w, [w])
    return ws

def build():
    tl = json.load(open("build/timeline.json"))
    words = tl["words"]
    d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    cards = []
    for B in tl["beats"]:
        for p in B["phrases"]:
            k = p["w0"]
            for text in split_phrase(d, p["text"]):
                n = sum(len(norm(t)) for t in text.split())
                ws = words[k:k + n]; k += n
                cards.append({"beat": B["n"], "text": text, "s": ws[0]["s"], "e": ws[-1]["e"]})
            assert k == p["w1"] + 1, p["text"]
    for c in cards: c["show"] = round(c["s"] - 0.06, 3)
    for i, c in enumerate(cards):
        nxt = cards[i + 1]["show"] if i + 1 < len(cards) else c["e"] + 1.2
        end = c["e"] + 0.25
        if nxt - end < 0.6: end = nxt                 # held through a short pause
        end = max(end, min(c["s"] + 0.9, nxt))
        c["hide"] = round(min(end, nxt), 3)
    json.dump(cards, open("build/captions.json", "w"), indent=1)
    def ts(t, sep):
        h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
        return f"{h:02d}:{m:02d}:{int(s):02d}{sep}{int(round((s - int(s)) * 1000)):03d}"
    with open("soriano_parody.srt", "w") as f:
        for i, c in enumerate(cards, 1):
            f.write(f"{i}\n{ts(c['show'], ',')} --> {ts(c['hide'], ',')}\n{c['text']}\n\n")
    with open("soriano_parody.vtt", "w") as f:
        f.write("WEBVTT\n\n")
        for i, c in enumerate(cards, 1):
            f.write(f"{i}\n{ts(c['show'], '.')} --> {ts(c['hide'], '.')}\n{c['text']}\n\n")
    print(len(cards), "caption cards")
    for c in cards[:8]: print(f"  {c['show']:7.2f}-{c['hide']:7.2f} {c['text']}")

if __name__ == "__main__":
    build()
