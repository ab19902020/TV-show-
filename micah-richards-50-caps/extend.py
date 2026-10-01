"""extend.py: give every head-and-shoulders bust a torso, so behind a desk or a table it reads as a seated person.

The busts end in a straight cut across the upper chest. For each bust part (`*_b_*`, `*_e_*`) this writes `<name>_x`: the same drawing
with the chest continued downwards by ~0.8 of the bust's height. The new rows are the bust's own last clean rows, re-mapped so the
torso keeps its shape instead of becoming vertical stripes:

  * the shirt / skin V between the lapels closes in towards the centre (the lapel outlines run diagonally, like a jacket's V),
  * a tie in the middle keeps its width,
  * the jacket's outer edges flare out a little (shoulders into arms),
  * flat cel colour: the source row is median-filtered first, and the jacket darkens slightly towards the bottom.

Nothing above the cut changes, so the eyes, mouth, head box and neck pivot (sheet coordinates measured from the part's top-left) are the
same for `<name>` and `<name>_x`. The seam is continuous because the first new row is the bust's own last row, unwarped."""
import json, sys, numpy as np, cv2
from PIL import Image

P = "build/parts/"
HEADS = json.load(open("build/heads.json"))


def lum(c):
    return c[..., 0] * 0.3 + c[..., 1] * 0.59 + c[..., 2] * 0.11


def extend(name, frac=0.8, narrow=0.42, flare=0.07):
    im = np.asarray(Image.open(P + name + ".png")).astype(np.float32)
    H, W = im.shape[:2]
    solid = (im[..., 3] > 128).sum(1) > 8
    last = int(np.nonzero(solid)[0].max())
    # source row: vertical median of a few clean rows above the cut, then a horizontal median (flat cel colour, no streaks)
    band = im[last - 12:last - 2]
    src = np.median(band, axis=0).astype(np.float32)
    src = np.dstack([cv2.medianBlur(np.ascontiguousarray(src[None, :, k]).astype(np.uint8), 5)[0] for k in range(4)]).astype(np.float32)[0]
    alive = np.nonzero(src[:, 3] > 128)[0]
    L, R = int(alive.min()), int(alive.max())
    # centre of the V: the neck pivot (heads.json, sheet coords) if it lies inside the row, else the middle of the silhouette
    meta = json.load(open(P + "meta.json"))[name]
    base = name[:-2] if name.endswith("_x") else name
    c = (L + R) / 2
    if base in HEADS:
        nx = (HEADS[base]["neck"][0] - meta["off"][0]) * 4
        if L + 0.15 * (R - L) < nx < R - 0.15 * (R - L): c = nx
    # jacket colour: sampled at a quarter of the way in from each edge
    jl, jr = src[int(L + 0.12 * (R - L))][:3], src[int(R - 0.12 * (R - L))][:3]
    def is_jacket(x):
        col = src[x][:3]
        return min(np.abs(col - jl).max(), np.abs(col - jr).max()) < 38 and src[x][3] > 128
    def lapel(step):
        x, run = int(round(c)), 0
        while L < x < R:
            run = run + 1 if is_jacket(x) else 0
            if run >= 7: return abs(x - step * 6 - c)
            x += step
        return abs(x - c)
    if np.abs(jl - jr).max() > 40:                     # one side is covered (a hand at the chin): the jacket is the darker sample
        jl = jr = (jl if jl.sum() < jr.sum() else jr)
    Dl, Dr = lapel(-1), lapel(1)
    if Dr > 1.8 * Dl: Dr = 1.15 * Dl                    # the covered side's lapel is not found: mirror the clean one
    if Dl > 1.8 * Dr: Dl = 1.15 * Dr
    # a tie: a dark run straddling the centre
    T = 0
    lc = lum(src[:, :3])
    if lc[int(round(c))] < 80:
        while T < min(Dl, Dr) * 0.6 and lc[int(round(c - T))] < 95 and lc[int(round(c + T))] < 95: T += 1
    El, Er = c - L, R - c
    n = int(frac * (last + 1))
    # skin in the source row: an open collar (neck / chest) inside the lapels, or a hand outside them
    rgb0 = src[:, :3]
    mx, mn = rgb0.max(1), rgb0.min(1)
    skin = (src[:, 3] > 128) & (rgb0[:, 0] > 140) & (rgb0[:, 0] > rgb0[:, 1] + 18) & (rgb0[:, 1] > rgb0[:, 2] + 6) & ((mx - mn) / np.maximum(mx, 1) > 0.18)
    light = (src[:, 3] > 128) & (mn > 175) & ((mx - mn) < 40)
    shirt = np.median(rgb0[light], axis=0) if light.sum() > 6 else None
    jacket = (jl + jr) / 2
    top = shirt if shirt is not None else np.clip(jacket * 1.35 + 6, 0, 255)      # no shirt (Coleen): a dark top under the blazer
    sk = np.nonzero(skin & (np.abs(xs_ := np.arange(W) - c) < max(Dl, Dr)))[0]
    S0 = float(np.abs(sk - c).max()) if len(sk) else 0.0                            # half-width of the open collar at the cut
    ext = np.zeros((n, W, 4), np.float32)
    xs = np.arange(W, dtype=np.float32)
    for r in range(n):
        u = r / max(1, n - 1)
        p = narrow * (u * u * (3 - 2 * u))
        q = flare * u
        out = np.full(W, -1.0, np.float32)
        for side, D, Ed in ((-1, Dl, El), (1, Dr, Er)):
            d = (xs - c) * side                                      # distance from the centre on this side
            m = d >= 0
            Din = T + (D - T) * (1 - p)                              # the lapel's new distance
            Eo = Ed * (1 + q)
            s = np.where(d <= T, d,
                np.where(d <= Din, T + (d - T) * (D - T) / max(1e-3, Din - T),
                np.where(d <= Eo, D + (d - Din) * (Ed - D) / max(1e-3, Eo - Din), -1)))
            out = np.where(m & (s >= 0), c + side * s, out)
        valid = out >= 0
        sx = np.clip(out, 0, W - 1)
        x0 = np.floor(sx).astype(int); x1 = np.minimum(W - 1, x0 + 1); fx = (sx - x0)[:, None]
        row = src[x0] * (1 - fx) + src[x1] * fx
        row[~valid] = 0
        # skin in the new rows: inside the lapels the open collar closes to a point over the first 18 %; anything else is shirt / top;
        # skin outside the lapels (a hand at the chin) becomes jacket sleeve
        rs = row[:, :3]; rmx, rmn = rs.max(1), rs.min(1)
        rskin = valid & (rs[:, 0] > 140) & (rs[:, 0] > rs[:, 1] + 18) & (rs[:, 1] > rs[:, 2] + 6) & ((rmx - rmn) / np.maximum(rmx, 1) > 0.18)
        dist = np.abs(xs - c)
        Sv = S0 * max(0.0, 1 - u / 0.18)
        inside = dist < (T + (max(Dl, Dr) - T) * (1 - p))
        row[rskin & inside & (dist >= Sv), :3] = top
        row[rskin & ~inside, :3] = jacket
        # outside the lapels there is only jacket and its outline: anything else (a hand, a stray highlight) becomes sleeve
        Dmax = T + (max(Dl, Dr) - T) * (1 - p) + 12
        far = valid & (dist > Dmax)
        rl = rs[:, 0] * 0.3 + rs[:, 1] * 0.59 + rs[:, 2] * 0.11
        off = far & (np.abs(rs - jacket[None, :]).max(1) > 45) & (rl > 60)
        row[off, :3] = jacket
        if Sv > 2:                                                       # a soft fold line along the closing collar
            edge = rskin & inside & (np.abs(dist - Sv) < 3)
            row[edge, :3] = top * 0.78
        shade = 1.0 - 0.10 * u
        row[:, :3] *= shade
        ext[r] = row
    ext[..., 3] = np.where(ext[..., 3] > 128, 255, ext[..., 3])
    out = np.concatenate([im[:last - 1], ext, np.zeros((H - last - 1, W, 4), np.float32)], 0)
    # carry the outer outline down the new edges (the source row's edge pixels already hold it; make sure it is not antialiased away)
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(P + name + "_x.png")
    return out.shape[1], out.shape[0]


def main(pats):
    meta = json.load(open(P + "meta.json"))
    todo = [n for n in list(meta) if (("_b_" in n) or ("_e_" in n)) and not n.endswith("_x") and not n.endswith("back")
            and (not pats or any(p in n for p in pats))]
    for n in todo:
        w, h = extend(n)
        m = dict(meta[n]); m["size"] = [w, h]; meta[n + "_x"] = m
    json.dump(meta, open(P + "meta.json", "w"), indent=1)
    # the cached anchors of the extended parts are stale now
    try:
        an = json.load(open("build/anchors.json"))
        an = {k: v for k, v in an.items() if not k.endswith("_x")}
        json.dump(an, open("build/anchors.json", "w"))
    except FileNotFoundError:
        pass
    print(len(todo), "busts extended")


if __name__ == "__main__":
    main(sys.argv[1:])
