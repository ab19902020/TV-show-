import numpy as np
from PIL import Image
from scipy import ndimage
from pathlib import Path
L = Path("/home/user/ab19902020/animnationstuido-/library/characters")
a = np.asarray(Image.open("Rio_Wilcox_Cutout/source_character_sheet.png").convert("RGBA"))
B = {  # sheet px boxes
 ("rio-ferdinand", "bf-tray"): (0, 0, 262, 598), ("rio-ferdinand", "bf-tray-present"): (264, 0, 545, 598),
 ("rio-ferdinand", "bf-serve"): (530, 70, 802, 598), ("rio-ferdinand", "bf-rub1"): (770, 0, 1040, 598),
 ("rio-ferdinand", "bf-rub2"): (1030, 0, 1312, 598), ("rio-ferdinand", "bf-rub3"): (1290, 0, 1536, 598),
 ("rio-ferdinand", "bf-open"): (0, 598, 222, 1010), ("rio-ferdinand", "bf-point"): (212, 598, 362, 1010),
 ("rio-ferdinand", "bf-explain"): (360, 598, 513, 1010), ("rio-ferdinand", "bf-pockets"): (513, 598, 668, 1010),
 ("rio-ferdinand", "bf-think"): (678, 598, 818, 1010),
 ("jason-wilcox", "bf-smug"): (818, 650, 1007, 1010), ("jason-wilcox", "bf-bliss"): (1007, 650, 1180, 1010),
 ("jason-wilcox", "bf-eyesup"): (1180, 650, 1350, 1010), ("jason-wilcox", "bf-shrug"): (1345, 650, 1536, 1010),
}
al = a[..., 3] > 30
lab, n = ndimage.label(al)
for (cid, name), (x0, y0, x1, y1) in B.items():
    sub = lab[y0:y1, x0:x1]
    keep = np.zeros(sub.shape, bool)
    ids, counts = np.unique(sub[sub > 0], return_counts=True)
    big = ids[np.argmax(counts)]
    for i, c in zip(ids, counts):
        tot = (lab == i).sum()
        if (c / tot > 0.5 and c > 40) or i == big:
            keep |= sub == i
    crop = a[y0:y1, x0:x1].copy()
    crop[..., 3] = np.where(keep, crop[..., 3], 0)
    ys, xs = np.nonzero(crop[..., 3] > 10)
    crop = crop[max(0, ys.min() - 4):ys.max() + 5, max(0, xs.min() - 4):xs.max() + 5]
    out = L / cid / "reference" / "beg-friend"
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(crop).save(out / f"{name[3:]}.png")
    print(cid, name, crop.shape[1], crop.shape[0])
