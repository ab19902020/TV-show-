"""Browser preview: preview.html next to the two videos, with play / pause, seek, restart, a portrait / landscape
switch, optional subtitles (off by default: the film is not subtitled) and the cue list (click a line to jump to it).
Open it straight from the folder; the cues are embedded, so it needs no server.

-> preview.html"""
import json

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Soriano parody preview</title>
<style>
:root{--bg:#0f1115;--panel:#181b22;--ink:#eceef3;--mute:#9aa1ad;--red:#c8102e;--line:#2a2f3a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{padding:14px 16px;border-bottom:1px solid var(--line)}header b{letter-spacing:.04em}header span{color:var(--mute);margin-left:8px;font-size:13px}
main{display:grid;grid-template-columns:minmax(0,auto) minmax(260px,420px);gap:16px;padding:16px;max-width:1500px;margin:auto}
@media(max-width:900px){main{grid-template-columns:1fr}}
.stage{background:#000;border-radius:10px;overflow:hidden;display:flex;justify-content:center}
video{display:block;max-width:100%;max-height:78vh;background:#000}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px}
button{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;cursor:pointer}
button:hover{border-color:#4a5263}button.on{border-color:var(--red);color:#fff}
input[type=range]{flex:1;min-width:160px;accent-color:var(--red)}
.time{font-variant-numeric:tabular-nums;color:var(--mute);min-width:110px;text-align:right}
.cues{background:var(--panel);border:1px solid var(--line);border-radius:10px;max-height:82vh;overflow:auto}
.cue{padding:9px 12px;border-bottom:1px solid var(--line);cursor:pointer}.cue:hover{background:#1f232c}
.cue.now{background:#2a1418;border-left:3px solid var(--red)}
.cue .t{color:var(--mute);font-size:12px}.cue .m{color:var(--mute);font-size:12px;margin-top:2px}
.note{color:var(--mute);font-size:12px;padding:0 16px 16px}
</style></head><body>
<header><b>UNITED ROAD</b><span>SATIRE &mdash; FICTIONAL DIALOGUE &middot; &ldquo;Essentially, We Did It&rdquo; preview</span></header>
<main>
<section>
<div class="stage"><video id="v" playsinline preload="metadata"><source id="src" src="soriano_parody_portrait.mp4" type="video/mp4">
<track id="subs" kind="subtitles" src="soriano_parody.vtt" srclang="en" label="English"></video></div>
<div class="bar">
<button id="play">Play</button><button id="restart">Restart</button>
<input id="seek" type="range" min="0" max="1000" value="0" aria-label="Seek"><span class="time" id="time">0:00 / 0:00</span>
</div>
<div class="bar"><button id="fmt-p" class="on">Portrait</button><button id="fmt-l">Landscape</button><button id="cc">Subtitles off</button></div>
</section>
<aside class="cues" id="cues"></aside>
</main>
<p class="note">All dialogue is invented parody. It is not a genuine statement, confession, quotation, or factual admission by Ferran Soriano or Manchester City.</p>
<script>
const CUES = __CUES__;
const v = document.getElementById('v'), seek = document.getElementById('seek'), time = document.getElementById('time');
const fmt = s => { s = Math.max(0, s || 0); return Math.floor(s / 60) + ':' + String(Math.floor(s % 60)).padStart(2, '0'); };
const list = document.getElementById('cues');
CUES.forEach((c, i) => {
  const d = document.createElement('div'); d.className = 'cue'; d.id = 'c' + i;
  d.innerHTML = `<div class="t">${fmt(c.start)} &middot; beat ${c.beat} &middot; ${c.camera}</div><div>${c.phrase}</div>` +
                `<div class="m">${c.gesture}${c.expression ? ' &middot; ' + c.expression : ''}${c.overlay ? ' &middot; [' + c.overlay + ']' : ''}</div>`;
  d.onclick = () => { v.currentTime = c.start - 0.2; v.play(); };
  list.appendChild(d);
});
const playBtn = document.getElementById('play');
playBtn.onclick = () => v.paused ? v.play() : v.pause();
v.onplay = () => playBtn.textContent = 'Pause'; v.onpause = () => playBtn.textContent = 'Play';
document.getElementById('restart').onclick = () => { v.currentTime = 0; v.play(); };
seek.oninput = () => { if (v.duration) v.currentTime = seek.value / 1000 * v.duration; };
let last = -1;
v.ontimeupdate = () => {
  if (v.duration) { seek.value = v.currentTime / v.duration * 1000; time.textContent = fmt(v.currentTime) + ' / ' + fmt(v.duration); }
  let k = -1; CUES.forEach((c, i) => { if (v.currentTime >= c.start - 0.05) k = i; });
  if (k !== last) { if (last >= 0) document.getElementById('c' + last).classList.remove('now');
    if (k >= 0) { const e = document.getElementById('c' + k); e.classList.add('now'); e.scrollIntoView({block: 'nearest'}); } last = k; }
};
v.onloadedmetadata = () => { time.textContent = fmt(0) + ' / ' + fmt(v.duration); v.textTracks[0].mode = cc ? 'showing' : 'hidden'; };
function setFmt(f) {
  const t = v.currentTime, playing = !v.paused;
  document.getElementById('src').src = 'soriano_parody_' + f + '.mp4'; v.load();
  v.addEventListener('loadedmetadata', () => { v.currentTime = t; if (playing) v.play(); }, {once: true});
  document.getElementById('fmt-p').classList.toggle('on', f === 'portrait');
  document.getElementById('fmt-l').classList.toggle('on', f === 'landscape');
}
document.getElementById('fmt-p').onclick = () => setFmt('portrait');
document.getElementById('fmt-l').onclick = () => setFmt('landscape');
let cc = false; const ccBtn = document.getElementById('cc');
ccBtn.onclick = () => { cc = !cc; v.textTracks[0].mode = cc ? 'showing' : 'hidden'; ccBtn.textContent = cc ? 'Subtitles on' : 'Subtitles off'; ccBtn.classList.toggle('on', cc); };
document.addEventListener('keydown', e => { if (e.code === 'Space' && e.target === document.body) { e.preventDefault(); playBtn.click(); } });
</script></body></html>
"""

if __name__ == "__main__":
    cues = json.load(open("soriano_cues.json"))
    open("preview.html", "w").write(PAGE.replace("__CUES__", json.dumps(cues)))
    print("preview.html with", len(cues), "cues")
