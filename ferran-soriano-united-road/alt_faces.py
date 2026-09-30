"""Register the main sheet's two alternative faces (eyes shut, one brow raised) onto the master head (SIFT
similarity at half size). eyes.py takes the closed lids' skin tone from the eyes-shut face.

-> build/rig/alt_faces.json {name: 2x3 affine, face part px -> head px}"""
import json, numpy as np, cv2
from PIL import Image
from align_util import sift_similarity

def flat(im):
    a = im[..., 3:] / 255
    return np.clip(im[..., :3] * a + 128 * (1 - a), 0, 255).astype(np.uint8)

if __name__ == "__main__":
    head = flat(np.asarray(Image.open("build/rig/head.png")).astype(np.float32))
    h2 = cv2.resize(head, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    res = {}
    for name in ["face_shut", "face_brow"]:
        f = flat(np.asarray(Image.open(f"build/parts/{name}.png")).astype(np.float32))
        f2 = cv2.resize(f, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        M, nin, ng = sift_similarity(cv2.cvtColor(f2, cv2.COLOR_RGB2BGR), cv2.cvtColor(h2, cv2.COLOR_RGB2BGR),
                                     ratio=0.75, reproj=5)
        M = M.copy(); M[:, 2] *= 2
        res[name] = M.tolist()
        print(name, nin, "inliers")
    json.dump(res, open("build/rig/alt_faces.json", "w"), indent=1)
