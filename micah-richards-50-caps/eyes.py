"""Find the eyes of every bust / expression / pose head (for blinks and gaze).

Cartoon eyes here are white sclera with a black pupil, so each eye is the sclera blob (near-white, enclosed by outline)
plus the pupil inside it, found in the head area of each 1x cut. Teeth are the other white blobs; they are lower and
excluded by only looking above the nose line (the upper 52 % of the head). Writes build/eyes.json
{part: [[cx, cy, rx, ry], ...]} in SHEET coordinates; check_eyes.py draws them."""
import json, sys, glob, os, cv2, numpy as np
from PIL import Image
from scipy import ndimage

SHEET_OFF = json.load(open("build/cut1x/meta.json"))
BAND = True
WIDEN = ("gy_",)          # only Gary: big pupils behind glasses split his sclera; the other sheets' eyes are already whole


def find(name):
    im = np.asarray(Image.open(f"build/cut1x/{name}.png"))
    rgb, a = im[..., :3].astype(np.int16), im[..., 3]
    h, w = a.shape
    ys, xs = np.nonzero(a > 128)
    top = ys.min()
    # the head is the part above the shoulders: take the rows until the width jumps (shoulders)
    widths = (a > 128).sum(1)
    head_h = h
    mx = widths[top:top + int(0.85 * (h - top))].max() if h - top > 10 else widths.max()
    kind = name.split("_")[1]
    lim = top + int((0.52 if kind in ("b", "e") else 0.36) * (h - top))
    mn, mxc = rgb.min(2), rgb.max(2)
    scl = (a > 200) & (mn > 190) & ((mxc - mn) < 45)
    scl[lim:] = False
    if BAND and kind in ("b", "e"):
        # light hair (Gary's silver hair) also passes as "white with dark specks": eyes sit between brow and nose,
        # i.e. 30-68 % of the way from the top of the head to the chin
        chin = top + (0.89 if kind == "b" else 0.80) * (h - top)
        scl[:int(top + 0.30 * (chin - top))] = False
        scl[int(top + 0.68 * (chin - top)):] = False
    scl = ndimage.binary_opening(scl, iterations=1)
    lab, n = ndimage.label(scl)
    blobs = []
    for i in range(1, n + 1):
        m = lab == i
        area = int(m.sum())
        if area < 18: continue
        yy, xx = np.nonzero(m)
        bw, bh = xx.max() - xx.min() + 1, yy.max() - yy.min() + 1
        if bw < 5 or bh < 4 or bw > 0.45 * w: continue
        if bh > 1.4 * bw or bw > 3.2 * bh: continue
        fill = area / float(bw * bh)
        if fill < 0.45: continue
        if mn[m].mean() < 228: continue                 # sclera is near pure white (~245); light grey hair is ~205
        blobs.append((area, xx.min(), yy.min(), xx.max(), yy.max()))
    # a big pupil can split one sclera into two whites: merge two blobs when only pupil / shine lies between them (no skin)
    def skin_between(p, q):
        _, ax0, ay0, ax1, ay1 = p; _, bx0, by0, bx1, by1 = q
        if ax0 > bx0: p, q = q, p; _, ax0, ay0, ax1, ay1 = p; _, bx0, by0, bx1, by1 = q
        y0_, y1_ = max(ay0, by0), min(ay1, by1)
        if y1_ - y0_ < 0.4 * min(ay1 - ay0, by1 - by0) or bx0 - ax1 > 1.6 * max(ay1 - ay0, by1 - by0): return 1.0
        if bx0 <= ax1 + 1: return 0.0
        g = rgb[y0_:y1_ + 1, ax1 + 1:bx0]
        dk = g.max(2) < 95
        wh = (g.min(2) > 185) & ((g.max(2) - g.min(2)) < 50)
        return float((~dk & ~wh).mean())
    merged = True
    while merged and len(blobs) > 1:
        merged = False
        for i in range(len(blobs)):
            for j in range(i + 1, len(blobs)):
                if skin_between(blobs[i], blobs[j]) < 0.12:
                    p, q = blobs[i], blobs[j]
                    blobs[i] = (p[0] + q[0], min(p[1], q[1]), min(p[2], q[2]), max(p[3], q[3]), max(p[4], q[4]))
                    blobs.pop(j); merged = True; break
            if merged: break
    def pupil(bx):
        _, x0, y0, x1, y1 = bx
        sub = rgb[y0:y1 + 1, x0:x1 + 1]
        return int(((sub.max(2) < 70) & (a[y0:y1 + 1, x0:x1 + 1] > 128)).sum())
    blobs = [b_ for b_ in blobs if pupil(b_) >= 4]           # a real eye has a dark pupil inside it
    blobs.sort(reverse=True)
    def widen(x0, y0, x1, y1):
        """a big pupil splits the sclera: carry the box across the pupil to the last white column on each side (stop at skin)"""
        hb = y1 - y0
        r0, r1 = y0 + int(0.2 * hb), y1 - int(0.2 * hb) + 1
        def scan(start, step, lim):
            last, x = None, start
            for _ in range(lim):
                if x < 0 or x >= w: break
                col = rgb[r0:r1, x]
                dk = col.max(1) < 95
                wh = (col.min(1) > 185) & ((col.max(1) - col.min(1)) < 50)
                if (~dk & ~wh).mean() > 0.3: break
                if wh.any(): last = x
                x += step
            return last
        lim = int(1.3 * hb) + 2
        r = scan(x1 + 1, 1, lim); l = scan(x0 - 1, -1, lim)
        return (l if l is not None else x0), y0, (r if r is not None else x1), y1

    eyes = []
    for area, x0, y0, x1, y1 in blobs[:2]:
        if name.startswith(WIDEN): x0, y0, x1, y1 = widen(x0, y0, x1, y1)
        # include the pupil even where it touches the outline
        eyes.append([(x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 1.5, (y1 - y0) / 2 + 1.5])
    if len(eyes) == 2 and abs(eyes[0][1] - eyes[1][1]) > 0.45 * max(eyes[0][2], eyes[1][2]) * 2.2:
        eyes = eyes[:1]
    eyes.sort()
    ox, oy = SHEET_OFF[name]["off"]
    return [[round(e[0] + ox, 1), round(e[1] + oy, 1), round(e[2], 1), round(e[3], 1)] for e in eyes]


# far eyes the detector cannot see whole (behind a glasses frame on a 3/4 view), sheet coords
MANUAL_ADD = {}
# Gary (glasses, big pupils): read off 8x grids of the sheet, whole sclera incl. the pupil, sheet coords
MANUAL_SET = {
    "gy_b_front":   [[348.3, 624.0, 12.0, 11.0], [390.8, 620.5, 12.2, 11.2]],
    "gy_b_q34L":    [[533.8, 621.8, 10.8, 10.2], [567.5, 616.3, 5.6, 10.6]],
    "gy_b_q34R":    [[855.6, 621.4, 11.0, 10.3], [890.9, 616.1, 5.1, 10.6]],
    "gy_e_neutral": [[334.9, 831.3, 8.8, 7.2], [364.9, 831.3, 8.8, 7.2]],
    "gy_e_amused":  [[550.3, 833.0, 8.4, 4.4], [577.2, 826.8, 5.9, 5.6]],
    "gy_e_smiling": [[1040.6, 833.3, 9.4, 7.5], [1066.0, 830.8, 5.4, 6.9]],
    "gy_e_laughing": [],                     # eyes shut tight: nothing to blink
}


def main(pats):
    out = json.load(open("build/eyes.json")) if os.path.exists("build/eyes.json") else {}
    for n in SHEET_OFF:
        if pats and not any(p in n for p in pats): continue
        kind = n.split("_")[1]
        if kind not in ("b", "e", "p", "t"): continue
        if n.endswith("back"): continue
        if n in MANUAL_SET: out[n] = MANUAL_SET[n]; continue
        found, add = find(n), MANUAL_ADD.get(n, [])
        # a hand-placed eye replaces any partial detection of the same eye
        found = [e for e in found if not any(abs(e[0] - m[0]) < 1.6 * m[2] and abs(e[1] - m[1]) < 1.6 * m[3] for m in add)]
        out[n] = sorted(found + add)
    json.dump(out, open("build/eyes.json", "w"), indent=0)
    return out


if __name__ == "__main__":
    o = main(sys.argv[1:])
    print(len(o), "parts;", sum(1 for v in o.values() if len(v) == 2), "with two eyes,", sum(1 for v in o.values() if len(v) == 1), "with one,",
          [k for k, v in o.items() if not v][:40], "with none")
