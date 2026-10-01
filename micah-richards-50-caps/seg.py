"""Find every separate drawing on a character sheet (connected components of "not paper"), label them on a contact image.
  python3 seg.py SHEETNAME            -> prints the components, writes scratchpad/g/<sheet>_seg.jpg
Components: (id, x0, y0, x1, y1, area). Header bars, text labels and thin panel borders are dropped."""
import os as _os
_os.makedirs('build/review', exist_ok=True)
import sys, os, json, cv2, numpy as np
from scipy import ndimage

ART = "src/art/"
G = "build/review/"


def foreground(rgb, thr=38):
    f = rgb.astype(np.float32)
    paper = np.float32([244, 252, 252])
    dist = np.abs(f - paper).max(2)
    fg = dist > thr
    fg = ndimage.binary_opening(fg, iterations=1)
    return fg


def components(rgb, min_area=350):
    fg = foreground(rgb)
    # close small gaps in outlines before filling
    fgc = ndimage.binary_closing(fg, iterations=2)
    filled = ndimage.binary_fill_holes(fgc)
    lab, n = ndimage.label(filled)
    objs = ndimage.find_objects(lab)
    out = []
    for i, sl in enumerate(objs, 1):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        area = int((lab[sl] == i).sum())
        w, h = x1 - x0, y1 - y0
        if area < min_area: continue
        if w > 560 and h < 70: continue            # header bars
        if h <= 30 and w <= 260 and area < 4000 and (area / (w * h)) < 0.9: continue      # text labels
        out.append(dict(id=len(out), box=[x0, y0, x1, y1], area=area))
    return lab, out


def draw(rgb, comps, path):
    im = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR).copy()
    for c in comps:
        x0, y0, x1, y1 = c["box"]
        cv2.rectangle(im, (x0, y0), (x1, y1), (0, 0, 255), 1)
        cv2.putText(im, str(c["id"]), (x0 + 2, y0 + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2, cv2.LINE_AA)
    cv2.imwrite(path, im, [cv2.IMWRITE_JPEG_QUALITY, 85])


if __name__ == "__main__":
    name = sys.argv[1]
    rgb = cv2.cvtColor(cv2.imread(ART + name + ".png"), cv2.COLOR_BGR2RGB)
    lab, comps = components(rgb)
    draw(rgb, comps, G + name + "_seg.jpg")
    for c in comps: print(c["id"], c["box"], c["area"])
    json.dump(comps, open(G + name + "_seg.json", "w"))
