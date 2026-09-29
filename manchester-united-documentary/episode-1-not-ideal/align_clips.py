"""Word + phone forced alignment (pocketsphinx, en-us model from the PyPI wheel) of every raw voice clip
against its corrected transcript. Output: phones.json {clip: {dur, words:[{w,s,e,ph}], phones:[{p,w,s,e}]}}."""
import json, re, sys, numpy as np, librosa
from pocketsphinx import Decoder

TEXT = {
 "jason/Clony-AI-jOUZbRL3oERxwWzo.mp3": "Right Michael. New season. New chapter. We've got a very clear plan. One second. Well first and foremost clarity. Alignment. Sustainability. Agility. Yeah? We've got options. That's one of the options. At the moment a lot.",
 "jason/Clony-AI-rkUcZyntNsdrtWiq.mp3": "Enough that we're not buying a striker. Long term sustainability. Squad cost regulations. Gentlemen fantastic. This is the plan. I've actually got another meeting. European DNA. Clear plan.",
 "Carrick/Clony-AI-MbfWqpLIZh9ThTuk.mp3": "What's the plan? Right. Yep. Okay. Jason. Who are we signing? I know. I'm just thinking. Another striker? No? Benjamin's injured. He's injured. Left back? Centre back? Another forward? Goalkeeper? Fair enough. How much?",
 "Carrick/Clony-AI-FigW3R4wGa7AVJWL.mp3": "How much is a lot? Right. So. Sell to buy? Sell to buy. And the objectives? Anything else? And I've got everything I need? Brilliant. Good meeting. Positive. Good meeting. So where's the money actually going? Glazer dividends? Oh. Cheers.",
 "Carrick/Clony-AI-nCbSTDErPKHckMCM.mp3": "Brilliant. Yep. Good input. Newly promoted team. Crowd will be up for it. Do the basics. And most importantly set pieces. Right. Not ideal. It's one game. You can't judge a season after one game. Did he? Now concentrate.",
 "omar/Clony-AI-gpqmga8px6et6YNx.mp3": "Michael we've invested significantly. I would describe it as responsive squad optimization. Cash flow. Infrastructure. Technically there weren't any dividends paid this year. Morning Joel.",
 "jim/Clony-AI-N1Fxua8QKhHIuO2y.mp3": "No. No. You already asked that. We've got one. Don't complain about the squad. Debt. Funny you should mention them. Unfortunately. Right. Hull. Don't lose.",
 "j glazer/Clony-AI-ecyktuuXcVQCHNGa.mp3": "Hello everybody. Can you hear us? Michael. Good luck this season. We're all really excited. Big season. Go United. Jason how's the season going?",
 "a glazer/Clony-AI-VGllzn0mfCmq0W7T.mp3": "Michael. Good luck this season. Need to run.",
 "harry m/Clony-AI-Kzk4F3tsMBLpnbPz.mp3": "Set pieces. Got it. Two set pieces. He did. Very clear. Execution. You did. For about eight minutes. Any time. It counts in expected goals. What? I've been listening to Jason.",
}
EXTRA = {"optimization": "AA P T AH M AH Z EY SH AH N", "glazer": "G L EY Z ER", "centre": "S EH N T ER"}

def words_of(text):
    return re.sub(r"[^a-z' ]", " ", text.lower().replace("-", " ")).split()

def align(f, text):
    y, _ = librosa.load(f, sr=16000, mono=True)
    pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
    d = Decoder(samprate=16000, bestpath=False, loglevel="FATAL")
    for w, ph in EXTRA.items():
        if d.lookup_word(w) is None: d.add_word(w, ph, True)
    ws = words_of(text)
    d.set_align_text(" ".join(ws))
    d.start_utt(); d.process_raw(pcm, full_utt=True); d.end_utt()
    d.set_alignment()
    d.start_utt(); d.process_raw(pcm, full_utt=True); d.end_utt()
    words, phones = [], []
    for wseg in d.get_alignment():
        name = re.sub(r"\(\d+\)$", "", wseg.name)
        if name in ("<sil>", "<s>", "</s>", "[NOISE]"): continue
        i = len(words)
        ps = [(p.name, p.start / 100, (p.start + p.duration) / 100) for p in wseg]
        words.append({"w": name, "s": wseg.start / 100, "e": (wseg.start + wseg.duration) / 100, "ph": [p[0] for p in ps]})
        phones += [{"p": n, "w": i, "s": s, "e": e} for n, s, e in ps]
    assert [w["w"] for w in words] == ws, ([w["w"] for w in words], ws)
    return {"dur": len(y) / 16000, "words": words, "phones": phones}

out = {}
for k, t in TEXT.items():
    out[k] = align("audio_raw/show TV/" + k, t)
    print("==", k); print("  ".join(f"{w['w']}@{w['s']:.2f}-{w['e']:.2f}" for w in out[k]["words"]))
json.dump(out, open("phones.json", "w"), indent=1)
