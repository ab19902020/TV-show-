"""The cast: which drawings each character uses, and where things are on each drawing (native sheet pixels).

eyes   - the two eye boxes (x, y, w, h), found by face.py's white-blob search on the native drawing (checked by eye)
mouth  - centre of the drawn closed mouth and its width (measured on 10x crops)
hand   - where a held prop sits (the palm / pinch point), for the props parented to hands
"""
import os, numpy as np, cv2
from functools import lru_cache
from PIL import Image
import face

UP = "build/up"
ART = "src/art"

POSES = {
    "David_Brent": {
        "01_neutral": dict(eyes=[(142, 65, 18, 24), (168, 62, 15, 23)], mouth=((164.5, 104.5), 14)),
        "02_talking_gesture": dict(eyes=[(142, 66, 17, 23), (168, 62, 13, 23)], mouth=((165.5, 104.5), 14)),
        "03_shrug": dict(eyes=[(127, 64, 17, 23), (152, 60, 15, 23)], mouth=((151.5, 102.5), 14)),
        "06_arms_folded": dict(eyes=[(124, 62, 17, 22), (149, 57, 14, 23)], mouth=((148, 99), 14)),
        "07_hands_on_hips": dict(eyes=[(143, 69, 17, 23), (168, 66, 14, 22)], mouth=((165.5, 106.5), 14)),
        "08_wave": dict(eyes=[(144, 66, 17, 22), (170, 62, 14, 22)], mouth=((168, 103.5), 14)),
        "09_amused": dict(eyes=[(130, 67, 17, 23), (154, 61, 15, 21)], mouth=((156.5, 101), 15)),
        "11_awkward": dict(eyes=[(125, 68, 17, 22), (150, 64, 14, 21)], mouth=((150.5, 104), 13)),
        "12_lean_forward": dict(eyes=None, mouth=None),
        "13_seated_front": dict(eyes=[(126, 71, 17, 24), (153, 70, 17, 24)], mouth=((150, 110.5), 19)),
        "19_seated_folded_arms": dict(eyes=[(136, 63, 17, 23), (162, 60, 15, 22)], mouth=((158.5, 100), 15)),
        "14_seated_three_quarter": dict(eyes=[(132, 67, 18, 23), (157, 61, 13, 22)], mouth=((157, 103.5), 14)),
    },
    "Tim_Canterbury": {
        "13_seated_front": dict(eyes=[(139, 68, 20, 23), (167, 65, 16, 23)], mouth=((159, 106), 15)),
        "14_seated_three_quarter": dict(eyes=[(131, 67, 18, 24), (158, 63, 15, 23)], mouth=((152, 105.5), 15)),
        "19_seated_folded_arms": dict(eyes=[(134, 66, 20, 24), (163, 63, 16, 23)], mouth=((157, 105.5), 16)),
    },
    "Gareth_Keenan": {
        "13_seated_front": dict(eyes=[(135, 61, 17, 25), (158, 61, 17, 25)], mouth=((153.5, 106), 13)),
        "14_seated_three_quarter": dict(eyes=[(125, 56, 18, 25), (148, 56, 14, 24)], mouth=((142, 101.5), 12)),
        "16_typing": dict(eyes=[(115, 55, 18, 25), (138, 56, 13, 24)], mouth=((129, 100.5), 12)),
        "19_seated_folded_arms": dict(eyes=[(140, 58, 17, 25), (162, 58, 15, 24)], mouth=((157, 102.5), 11)),
    },
}


@lru_cache(maxsize=None)
def drawing(char, name, folder="Actions"):
    """4x RGBA drawing as (rgb uint8, alpha uint8)."""
    im = np.asarray(Image.open(f"{UP}/{char}/{folder}/{name}.png").convert("RGBA"))
    return np.ascontiguousarray(im[..., :3]), np.ascontiguousarray(im[..., 3])


@lru_cache(maxsize=None)
def rig(char, name):
    rgb, a = drawing(char, name)
    meta = POSES.get(char, {}).get(name, {})
    eyes = [face.Eye(rgb, a, b) for b in meta["eyes"]] if meta.get("eyes") else []
    mouth = None
    if meta.get("mouth"):
        skin = eyes[0].skin if eyes else np.array([245, 185, 135.])
        mouth = face.Mouth(rgb, a, meta["mouth"][0], meta["mouth"][1], skin)
    ys, xs = np.where(a > 128)
    bottom = ys.max()
    feet_x = xs[ys > bottom - 12].mean()
    eyes_mid = np.mean([e.c for e in eyes], 0) if eyes else np.array([xs.mean(), ys.min() + 0.3 * (bottom - ys.min())])
    return dict(eyes=eyes, mouth=mouth, feet=np.array([feet_x, bottom]), eyes_mid=eyes_mid,
                top=ys.min(), size=a.shape)


@lru_cache(maxsize=48)
def posed(char, name, key):
    """the drawing with its face set: key = (gaze L, gaze R, lid, vis, amt, smile, skew), all rounded"""
    rgb, a = drawing(char, name)
    r = rig(char, name)
    gaze, lid, vis, amt, smile, skew = key
    out = rgb.copy()
    for e in r["eyes"]:
        face.draw_eye(out, e, gaze=gaze, lid=lid)
    if r["mouth"] is not None:
        face.draw_mouth(out, r["mouth"], vis, amt=amt, smile=smile, skew=skew)
    return out, a
