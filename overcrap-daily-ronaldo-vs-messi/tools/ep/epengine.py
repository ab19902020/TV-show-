"""Episode engine: rigs, lip sync, timeline and the 4K compositor for the
bitmap cut-out studio (Mark Goldbridge, Wayne Rooney, Roy Keane, Rio Ferdinand).
Ported from Pass Mic's Episode 1 engine (Mark, Gary, Roy) and extended to
four characters.

Coordinates: every background has a "1x" space (the supplied 1672x941 art);
its AI-upscaled 4x copy and foreground matte are what gets rendered.
A camera is (background, x0, y0, width) in 1x space, 16:9; frames come out at
OUT (3840x2160). Characters are anchored by their face (face centre + face
width in 1x space) or by their feet, so any drawing of a character can be
swapped in at the same place and size.
"""
import bisect, json, math, os, re, subprocess, sys
from functools import lru_cache
import cv2, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EP = os.path.join(ROOT, 'episode')
sys.path.insert(0, HERE)
import face_rig as F   # noqa: E402

FPS = 24
OUT = (3840, 2160)
K = 4                      # background upscale factor
SR = 44100
MOUTH_KEYS = ['rest', 'a', 'e', 'i', 'o', 'u', 'smile', 'frown', 'wide_shout']
CHARS = ('mark', 'rooney', 'roy', 'rio')
OPEN_SCALE = 0.88          # open mouths a touch smaller than the sheet's: the show's delivery is played straight


def _nbytes(v):
    if isinstance(v, np.ndarray):
        return v.nbytes
    if isinstance(v, tuple):
        return sum(_nbytes(x) for x in v)
    return 64


def trim(cache, budget, keep=lambda k: False):
    """Drop the oldest entries of a dict cache until its arrays fit in `budget` bytes."""
    total = sum(_nbytes(v) for v in cache.values())
    for k in list(cache):
        if total <= budget:
            break
        if not keep(k):
            total -= _nbytes(cache.pop(k))


# ------------------------------------------------------------------ backgrounds
class Background:
    def __init__(self, name):
        self.name = name
        self.cfg = json.load(open(os.path.join(EP, 'backgrounds', name + '.json')))
        self._img = self._fg = None
        self.cache = {}

    def img(self):
        if self._img is None:
            self._img = cv2.imread(os.path.join(EP, 'x4', self.cfg['image']))
            fg = os.path.join(ROOT, 'out', 'bg', self.name + '_fg.png')
            if not os.path.exists(fg):             # the desk matte is built from backgrounds/<name>.json
                import bgmatte
                bgmatte.build(self.name)
            self._fg = cv2.imread(fg, cv2.IMREAD_UNCHANGED)
        return self._img, self._fg

    def view(self, rect, dof=0.0):
        """(bg BGR, fg RGBA) at output size for a camera rect in 1x coords."""
        key = (tuple(round(v, 2) for v in rect), round(dof, 2))
        if key in self.cache:
            return self.cache[key]
        img, fg = self.img()
        x0, y0, w = rect
        h = w * OUT[1] / OUT[0]
        k = OUT[0] / (w * K)
        M = np.float32([[k, 0, -x0 * K * k], [0, k, -y0 * K * k]])
        interp = cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC
        bg = cv2.warpAffine(img, M, OUT, flags=interp, borderMode=cv2.BORDER_REPLICATE)
        fgv = cv2.warpAffine(fg, M, OUT, flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if dof > 0:
            bg = cv2.GaussianBlur(bg, (0, 0), dof)
        if len(self.cache) > 2:
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = (bg, fgv)
        return bg, fgv


# ------------------------------------------------------------------ rigs
class Rig:
    """All drawings of one character, with face info, mouth swaps and blinks."""

    def __init__(self, name):
        self.name = name
        self.idx = json.load(open(os.path.join(EP, 'characters', name, 'index.json')))
        p = os.path.join(EP, 'characters', name, 'rig.json')
        self.over = json.load(open(p)) if os.path.exists(p) else {}
        self.info = {}
        self.imgs = {}
        self.parts = None
        self.cache = {}

    # -- drawings
    def image(self, key):
        if key not in self.imgs:
            panel, name = key.split('/')
            hi = os.path.join(EP, 'characters_x16', self.name, panel, name + '.png')
            path = hi if os.path.exists(hi) else os.path.join(EP, self.idx[panel][name]['file'])
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            for fix in self.over.get('_eye_fix', {}).get(key, []):
                img = fix_eye(img, fix)
            self.imgs[key] = img
        return self.imgs[key]

    def face(self, key):
        """Face info for a drawing: centre, width, mouth box, eyes."""
        if key in self.info:
            return self.info[key]
        img = self.image(key)
        H, W = img.shape[:2]
        panel = key.split('/')[0]
        ov = self.over.get(key, {})
        hf = ov.get('head_frac', {'upper': 0.6, 'body': 0.35, 'turnaround': 0.35, 'closeup': 0.6}.get(panel, 1.0))
        info = F.find_face(img, head_frac=hf)
        if info is None:
            info = dict(box=(0, 0, W, H), eyes=[], mouth=None, mouth_mask=np.zeros((H, W), bool),
                        face=np.zeros((H, W), bool), skin=np.array([75, 15, 25], np.float32))
        if 'mouth' in ov:        # [cx, cy, w(, h)] as fractions of the drawing size
            cx, cy, mw = ov['mouth'][:3]
            mh = ov['mouth'][3] * H if len(ov['mouth']) > 3 else mw * W * 0.3
            info['mouth'] = (cx * W, cy * H, mw * W, mh)
            m = np.zeros((H, W), np.uint8)
            cv2.ellipse(m, (int(cx * W), int(cy * H)), (int(mw * W * 0.55), int(max(mh * 0.55, mw * W * 0.2))), 0, 0, 360, 1, -1)
            info['mouth_mask'] = m > 0
        if ov.get('auto_mouth') and len(info['eyes']) == 2:
            # detection misses (a hand or prop over the chin): place the mouth from the eyes
            fwid = info['box'][2] - info['box'][0]
            (ex0, ey0), (ex1, ey1) = info['eyes'][0][:2], info['eyes'][1][:2]
            mw = fwid * 0.22
            mx, my = (ex0 + ex1) / 2 + (ex1 - ex0) * 0.1, (ey0 + ey1) / 2 + 0.46 * fwid
            info['mouth'] = (mx, my, mw, mw * 0.3)
            m = np.zeros((H, W), np.uint8)
            cv2.ellipse(m, (int(mx), int(my)), (int(mw * 0.55), int(mw * 0.2)), 0, 0, 360, 1, -1)
            info['mouth_mask'] = m > 0
        if 'lips' in ov:
            # located by hand: the drawn mouth's box, and the nose line nothing may cross
            lx0, lx1, ly0, ly1 = ov['lips']
            nose = ov.get('nose', ly0 - 0.01)
            pts = [(0.0, nose), (1.0, nose)] if not isinstance(nose, list) else \
                [(0.0, nose[0][1])] + [tuple(p) for p in nose] + [(1.0, nose[-1][1])]
            guard = np.interp(np.arange(W) / W, [p[0] for p in pts], [p[1] for p in pts]) * H
            bx = (lx0 * W, lx1 * W, ly0 * H, ly1 * H)
            info['lips_box'] = bx
            info['mouth'] = ((bx[0] + bx[1]) / 2, (bx[2] + bx[3]) / 2, bx[1] - bx[0], bx[3] - bx[2])
            info['mouth_mask'] = F.mouth_marks(img, info, bx)
            feather = max(2.0, 0.003 * H)
            info['allow'] = np.clip((np.arange(H)[:, None] - guard[None, :]) / feather, 0, 1).astype(np.float32)
            info['_interior'] = None
        if ov.get('no_mouth'):
            info['mouth'] = None
        fx0, fy0, fx1, fy1 = info['box']
        if info['eyes'] and len(info['eyes']) == 2:
            cx = (info['eyes'][0][0] + info['eyes'][1][0]) / 2
            cy = (info['eyes'][0][1] + info['eyes'][1][1]) / 2
        else:
            cx, cy = (fx0 + fx1) / 2, fy0 + (fy1 - fy0) * 0.45
        info['center'] = (float(cx), float(cy))
        info['width'] = float(ov.get('face_w', 1.0) * (fx1 - fx0))
        if self.over.get('_anchor_mouth') and info['mouth'] is not None:
            # Roy: his eyes are often narrowed or looking down; anchor every drawing on his mouth,
            # and size it by the head's width ear to ear at eye level (skin boxes vary with the beard)
            mx, my = info['mouth'][:2]
            ey = int(my - 0.425 * info['width'])
            row = img[max(0, ey), :, 3] > 100
            x0 = x1 = int(min(max(mx, 0), W - 1))
            while x0 > 0 and row[x0 - 1]:
                x0 -= 1
            while x1 < W - 1 and row[x1 + 1]:
                x1 += 1
            if x1 - x0 > 0.5 * info['width']:
                info['width'] = float(x1 - x0) * ov.get('face_w', 1.0)
            info['center'] = (float(mx), float(my - 0.425 * info['width']))
        ys, xs = np.nonzero(img[..., 3] > 128)
        yb = ys.max()
        low = xs[ys >= yb - max(4, int(H * 0.01))]
        info['feet'] = (float((low.min() + low.max()) / 2), float(yb))
        info['size'] = (W, H)
        ref = self.over.get('_height_ref')
        if ref and key != ref and key.split('/')[0] in self.over.get('_height_panels', ['body']):
            # walk drawings: the profile face is too small to measure, so the drawing is sized by
            # its height (top of head to feet) against the reference standing drawing
            r = self.face(ref)
            rys = np.nonzero(self.image(ref)[..., 3] > 128)[0]
            rtop, rh = rys.min(), r['feet'][1] - rys.min()
            top = ys.min()
            fig = yb - top
            info['width'] = float(r['width'] * fig / rh)
            ey = top + (r['center'][1] - rtop) * fig / rh
            band = xs[(ys >= top) & (ys <= ey)]
            info['center'] = (float(np.median(band)), float(ey))
        self.info[key] = info
        return info

    # -- mouths
    def mouth_parts(self):
        if self.parts is None:
            self.parts = {}
            for k in MOUTH_KEYS:
                if k in self.idx.get('mouths', {}):
                    hi = os.path.join(EP, 'characters_x16', self.name, 'mouths', k + '.png')
                    path = hi if os.path.exists(hi) else os.path.join(EP, self.idx['mouths'][k]['file'])
                    self.parts[k] = F.mouth_part(cv2.imread(path, cv2.IMREAD_UNCHANGED))
        return self.parts

    def patch_part(self, key):
        """A mouth cell of the sheet (RGB), for patch-style lip sync."""
        if self.parts is None:
            self.parts = {}
        if key not in self.parts:
            if key not in self.idx.get('mouths', {}):
                return None
            hi = os.path.join(EP, 'characters_x16', self.name, 'mouths', key + '.png')
            path = hi if os.path.exists(hi) else os.path.join(EP, self.idx['mouths'][key]['file'])
            self.parts[key] = cv2.imread(path, cv2.IMREAD_UNCHANGED)[..., :3]
        return self.parts[key]

    def erased(self, key):
        """The drawing with its own mouth painted out (cached), for the open mouths to go on."""
        ck = ('erased', key)
        if ck not in self.cache:
            img, info = self.image(key), self.face(key)
            ov = self.over.get(key, {})
            if 'erase' in ov:
                W, H = info['size']
                bx = [ov['erase'][0] * W, ov['erase'][1] * W, ov['erase'][2] * H, ov['erase'][3] * H]
            else:
                cx, cy, mw, _ = info['mouth']
                e = self.over.get('_erase_box', [0.75, 0.75, 0.3, 0.4])       # left, right, up, down in mouth widths
                bx = [cx - e[0] * mw, cx + e[1] * mw, cy - e[2] * mw, cy + e[3] * mw]
            if self.over.get('_erase_mode') == 'lipline':
                self.cache[ck] = erase_lip_line(img, info, bx)
            elif self.over.get('_erase_mode') == 'flat':
                self.cache[ck] = flatten_lips(img, info, bx)
            elif self.over.get('_erase_mode') == 'none':
                self.cache[ck] = img
            else:
                self.cache[ck] = erase_marks(img, info, bx)
        return self.cache[ck]

    def mouth_ratio(self):
        """Closed-mouth width / face width, from the front head close-up."""
        r = self.over.get('_mouth_ratio')
        if r:
            return r
        try:
            info = self.face('head/front')
            return max(0.2, min(0.4, info['mouth'][2] / info['width']))
        except Exception:
            return 0.3

    def drawing(self, key, mouth=None, blink=0.0, flip=False):
        """RGBA of a drawing with the given mouth (None = as drawn) and eyelids."""
        if mouth == 'shout':
            # a shouted vowel: drawings with a big open shout of their own show it as drawn,
            # the others take the open 'a'
            mouth = None if key in self.over.get('_shout_drawn', []) else 'a'
        ck = (key, mouth, round(blink, 1), flip)
        if ck in self.cache:
            return self.cache[ck]
        img = self.image(key)
        info = self.face(key)
        out = img
        if mouth is not None and info['mouth'] is not None:
            base = self.cache.get(('nomouth', key))
            if base is None and self.over.get('_mouth_style') != 'patch':
                base = F.erase_mouth(img, info) if 'lips_box' in info else F.without_mouth(img, info)
                self.cache[('nomouth', key)] = base
            if self.over.get('_mouth_style') == 'drawn':
                m = self.over.get('_alias', {}).get(mouth, mouth)
                shape = self.over.get('_shapes', {}).get(m) or DRAWN_SHAPES.get(m)
                ov = self.over.get(key, {})
                size = self.over.get('_mouth_size', 1.0) * ov.get('size', 1.0)
                if shape is not None:
                    out = drawn_mouth(self.erased(key), info, shape, ov.get('squash', 1.0), ov.get('tilt', 0.0), size)
                else:
                    # closed sounds inside a line: the same base with closed lips, so the lips
                    # don't flicker between the drawn ones and the open mouth
                    out = closed_mouth(self.erased(key), info, ov.get('squash', 1.0), ov.get('tilt', 0.0), size)
            elif self.over.get('_mouth_style') == 'patch':
                inner = self.over.get('_inner')
                if inner is not None:
                    mouth = self.over.get('_alias', {}).get(mouth, mouth)
                part = self.patch_part(mouth)
                if self.over.get('_erase'):
                    img = self.erased(key)
                if inner is not None:
                    # only the open mouth from the sheet (teeth, tongue, lips) over the drawing's own
                    # beard; closed shapes show the mouth as drawn
                    out = img if (part is None or mouth not in inner) else inner_mouth(
                        img, info, part, inner[mouth], self.over.get(key, {}).get('squash', 1.0),
                        self.over.get('_patch_lips', PATCH_LIPS), self.over.get('_patch_cy', 0.49))
                else:
                    out = img if part is None else patch_mouth(img, info, part, self.over.get(key, {}).get('squash', 1.0),
                                                               self.over.get('_patch_lips', PATCH_LIPS),
                                                               self.over.get('_patch_cy', 0.49),
                                                               self.over.get('_patch_oval', 0.6))
            else:
                parts = self.mouth_parts()
                part = parts.get(mouth) or parts.get('rest')
                rest_w = parts['rest'][2]
                ov = self.over.get(key, {})
                rest_px = ov['mw'] * info['size'][0] if 'mw' in ov else self.mouth_ratio() * info['width']
                width = rest_px * part[2] / rest_w
                if mouth != 'rest':
                    width *= self.over.get('_open_scale', OPEN_SCALE)
                part = recolor_part(part, info['skin'])
                sq = ov.get('squash', 1.0)
                dy = 0.0
                if 'lips_box' in info:
                    # every mouth hangs from the drawn upper lip: an open one drops the jaw, never
                    # reaches up into the nose
                    s = width / max(part[2], 1e-6)
                    top = info['lips_box'][2] + ov.get('lip_dy', 0.0) * info['size'][1]
                    if mouth != 'rest' and 'nose' in ov:
                        # an open mouth never starts right under the nose: it would read as covering it
                        nose = ov['nose']
                        ny = (max(p[1] for p in nose) if isinstance(nose, list) else nose) * info['size'][1]
                        top = max(top, ny + self.over.get('_nose_gap', 0.0) * info['width'])
                    dy = top + part[3] * s / 2 - info['mouth'][1]
                out = F.with_mouth(base, info, part, width, dy=dy, squash_x=sq, angle=ov.get('tilt', 0.0))
        if blink > 0 and len(info['eyes']) == 2 and not self.over.get('_no_blink'):
            out = F.blink(out, info, blink)             # never one eye only: that reads as a wink / cross-eyed
        if flip:
            out = out[:, ::-1].copy()
        self.cache[ck] = out
        trim(self.cache, 150e6, keep=lambda k: k[0] in ('nomouth', 'erased'))
        return out


def erase_marks(img, info, box):
    """Paint out a drawing's own mouth before a new one goes on (a bearded or grinning drawing
    would otherwise show its drawn mouth beside the new one): inside `box` (pixels x0, x1, y0, y1)
    the thin dark lines, the lips and the teeth are found and inpainted from the skin and beard
    around them. Thick dark shapes (a moustache, a goatee) are not thin lines and stay."""
    H, W = img.shape[:2]
    x0, x1, y0, y1 = [int(round(v)) for v in box]
    fw = info['width']
    m = int(0.08 * fw) + 4
    X0, X1, Y0, Y1 = max(0, x0 - m), min(W, x1 + m), max(0, y0 - m), min(H, y1 + m)
    crop = np.ascontiguousarray(img[Y0:Y1, X0:X1, :3])
    L = cv2.cvtColor(crop.astype(np.float32) / 255, cv2.COLOR_BGR2LAB)
    k = max(3, int(0.05 * fw)) | 1
    bh = cv2.morphologyEx(L[..., 0], cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    thin = bh > 9                                           # dark lines thinner than k
    lips = (L[..., 1] > 22) & (L[..., 0] < 75)              # red lips, tongue, gums
    teeth = (L[..., 0] > 78) & (L[..., 2] < 26) & (L[..., 1] < 12)   # white or cream teeth
    inner = (L[..., 0] < 32)                                 # the dark inside of a drawn open mouth
    inside = np.zeros(thin.shape, bool)
    inside[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
    mask = (thin | lips | teeth | inner) & inside & (img[Y0:Y1, X0:X1, 3] > 200)
    d = max(2, int(0.012 * fw))
    mask = cv2.dilate(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * d + 1, 2 * d + 1)))
    mask &= inside.astype(np.uint8)
    if not mask.any():
        return img
    fill = cv2.inpaint(crop, mask * 255, max(3, int(0.02 * fw)), cv2.INPAINT_TELEA)
    out = img.copy()
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), max(1.0, 0.004 * fw))
    soft = np.maximum(soft, mask.astype(np.float32))[..., None]
    out[Y0:Y1, X0:X1, :3] = (crop * (1 - soft) + fill * soft).astype(np.uint8)
    return out


def flatten_lips(img, info, box):
    """Roy: his drawn lips (the salmon shapes and the line between them, inside `box`) take the
    flat grey of the beard around them, so a drawn opening doesn't sit beside a second, closed
    mouth. Flat, not blurred: it keeps the drawing's flat-colour look."""
    H, W = img.shape[:2]
    x0, x1, y0, y1 = [int(round(v)) for v in box]
    crop = np.ascontiguousarray(img[y0:y1, x0:x1, :3])
    L = cv2.cvtColor(crop.astype(np.float32) / 255, cv2.COLOR_BGR2LAB)
    chroma = np.hypot(L[..., 1], L[..., 2])
    warm = (chroma > 16) & (L[..., 0] > 30)                 # lips / skin showing between the hairs
    fw = info['width']
    k = max(3, int(0.04 * fw)) | 1
    bh = cv2.morphologyEx(L[..., 0], cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    mask = (warm | (bh > 10)) & (img[y0:y1, x0:x1, 3] > 200)
    beard = ~mask & (chroma < 14)
    if beard.sum() < 20 or not mask.any():
        return img
    grey = np.median(crop[beard], axis=0)
    # an elliptical box, so the change has no straight edges
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0].astype(np.float32)
    ell = ((xx - (x1 - x0) / 2) / ((x1 - x0) / 2)) ** 2 + ((yy - (y1 - y0) / 2) / ((y1 - y0) / 2)) ** 2 <= 1
    m = cv2.dilate((mask & ell).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 1.0)[..., None]
    out = img.copy()
    out[y0:y1, x0:x1, :3] = (crop * (1 - m) + grey * m).astype(np.uint8)
    return out


def erase_lip_line(img, info, box):
    """Rio: take out only the thin drawn lip line (and the lips' darker shading) inside `box`,
    filling it with the lip-band skin around it. The moustache and the goatee are thick, so
    they are left exactly as drawn."""
    x0, x1, y0, y1 = [int(round(v)) for v in box]
    crop = np.ascontiguousarray(img[y0:y1, x0:x1, :3])
    L = cv2.cvtColor(crop.astype(np.float32) / 255, cv2.COLOR_BGR2LAB)
    fw = info['width']
    k = max(5, int(0.035 * fw)) | 1
    bh = cv2.morphologyEx(L[..., 0], cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    skin = (np.hypot(L[..., 1], L[..., 2]) > 25) & (L[..., 0] > 45)
    near_skin = cv2.blur(skin.astype(np.float32), (k * 2 + 1, k * 2 + 1)) > 0.35
    shade = (np.hypot(L[..., 1], L[..., 2]) > 20) & (L[..., 0] > 25) & (L[..., 0] < np.median(L[..., 0][skin]) - 8) \
        if skin.sum() > 20 else np.zeros_like(skin)
    mask = ((bh > 8) | shade) & near_skin & (img[y0:y1, x0:x1, 3] > 200)
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0].astype(np.float32)
    ell = ((xx - (x1 - x0) / 2) / ((x1 - x0) / 2)) ** 2 + ((yy - (y1 - y0) / 2) / ((y1 - y0) / 2)) ** 2 <= 1
    mask &= ell
    if not mask.any() or skin.sum() < 20:
        return img
    m = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & (skin | mask)
    # fill from the skin right around it (normalised blur of the skin only)
    w = (skin & ~m).astype(np.float32)
    sig = max(2.0, 0.02 * fw)
    num = cv2.GaussianBlur(crop.astype(np.float32) * w[..., None], (0, 0), sig)
    den = cv2.GaussianBlur(w, (0, 0), sig)[..., None]
    fill = num / np.maximum(den, 1e-4)
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.8)
    a = np.maximum(a, m)[..., None]
    out = img.copy()
    out[y0:y1, x0:x1, :3] = (crop * (1 - a) + fill * a).clip(0, 255).astype(np.uint8)
    return out


def fix_eye(img, fix):
    """Repaint an eye whose pupil looks the wrong way on the sheet (Roy's arms-crossed drawing
    has one pupil jammed in the inner corner, which reads as cross-eyed): the eye's opening
    (a polygon) is filled with the eye white, a new iris drawn where it should look, and the
    upper lid line drawn back over the top. Coordinates are fractions of the drawing size."""
    H, W = img.shape[:2]
    out = img.copy()
    S = 4                                            # supersampled for clean anti-aliased edges
    poly = np.round(np.array(fix['poly']) * [W, H] * S).astype(np.int32)
    x0, y0 = poly.min(0) // S - 30
    x1, y1 = poly.max(0) // S + 30
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    h, w = y1 - y0, x1 - x0
    off = np.array([x0, y0]) * S

    def layer(draw):
        m = np.zeros((h * S, w * S), np.uint8)
        draw(m)
        return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255

    opening = layer(lambda m: cv2.fillPoly(m, [poly - off], 255, cv2.LINE_AA))
    icx, icy, irx, iry = fix['iris']
    iris = layer(lambda m: cv2.ellipse(m, (int((icx * W - x0) * S), int((icy * H - y0) * S)),
                                       (int(irx * W * S), int(iry * H * S)), 0, 0, 360, 255, -1, cv2.LINE_AA))
    iris *= opening
    lid_pts = np.round(np.array(fix['lid']) * [W, H] * S).astype(np.int32) - off
    lid = layer(lambda m: cv2.polylines(m, [lid_pts], False, 255, int(fix['lid_w'] * W * S), cv2.LINE_AA))
    reg = out[y0:y1, x0:x1, :3].astype(np.float32)
    white = np.array(fix.get('white', [246, 246, 250]), np.float32)
    dark = np.array(fix.get('dark', [18, 16, 20]), np.float32)
    reg = reg * (1 - opening[..., None]) + white * opening[..., None]
    reg = reg * (1 - iris[..., None]) + dark * iris[..., None]
    reg = reg * (1 - lid[..., None]) + dark * lid[..., None]
    out[y0:y1, x0:x1, :3] = reg.clip(0, 255).astype(np.uint8)
    return out


@lru_cache(maxsize=64)
def _skin_of_part(pid):
    return None


def recolor_part(part, skin_lab):
    """Shift a mouth part's skin tone to the target face's skin."""
    patch, c, w = part[:3]
    key = (id(patch), tuple(np.round(skin_lab, 1)))
    hit = _RECOLOR.get(key)
    if hit is not None:
        return hit
    L = cv2.cvtColor(patch[..., :3].astype(np.float32) / 255, cv2.COLOR_BGR2LAB)
    ps = F.skin_colour(patch)
    if ps is None:
        return part
    d = np.array(skin_lab, np.float32) - ps
    near = np.linalg.norm(L - ps, axis=2) < 18
    wgt = near.astype(np.float32)[..., None]
    L2 = L + d * wgt
    bgr = (cv2.cvtColor(L2, cv2.COLOR_LAB2BGR) * 255).clip(0, 255).astype(np.uint8)
    out = (np.dstack([bgr, patch[..., 3]]), c, w) + tuple(part[3:])
    _RECOLOR[key] = out
    return out


_RECOLOR = {}

PATCH_LIPS = 0.72          # closed-lip width as a fraction of a mouth cell's width (all cells share one zoom)


def patch_mouth(img, info, cell, squash=1.0, lips=PATCH_LIPS, cell_cy=0.49, oval_cy=0.6):
    """Roy's lip sync: a mouth cell from his sheet - lips, moustache and beard -
    scaled to his mouth, colour-matched to the drawing under it and blended in
    with a soft oval edge. The cell's lip line lands on his drawn lip line."""
    cx, cy, mw, _ = info['mouth']
    ch, cw = cell.shape[:2]
    s = mw / lips / cw
    sx = s * squash
    patch = cv2.resize(cell, (max(2, int(cw * sx)), max(2, int(ch * s))),
                       interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC).astype(np.float32)
    h, w = patch.shape[:2]
    x0, y0 = int(round(cx - 0.5 * w)), int(round(cy - cell_cy * h))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx / w - 0.5) / 0.47) ** 2 + ((yy / h - oval_cy) / 0.36) ** 2)
    alpha = np.clip((1.0 - d) / 0.3, 0, 1)
    # match the beard and skin tones of the drawing underneath (mean shift over the soft rim)
    H, W = img.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return img
    under = img[ya:yb, xa:xb, :3].astype(np.float32)
    pc = patch[ya - y0:yb - y0, xa - x0:xb - x0]
    ring = (alpha[ya - y0:yb - y0, xa - x0:xb - x0] > 0.05) & (alpha[ya - y0:yb - y0, xa - x0:xb - x0] < 0.6) & \
        (img[ya:yb, xa:xb, 3] > 200)
    if ring.sum() > 50:
        shift = under[ring].mean(axis=0) - pc[ring].mean(axis=0)
        patch = np.clip(patch + 0.7 * shift, 0, 255)
    rgba = np.dstack([patch, alpha * 255]).astype(np.uint8)
    out = img.copy()
    F.paste(out, rgba, x0, y0)
    return out


def inner_mouth(img, info, cell, shape, squash=1.0, lips=PATCH_LIPS, cell_cy=0.49):
    """Rio's lip sync: from a mouth cell of his sheet only the opening itself - the dark inside,
    teeth, tongue and its ink rim, inside an oval given in cell fractions (cx, cy, rx, ry[, dy,
    scale]) - is pasted onto his mouth, placed as patch_mouth places the whole cell. The cell's
    skin (lips) and moustache are left out, so his drawn moustache, lips and beard stay his own
    around a crisp opening. dy moves the opening down (cell fractions), scale shrinks it."""
    ox, oy, rx, ry = shape[:4]
    dy = shape[4] if len(shape) > 4 else 0.0
    sc = shape[5] if len(shape) > 5 else 1.0
    cx, cy, mw, _ = info['mouth']
    ch, cw = cell.shape[:2]
    s = mw / lips / cw * sc
    sx = s * squash
    rgb = cell[..., :3]
    L = cv2.cvtColor(rgb.astype(np.float32) / 255, cv2.COLOR_BGR2LAB)
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    d = np.sqrt(((xx / cw - ox) / rx) ** 2 + ((yy / ch - oy) / ry) ** 2)
    oval = np.clip((1.0 - d) / 0.07, 0, 1)
    # the cell's skin (its lips and chin) is not the opening: measured as the median of the
    # cell's light orange pixels
    sk = (L[..., 0] > 45) & (L[..., 1] > 12) & (L[..., 2] > 25)
    skin = np.median(L[sk], axis=0) if sk.sum() > 50 else np.array([65, 25, 45], np.float32)
    notskin = (np.linalg.norm(L - skin, axis=2) > 14).astype(np.uint8)
    k = max(3, int(cw * 0.006)) | 1
    notskin = cv2.morphologyEx(notskin, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    a = cv2.GaussianBlur(notskin.astype(np.float32), (0, 0), max(1.0, cw * 0.003)) * oval
    rgba = np.dstack([rgb, (a * 255).astype(np.uint8)])
    patch = cv2.resize(rgba, (max(2, int(cw * sx)), max(2, int(ch * s))),
                       interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    h, w = patch.shape[:2]
    x0 = int(round(cx - 0.5 * w))
    y0 = int(round(cy - (cell_cy - dy) * h / sc * sc - (1 - sc) * (cell_cy - oy) * h / sc * 0))
    out = img.copy()
    F.paste(out, patch, x0, y0)
    return out


# drawn mouth openings, sized by the drawing's closed-lip width:
# (width, height, top teeth, bottom teeth, tongue, roundness 0..1)
DRAWN_SHAPES = {
    'a': (0.78, 0.50, 0.30, 0.00, 0.55, 0.15),
    'e': (0.86, 0.32, 0.36, 0.16, 0.00, 0.05),
    'i': (0.74, 0.18, 0.50, 0.40, 0.00, 0.00),
    'o': (0.46, 0.46, 0.22, 0.00, 0.45, 0.90),
    'u': (0.34, 0.32, 0.00, 0.00, 0.50, 1.00),
    'fv': (0.66, 0.15, 0.85, 0.00, 0.00, 0.00),
    'cdg': (0.70, 0.22, 0.45, 0.30, 0.00, 0.05),
    'l': (0.66, 0.24, 0.35, 0.00, 0.50, 0.10),
    'r': (0.42, 0.30, 0.25, 0.00, 0.30, 0.80),
    'th': (0.70, 0.17, 0.55, 0.30, 0.00, 0.00),
}


def drawn_mouth(img, info, shape, squash=1.0, tilt=0.0, size=1.0, ink=(22, 16, 18)):
    """A mouth opening drawn in the flat cartoon style of the drawings themselves - a dark
    inside with teeth and a tongue, inside an ink outline - over the drawing's own closed
    mouth, so a bearded face keeps its own moustache and beard and only the opening moves.
    The top edge stays at the drawn upper lip; the opening drops down from it."""
    cx, cy, mw, _ = info['mouth']
    w0, h0, tt, bt, tg, rnd = shape
    w, h = w0 * mw * size * squash, h0 * mw * size
    S = 4                                                   # supersampled, then reduced: smooth edges
    pad = int(0.12 * mw) + 4
    PW, PH = int(w + 2 * pad), int(h + 2 * pad)
    ox, oy = cx - PW / 2, cy - 0.10 * h - pad              # hangs from just above the lip line
    N = 48
    ts = np.linspace(0, 1, N)
    xs = (ts - 0.5) * w
    # top edge: a shallow arch; bottom: a deep curve (an oval for O/U)
    top = -0.06 * h * np.sin(np.pi * ts) + 0.05 * h * np.sin(np.pi * ts) ** 8
    bot = h * (np.sin(np.pi * ts) ** (0.55 + 0.45 * (1 - rnd)))
    slot = np.concatenate([np.stack([xs, top], 1), np.stack([xs[::-1], bot[::-1]], 1)])
    if rnd > 0:
        a = np.linspace(-np.pi, np.pi, len(slot))
        oval = np.stack([np.cos(a) * w / 2, h / 2 + np.sin(a) * h / 2], 1)
        # match the slot's point order: along the top left to right, back along the bottom
        oval = np.concatenate([np.stack([xs, h / 2 - np.sqrt(np.clip(1 - (2 * xs / w) ** 2, 0, 1)) * h / 2], 1),
                               np.stack([xs[::-1], h / 2 + np.sqrt(np.clip(1 - (2 * xs[::-1] / w) ** 2, 0, 1)) * h / 2], 1)])
        pts = slot * (1 - rnd) + oval * rnd
    else:
        pts = slot
    th = math.radians(tilt)
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    pts = pts @ R.T + [PW / 2, pad + 0.10 * h]

    def mask(draw):
        m = np.zeros((PH * S, PW * S), np.uint8)
        draw(m)
        return cv2.resize(m, (PW, PH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255

    P = np.round(pts * S).astype(np.int32)
    inside = mask(lambda m: cv2.fillPoly(m, [P], 255, cv2.LINE_AA))
    lw = max(2, int(0.045 * mw * size * S))
    outline = mask(lambda m: cv2.polylines(m, [P], True, 255, lw, cv2.LINE_AA))
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
    u = (xx - PW / 2) * math.cos(-th) - (yy - pad - 0.10 * h) * math.sin(-th)
    v = (xx - PW / 2) * math.sin(-th) + (yy - pad - 0.10 * h) * math.cos(-th)
    teeth = np.zeros_like(inside)
    if tt > 0:
        teeth = np.maximum(teeth, np.clip((tt * h - v) / 1.5, 0, 1))
    if bt > 0:
        teeth = np.maximum(teeth, np.clip((v - (1 - bt) * h * 0.92) / 1.5, 0, 1) * (np.abs(u) < 0.36 * w))
    teeth *= inside
    tongue = np.zeros_like(inside)
    if tg > 0:
        d = np.sqrt((u / (0.34 * w)) ** 2 + ((v - h * 1.02) / (tg * h)) ** 2)
        tongue = np.clip((1 - d) / 0.08, 0, 1) * inside
    col = np.zeros((PH, PW, 3), np.float32)
    col[:] = (34, 14, 52)                                   # the dark inside (BGR: a deep red-brown)
    col = col * (1 - tongue[..., None]) + np.array([78, 72, 178], np.float32) * tongue[..., None]
    col = col * (1 - teeth[..., None]) + np.array([244, 244, 246], np.float32) * teeth[..., None]
    col = col * (1 - outline[..., None]) + np.array(ink, np.float32) * outline[..., None]
    alpha = np.maximum(inside, outline)
    out = img.copy()
    x0, y0 = int(round(ox)), int(round(oy))
    H, W = img.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + PW), min(H, y0 + PH)
    if xa < xb and ya < yb:
        al = alpha[ya - y0:yb - y0, xa - x0:xb - x0, None]
        reg = out[ya:yb, xa:xb, :3].astype(np.float32)
        out[ya:yb, xa:xb, :3] = (reg * (1 - al) + col[ya - y0:yb - y0, xa - x0:xb - x0] * al).astype(np.uint8)
    return out


def closed_mouth(img, info, squash=1.0, tilt=0.0, size=1.0, ink=(22, 16, 18)):
    """Closed lips in the drawings' style: one ink line, a little thicker in the middle."""
    cx, cy, mw, _ = info['mouth']
    w = 0.62 * mw * size * squash
    S = 4
    pad = int(0.1 * mw) + 4
    PW, PH = int(w + 2 * pad), int(0.3 * mw + 2 * pad)
    ts = np.linspace(-1, 1, 40)
    th = math.radians(tilt)
    pts = np.stack([ts * w / 2, 0.035 * mw * (1 - ts ** 2) - 0.02 * mw], 1)
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    pts = pts @ R.T + [PW / 2, PH / 2]
    m = np.zeros((PH * S, PW * S), np.uint8)
    lw = max(2, int(0.04 * mw * size * S))
    cv2.polylines(m, [np.round(pts * S).astype(np.int32)], False, 255, lw, cv2.LINE_AA)
    a = cv2.resize(m, (PW, PH), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255
    out = img.copy()
    x0, y0 = int(round(cx - PW / 2)), int(round(cy - PH / 2))
    H, W = img.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + PW), min(H, y0 + PH)
    if xa < xb and ya < yb:
        al = a[ya - y0:yb - y0, xa - x0:xb - x0]
        reg = out[ya:yb, xa:xb, :3].astype(np.float32)
        out[ya:yb, xa:xb, :3] = (reg * (1 - al) + np.array(ink, np.float32) * al).astype(np.uint8)
    return out


# ------------------------------------------------------------------ lip sync
VOWEL = {'AA': 'a', 'AE': 'a', 'AH': 'e', 'AY': 'a', 'AW': 'a', 'EH': 'e', 'EY': 'e', 'ER': 'e',
         'IH': 'i', 'IY': 'i', 'OW': 'o', 'AO': 'o', 'OY': 'o', 'UW': 'u', 'UH': 'u'}
CONS = {'M': 'rest', 'B': 'rest', 'P': 'rest', 'F': 'i', 'V': 'i', 'W': 'u', 'R': 'u', 'Y': 'i',
        'SH': 'u', 'ZH': 'u', 'CH': 'i', 'JH': 'i', 'S': 'i', 'Z': 'i', 'T': 'i', 'D': 'i', 'N': 'i',
        'TH': 'e', 'DH': 'e', 'L': 'e', 'K': 'e', 'G': 'e', 'NG': 'e', 'HH': 'e'}


# Roy's sheet: A (day), E (get), I (sit), O (go), U (put), C/D/G, F/V, L, M/B/P, R, TH
VOWEL_ROY = {'AA': 'a', 'AE': 'a', 'AH': 'e', 'AY': 'a', 'AW': 'o', 'EH': 'e', 'EY': 'a', 'ER': 'r',
             'IH': 'i', 'IY': 'i', 'OW': 'o', 'AO': 'o', 'OY': 'o', 'UW': 'u', 'UH': 'u'}
CONS_ROY = {'M': 'mbp', 'B': 'mbp', 'P': 'mbp', 'F': 'fv', 'V': 'fv', 'L': 'l', 'R': 'r', 'W': 'u',
            'TH': 'th', 'DH': 'th'}                    # everything else: C/D/G


# Rooney's sheet: rest, A, E, I, O, smile
VOWEL_ROONEY = {'AA': 'a', 'AE': 'a', 'AH': 'e', 'AY': 'a', 'AW': 'a', 'EH': 'e', 'EY': 'e', 'ER': 'e',
                'IH': 'i', 'IY': 'i', 'OW': 'o', 'AO': 'o', 'OY': 'o', 'UW': 'o', 'UH': 'o'}
CONS_ROONEY = dict(CONS, W='o', R='o', SH='o', ZH='o')
# Rio's sheet: rest, A, E, I, O, U, M/B/P, F/V
CONS_RIO = dict(CONS, M='mbp', B='mbp', P='mbp', F='fv', V='fv')
STYLES = {'roy': (VOWEL_ROY, CONS_ROY, 'mbp', 'cdg'), 'rooney': (VOWEL_ROONEY, CONS_ROONEY, 'rest', 'i'),
          'rio': (VOWEL, CONS_RIO, 'rest', 'i'), 'sheet': (VOWEL, CONS, 'rest', 'i')}


def phones_to_frames(words, dur, fps=FPS, loud=False, style='sheet'):
    """Per-frame mouth keys from aligned words/phones; held on twos."""
    vowels, cons, rest, other = STYLES[style]
    n = int(dur * fps) + 2
    best = [None] * n
    wgt = np.zeros(n)
    for w in words:
        for ph, a, b in w['phones']:
            ph = re.sub(r'\d', '', ph)
            key = vowels.get(ph) or cons.get(ph, other)
            if key in ('a', 'e', 'o') and loud and style == 'sheet':
                key = 'shout'                    # the drawing's own shout mouth where it has one
            isv = ph in vowels
            for f in range(max(0, int(a * fps)), min(n, max(int(a * fps) + 1, int(round(b * fps))))):
                sc = (b - a) + (0.15 if isv else 0) + (0.3 if key == rest else 0)
                if sc > wgt[f]:
                    wgt[f], best[f] = sc, key
    out, last, held = [], rest, 9
    for f in range(n):
        m = best[f] or rest
        if m != last and held < 2:
            m = last
        held = held + 1 if m == last else 1
        out.append(m)
        last = m
    return out


def gate_frames(frames, x, style='sheet', fps=FPS):
    """Tighten aligned mouth frames against the voice itself: every frame where the voice is
    quiet (and is not about to start) gets the closed mouth - the aligner stretches the first
    and last words over the pauses around them, which left mouths hanging open in silence -
    and each mouth change comes one frame before its sound. Runs of a single frame are merged
    so shapes still hold for at least two frames."""
    rest = STYLES[style][2]
    hop = SR / fps
    n = len(frames)
    rms = np.zeros(n)
    for i in range(n):
        a, b = int(max(0, (i - 0.25) * hop)), int(min(len(x), (i + 1.25) * hop))
        if b > a:
            rms[i] = np.sqrt(np.mean(x[a:b] ** 2))
    thr = max(0.006, 0.10 * np.percentile(rms, 95))
    voiced = rms > thr
    lead = list(frames[1:]) + [frames[-1]]                 # one frame ahead of the sound
    out = []
    for i in range(n):
        on = voiced[i] or (i + 1 < n and voiced[i + 1])
        out.append(lead[i] if on else rest)
    # no single-frame flickers: a lone frame takes its neighbour's shape
    for i in range(1, n - 1):
        if out[i] != out[i - 1] and out[i] != out[i + 1]:
            out[i] = out[i - 1] if out[i] != rest else out[i]
    return out


def synth_words(text, dur):
    """Evenly timed phones for a line with no recording yet."""
    sys.path.insert(0, HERE)
    import align as A
    words = A.words_of(text)
    phs = []
    for w in words:
        A.ensure_word(A.decoder(), w)
        p = A.decoder().lookup_word(w) or 'AH'
        phs.append(p.split())
    total = sum(len(p) for p in phs) or 1
    t = 0.05
    step = (dur - 0.1) / total
    out = []
    for w, p in zip(words, phs):
        t0 = t
        pp = []
        for ph in p:
            pp.append((ph, t, t + step))
            t += step
        out.append(dict(word=w, t0=t0, t1=t, phones=pp))
    return out


def load_audio(path):
    tmp = os.path.join(ROOT, 'out', 'wav44', os.path.basename(path) + '.wav')
    if not os.path.exists(tmp) or os.path.getmtime(tmp) < os.path.getmtime(path):
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-ac', '1', '-ar', str(SR), tmp], check=True)
    import soundfile as sf
    x, _ = sf.read(tmp, dtype='float32')
    return x


def find_audio(lid):
    for ext in ('.wav', '.mp3', '.m4a', '.aac', '.ogg', '.flac'):
        p = os.path.join(EP, 'audio', lid + ext)
        if os.path.exists(p):
            return p
    return None


def estimate_duration(text):
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'vec'))
    import lipsync as LS
    sy, _ = LS.syllables(text)
    return 0.35 + 0.2 * len(sy) + 0.25 * text.count('.')


# ------------------------------------------------------------------ timeline
class Track:
    def __init__(self):
        self.t, self.v, self.e = [], [], []

    def add(self, t, v, e='step'):
        i = bisect.bisect_right(self.t, t)
        self.t.insert(i, t); self.v.insert(i, v); self.e.insert(i, e)

    def at(self, t, default=None):
        if not self.t:
            return default
        i = bisect.bisect_right(self.t, t) - 1
        if i < 0:
            return self.v[0] if self.e[0] != 'step' else default
        v0 = self.v[i]
        if i + 1 < len(self.t) and isinstance(v0, (int, float)) and not isinstance(v0, bool) and self.e[i + 1] != 'step':
            t0, t1, v1 = self.t[i], self.t[i + 1], self.v[i + 1]
            u = min(1.0, max(0.0, (t - t0) / max(t1 - t0, 1e-6)))
            if self.e[i + 1] == 'ease':
                u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
        return v0


class Timeline:
    def __init__(self, script):
        self.script = script
        self.t = 0.0
        self.lines = []            # dict(id, who, start, dur, audio, text, words)
        self.tracks = {}
        self.shots = []            # (t, dict)
        self.fx = []               # (t, name, gain, kw)
        self.blinks = {}           # who -> [t]: blinks the staging asks for (the rest are random)
        self.shakes = []           # (t, amplitude in 1/1000 of the frame width, duration)
        self.cues = {}

    def key(self, t, who, e='step', **kv):
        for k, v in kv.items():
            self.tracks.setdefault((who, k), Track()).add(t, v, e)

    def get(self, who, k, t, default=None):
        tr = self.tracks.get((who, k))
        return tr.at(t, default) if tr else default

    def wait(self, d):
        s = self.t
        self.t += d
        return s

    def say(self, lid, gap=0.35, lead=0.0):
        who = self.script.SPEAKER[lid[:2]]
        text = self.script.LINES[lid]
        path = find_audio(lid)
        self.t += lead
        start = self.t
        if path:
            x = load_audio(path)
            dur = len(x) / SR
            words = None
            al = ALIGN.get(lid)
            if al:
                words = al
            else:
                import align as A
                w16 = os.path.join(ROOT, 'out', 'wav16', lid + '.wav')
                os.makedirs(os.path.dirname(w16), exist_ok=True)
                A.to16k(path, w16)
                try:
                    words = A.align(w16, text)
                except Exception:
                    words = synth_words(text, dur)
        else:
            dur = estimate_duration(text)
            words = synth_words(text, dur)
        ln = dict(id=lid, who=who, start=start, dur=dur, audio=path, text=text, words=words)
        self.lines.append(ln)
        self.t = start + dur + gap
        return ln

    def shot(self, t, bg, rect=None, **kw):
        d = dict(kw, bg=bg, rect=rect, t=t)
        i = bisect.bisect_right([s[0] for s in self.shots], t)
        self.shots.insert(i, (t, d))

    def sfx(self, t, name, gain=1.0, **kw):
        self.fx.append((t, name, gain, kw))

    def shot_at(self, t):
        i = bisect.bisect_right([s[0] for s in self.shots], t) - 1
        s = self.shots[max(i, 0)][1]
        t1 = self.shots[i + 1][0] if i + 1 < len(self.shots) else self.t
        return s, t1


ALIGN = {}


def load_alignment():
    p = os.path.join(EP, 'audio', 'alignment.json')
    if os.path.exists(p):
        ALIGN.update(json.load(open(p)))


# ------------------------------------------------------------------ compositing
def over(frame, rgba, x, y):
    """Alpha-composite RGBA onto BGR frame at float position (x, y)."""
    h, w = rgba.shape[:2]
    H, W = frame.shape[:2]
    xi, yi = int(round(x)), int(round(y))
    xa, ya, xb, yb = max(xi, 0), max(yi, 0), min(xi + w, W), min(yi + h, H)
    if xa >= xb or ya >= yb:
        return
    s = rgba[ya - yi:yb - yi, xa - xi:xb - xi]
    a = s[..., 3:4].astype(np.float32) * (1 / 255)
    d = frame[ya:yb, xa:xb]
    frame[ya:yb, xa:xb] = (s[..., :3] * a + d * (1 - a)).astype(np.uint8)


def over_full(frame, rgba):
    a = rgba[..., 3]
    ys, xs = np.nonzero(a[::8, ::8])
    if len(ys) == 0:
        return
    y0, y1 = max(0, ys.min() * 8 - 8), min(a.shape[0], ys.max() * 8 + 16)
    x0, x1 = max(0, xs.min() * 8 - 8), min(a.shape[1], xs.max() * 8 + 16)
    over(frame, rgba[y0:y1, x0:x1], x0, y0)


# under a close-up head the body is the calm arms-down drawing: a gesturing pose's hands would
# poke out from behind the bust with no arms (crossed arms stay crossed)
CU_BODY = {'upper/crossed_arms': 'upper/crossed_arms'}


class Renderer:
    def __init__(self, tl, size=OUT):
        self.tl = tl
        self.size = size
        self.bgs = {}
        self.rigs = {c: Rig(c) for c in CHARS}
        self.scaled = {}
        self.blinks = self.plan_blinks()
        self.face_px = {}              # who -> (x, y, face width, drawing) of the last frame drawn
        self.mouth_frames = {}
        for ln in tl.lines:
            loud = ln['id'] in getattr(tl.script, 'LOUD', ())
            style = ln['who'] if ln['who'] in STYLES else 'sheet'
            fr = phones_to_frames(ln['words'], ln['dur'], loud=loud, style=style)
            if ln['audio']:
                fr = gate_frames(fr, load_audio(ln['audio']), style)
            self.mouth_frames[ln['id']] = fr

    def bg(self, name):
        if name not in self.bgs:
            self.bgs[name] = Background(name)
        return self.bgs[name]

    def plan_blinks(self):
        out = {}
        for i, c in enumerate(CHARS):
            rng = np.random.RandomState(20 + i)
            t, lst = 1.0 + i * 0.7, []
            while t < self.tl.t + 5:
                lst.append(t)
                t += rng.uniform(2.4, 5.0)
            forced = sorted(self.tl.blinks.get(c, []))
            lst = [b for b in lst if all(abs(b - f) > 1.2 for f in forced)]
            out[c] = sorted(lst + forced)
        return out

    def blink(self, who, t):
        for b in self.blinks[who]:
            k = (t - b) * FPS
            if 0 <= k < 4:
                return [0.45, 0.75, 0.75, 0.45][int(k)]
        return 0.0

    def speaking(self, who, t):
        for ln in self.tl.lines:
            if ln['who'] == who and ln['start'] <= t < ln['start'] + ln['dur']:
                f = int((t - ln['start']) * FPS)
                fr = self.mouth_frames[ln['id']]
                return fr[min(f, len(fr) - 1)], ln
        return None, None

    # -- where a character is in a given background
    def placement(self, who, t, bgname):
        tl = self.tl
        loc = tl.get(who, 'loc', t, 'off')
        if loc == 'off':
            return None
        cfg = self.bg(bgname).cfg
        body = tl.get(who, 'body', t, 'upper/arms_down')
        flip = tl.get(who, 'flip', t, False)
        if loc == 'seat':
            back = cfg.get('spots', {}).get(who + '_back')
            if back:
                return dict(kind='back', spot=back)
            seat = cfg.get('seats', {}).get(who)
            if not seat:
                return None
            dy = tl.get(who, 'dy', t, 0.0) or 0.0
            return dict(kind='face', pos=(seat['face'][0], seat['face'][1] + dy * seat['face_w']), fw=seat['face_w'],
                        body=body, flip=flip)
        if loc in ('stand', 'walk'):
            path = tl.get(who, 'path', t)
            if not path:
                return None
            a, b = path
            sa, sb = cfg.get('spots', {}).get(a), cfg.get('spots', {}).get(b)
            if not sa or not sb:
                return None
            u = tl.get(who, 'u', t, 0.0) if loc == 'walk' else 1.0
            fx = sa['feet'][0] + (sb['feet'][0] - sa['feet'][0]) * u
            fy = sa['feet'][1] + (sb['feet'][1] - sa['feet'][1]) * u
            fw = sa['face_w'] + (sb['face_w'] - sa['face_w']) * u
            if loc == 'walk':
                cyc = tl.get(who, 'cycle', t, ['body/walk_1', 'body/walk_2', 'body/walk_3', 'body/walk_4'])
                body = cyc[int(t * 8) % len(cyc)]          # 8 drawings a second: the show's brisk walk
                fy -= abs(math.sin(t * 8 * math.pi / 2)) * fw * 0.04
            return dict(kind='feet', pos=(fx, fy), fw=fw, body=body, flip=flip)
        return None

    def _rect(self, r, t0):
        if callable(r):
            key = ('cam', id(r), t0)
            if key not in self.scaled:
                self.scaled[key] = r(self, t0 + 0.2)
            return self.scaled[key]
        return r

    def camera(self, t):
        """The shot's camera at time t: its rect, then (optionally) a crash zoom in from a wider
        rect ('crash_from', over 'crash' seconds), a slow push in over the whole shot ('push': the
        fraction the frame narrows by, about 'focus' or the frame centre) and the timeline's
        camera shakes."""
        s, t1 = self.tl.shot_at(t)
        x0, y0, w = self._rect(s['rect'], s['t'])
        u = t - s['t']
        if s.get('crash_from') is not None and u < s.get('crash', 0.12):
            a = self._rect(s['crash_from'], s['t'])
            k = u / s.get('crash', 0.12)
            k = 1 - (1 - k) ** 3
            x0, y0, w = a[0] + (x0 - a[0]) * k, a[1] + (y0 - a[1]) * k, a[2] + (w - a[2]) * k
        push = s.get('push')
        if push:
            k = min(1.0, max(0.0, u / max(t1 - s['t'], 1e-3)))
            k = k * k * (3 - 2 * k)
            h = w * OUT[1] / OUT[0]
            fx, fy = s.get('focus') or (0.5, 0.42)
            cx, cy = x0 + fx * w, y0 + fy * h
            sc = 1 - push * k
            x0, y0, w = cx - fx * w * sc, cy - fy * h * sc, w * sc
        for ts, amp, dur in self.tl.shakes:
            if ts <= t < ts + dur:
                e = (1 - (t - ts) / dur) ** 2 * amp * w / 1000.0
                x0 += e * math.sin(t * 97.0) * 1.0
                y0 += e * math.cos(t * 83.0) * 0.8
        return s, (x0, y0, w)

    def sprite_scaled(self, rig, key, mouth, blink, flip, scale):
        sq = round(math.log(scale) * 400) / 400        # fine steps: no visible jumps in a camera push
        ck = (rig.name, key, mouth, round(blink, 1), flip, sq)
        hit = self.scaled.get(ck)
        if hit is not None:
            return hit
        img = rig.drawing(key, mouth, blink, flip)
        s = math.exp(sq)
        res = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
        self.scaled[ck] = (res, s)
        trim(self.scaled, 400e6, keep=lambda k: k[0] == 'cam')
        return res, s

    def draw_char(self, frame, who, t, bgname, rect, shot):
        pl = self.placement(who, t, bgname)
        if pl is None:
            return
        rig = self.rigs[who]
        x0, y0, cw = rect
        k1 = OUT[0] / cw                        # output px per 1x px
        if pl['kind'] == 'back':
            sp = pl['spot']
            key = 'turnaround/back'
            info = rig.face(key)
            img = rig.image(key)
            W, H = info['size']
            head_w = W * 0.62                         # the back view's head is ~62% of the drawing width
            s = sp['head_w'] * k1 / head_w
            res = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
            res = cv2.GaussianBlur(res, (0, 0), 3.0)
            over(frame, res, (sp['head'][0] - x0) * k1 - res.shape[1] / 2, (sp['head'][1] - y0) * k1 - res.shape[0] * 0.2)
            return
        mouth, ln = self.speaking(who, t)
        talk = mouth is not None and self.tl.get(who, 'talk', t, True)
        env = 1.0 if (talk and mouth not in ('rest', None)) else 0.0
        key = pl['body']
        fw_out = pl['fw'] * k1
        cu = None
        if fw_out > rig.over.get('_cu_px', 700 if pl['kind'] == 'face' else 400):
            # seen large: a close-up drawing (expression bust / high-res head) supplies the head
            cu = self.tl.get(who, 'face', t, 'expressions/neutral' if pl['kind'] == 'face' else None)
        blink = self.blink(who, t) if not self.tl.get(who, 'eyes_shut', t, False) else 1.0
        nod = self.tl.get(who, 'nod', t, 0.0) or 0.0
        bob = (-env * fw_out * 0.012 + nod * fw_out * 0.035) if pl['kind'] == 'face' else 0.0
        # the body drawing, anchored by its face (seated) or its feet (standing)
        info = rig.face(key)
        W, H = info['size']
        idle = rig.over.get('_rest_when_silent', [])       # drawn open mouths close when not talking
        quiet = rig.over.get('_silent_mouth', 'rest')
        body_mouth = (mouth if talk else (quiet if key in idle else None)) if cu is None else None
        res, s = self.sprite_scaled(rig, key, body_mouth, blink if cu is None else 0.0, pl['flip'], fw_out / max(info['width'], 1))
        cx, cy = info['center']
        if pl['flip']:
            cx = W - cx
        if pl['kind'] == 'face':
            px = (pl['pos'][0] - x0) * k1 - cx * s
            py = (pl['pos'][1] - y0) * k1 - cy * s + bob
        elif self.cut_bottom(rig, key):
            # a drawing cut off at the waist (a gesture bust): its face goes where the full-body
            # reference drawing's face is, standing on the same spot
            ref = rig.face(rig.over.get('_stand_ref', 'turnaround/front'))
            eye_h = (ref['feet'][1] - ref['center'][1]) * fw_out / max(ref['width'], 1)
            px = (pl['pos'][0] - x0) * k1 - cx * s
            py = (pl['pos'][1] - y0) * k1 - eye_h - cy * s
        else:
            fy = info['feet'][1]
            px = (pl['pos'][0] - x0) * k1 - cx * s
            py = (pl['pos'][1] - y0) * k1 - fy * s
        if pl['kind'] == 'feet' and self.cut_bottom(rig, key) and py + res.shape[0] < frame.shape[0] - 2:
            # the frame shows below the waist where a gesture bust ends: the full-body drawing instead
            key = rig.over.get('_stand_ref', 'turnaround/front')
            info = rig.face(key)
            W, H = info['size']
            res, s = self.sprite_scaled(rig, key, body_mouth, blink if cu is None else 0.0, pl['flip'],
                                        fw_out / max(info['width'], 1))
            cx, cy = info['center']
            if pl['flip']:
                cx = W - cx
            px = (pl['pos'][0] - x0) * k1 - cx * s
            py = (pl['pos'][1] - y0) * k1 - info['feet'][1] * s
        self.face_px[who] = (px + cx * s, py + cy * s, fw_out, cu or key)
        if cu is None:
            over(frame, res, px, py)
            return
        # close-up: the body from just under its chin, then the close-up head blended on at the same face
        calm = rig.over.get('_calm') or CU_BODY.get(key, 'upper/arms_down' if key.startswith('upper/') else None)
        if rig.over.get('_calm_keep') and key in rig.over['_calm_keep']:
            calm = key
        if calm and calm != key and calm.split('/')[1] in rig.idx.get(calm.split('/')[0], {}):
            key = calm
            info = rig.face(key)
            W, H = info['size']
            res, s = self.sprite_scaled(rig, key, None, 0.0, pl['flip'], fw_out / max(info['width'], 1))
            cx, cy = info['center']
            if pl['flip']:
                cx = W - cx
            if pl['kind'] == 'face' or self.cut_bottom(rig, key):
                px = (pl['pos'][0] - x0) * k1 - cx * s
                py = (pl['pos'][1] - y0) * k1 - cy * s + bob
            else:
                px = (pl['pos'][0] - x0) * k1 - cx * s
                py = (pl['pos'][1] - y0) * k1 - info['feet'][1] * s
        fcx, fcy = px + cx * s, py + cy * s
        cinfo = rig.face(cu)
        cs = fw_out / max(cinfo['width'], 1)
        cres, cs = self.sprite_scaled(rig, cu, mouth if talk else (quiet if cu in idle else None), blink, pl['flip'], cs)
        ccx, ccy = cinfo['center']
        if pl['flip']:
            ccx = cinfo['size'][0] - ccx
        # the body only from just above where the close-up bust ends: its own head and neck never show
        # (Roy's close-ups are heads without shoulders: his whole body goes under, the head covers its own)
        cu_bottom = fcy - ccy * cs + cres.shape[0]
        if rig.over.get('_cu_full_body') and info.get('mouth') is not None:
            # Roy: the body from mid-beard down (its own head would show beside a turned one)
            chin = int((info['mouth'][1] + 0.22 * info['width']) * s)
        else:
            chin = int(cu_bottom - rig.over.get('_cu_overlap', 0.14) * fw_out - py)
        chin = max(0, min(res.shape[0], chin))
        over(frame, res[chin:], px, py + chin)
        mk = ('cumask', who, cu, pl['flip'], cres.shape)
        m = self.scaled.get(mk)
        if m is None:
            m = self.cu_mask(rig, cu, pl['flip'], cres.shape[1], cres.shape[0])
            self.scaled[mk] = m
        cres = cres.copy()
        cres[..., 3] = (cres[..., 3] * m).astype(np.uint8)
        over(frame, cres, fcx - ccx * cs, fcy - ccy * cs)

    @staticmethod
    def cut_bottom(rig, key):
        panel, name = key.split('/')
        if panel == 'upper' and rig.over.get('_stand_ref'):
            return True                 # a standing character's gesture busts end at the waist
        return bool(rig.idx.get(panel, {}).get(name, {}).get('cut', {}).get('bottom'))

    def cu_mask(self, rig, key, flip, w, h):
        """A close-up drawing is kept whole; only the edges where the sheet cut
        it off (bottom, and the sides of the shoulders) fade into the body
        drawn underneath."""
        info = rig.face(key)
        W, H = info['size']
        fw = info['box'][2] - info['box'][0]
        a = rig.image(key)[..., 3] > 20
        m = np.ones((H, W), np.float32)
        ramp = max(2.0, fw * rig.over.get('_cu_ramp', 0.1))
        yy = np.arange(H, dtype=np.float32)[:, None]
        xx = np.arange(W, dtype=np.float32)[None, :]
        m *= np.clip((H - 1 - yy) / ramp, 0, 1)
        # sides only where the drawing actually touches them (cut shoulders), and only low down
        low = np.clip((yy - info['box'][3] + 0.1 * fw) / ramp, 0, 1)
        if a[:, 0].any():
            m *= 1 - (1 - np.clip(xx / ramp, 0, 1)) * low
        if a[:, -1].any():
            m *= 1 - (1 - np.clip((W - 1 - xx) / ramp, 0, 1)) * low
        if flip:
            m = m[:, ::-1]
        return cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)

    def render(self, t):
        shot, rect = self.camera(t)
        if shot['bg'] in INSERTS:
            return INSERTS[shot['bg']](self, t, shot)
        bgo = self.bg(shot['bg'])
        bgimg, fg = bgo.view(rect, shot.get('dof', 0.0))
        frame = bgimg.copy()
        order = shot.get('order', ('rooney', 'mark', 'roy', 'rio'))
        self.face_px = {}
        for who in order:
            self.draw_char(frame, who, t, shot['bg'], rect, shot)
        over_full(frame, fg)
        for fn in OVERLAYS:
            frame = fn(self, t, frame)
        fade = self.tl.get('world', 'fade', t, 0.0) or 0.0
        if fade > 0:
            frame = (frame * (1 - min(fade, 1.0))).astype(np.uint8)
        if self.size != OUT:
            frame = cv2.resize(frame, self.size, interpolation=cv2.INTER_AREA)
        return frame


INSERTS = {}
OVERLAYS = []             # fn(renderer, t, frame) -> frame: on-screen graphics over the composed shot
