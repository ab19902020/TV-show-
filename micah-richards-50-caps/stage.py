"""Stages: a set plate + actors + occluders, rendered through a camera window.

World coordinates are 4x-plate pixels; positions in the direction files are given in 1x plate px (x4 here). An
actor is one Drawing placed with its anchor at a world point; `scale` = 1x plate px per sheet px (which is also
world px per full-res part px). Per frame an actor gets a face state (lip sync, blink, gaze, brows, head tilt / nod /
turn) and a body transform (breathing, lean, bob, slide). Occluders are polygons (1x plate coords) of the plate that
stand in front of the actors (the table, foreground chairs); they are re-composited over the actors from the plate
itself, so the edge is the painting's own edge."""
import math, numpy as np, cv2
import engine as E
import cast

OW, OH = E.OW, E.OH


class Actor:
    def __init__(self, drawing, x, y, scale, flip=False, anchor="collar", z=0.0, clip=None, shade=0.0, rim=None,
                 name=None, light=1.0):
        self.d = cast.get(drawing) if isinstance(drawing, str) else drawing
        self.x, self.y, self.scale, self.flip, self.z = x * 4, y * 4, scale, flip, z
        self.anchor = self.d.anchors.get(anchor, (0.0, 0.0)) if isinstance(anchor, str) else self.d.P(*anchor)
        self.clip, self.shade, self.rim, self.light = clip, shade, rim, light
        self.name = name or self.d.name

    def matrix(self, body=None):
        """full-res part px -> world px (3x3)"""
        ax, ay = self.anchor
        s = self.scale * 4.0 / self.d.k          # world px per part px (parts are 4x or 8x the sheet)
        sx = -s if self.flip else s
        M = np.array([[sx, 0, self.x - sx * ax], [0, s, self.y - s * ay], [0, 0, 1]], np.float64)
        if body is not None:
            M = M @ body
        return M


def body_matrix(pivot, breath=0.0, lean=0.0, dx=0.0, dy=0.0, sx=1.0, sy=1.0, skew=0.0):
    """part-space transform about pivot (full-res part px): breathing = vertical stretch, lean in degrees,
    skew (shoulder rotation in a walk), translation in part px"""
    px, py = pivot
    S = np.array([[sx, skew, (1 - sx) * px - skew * py], [0, sy * (1 + breath), (1 - sy * (1 + breath)) * py], [0, 0, 1]], np.float64)
    R = np.vstack([cv2.getRotationMatrix2D((float(px), float(py)), -lean, 1.0), [0, 0, 1]])
    T = np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]], np.float64)
    return T @ R @ S


def blur_half(img, sigma):
    small = cv2.resize(img, (OW // 2, OH // 2), interpolation=cv2.INTER_AREA)
    return cv2.resize(cv2.GaussianBlur(small, (0, 0), sigma / 2 * E.RS), (OW, OH), interpolation=cv2.INTER_LINEAR)


class Stage:
    def __init__(self, plate, occluders=(), ambient=(1.0, 1.0, 1.0), rim=None, name=""):
        self.set = E.Set(name, plate, occl=occluders if occluders else None)
        self.ambient = np.float32(ambient)
        self.rim = rim
        self.name = name

    def render(self, cam, actors, dof=0.0, plate_fx=None, post_fx=None, occ_dof=None, fg_actors=()):
        """cam = (cx, cy, w) in 1x plate px. actors = list of (Actor, face_state, body 3x3 or None, alpha);
        fg_actors are drawn after the occluders (in front of the table). plate_fx(bg, Aw) paints into the plate
        before depth of field (TV screens, crowds). Returns float32 RGB frame (0..1)."""
        cx, cy, w = [v * 4 for v in cam]
        z = OW / w
        h = w * OH / OW
        ox, oy = cx - w / 2, cy - h / 2
        L = 1 if z * 4 <= 1.15 else (2 if z * 2 <= 1.15 else 4)
        k = z * 4 / L                                   # screen px per plate-level px
        src = self.set.levels[L]
        if k < 0.95:
            small = cv2.resize(src, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
            A2 = np.float32([[1, 0, -z * ox], [0, 1, -z * oy]])
            bg = cv2.warpAffine(small, A2, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        else:
            A = np.float32([[k, 0, -z * ox], [0, k, -z * oy]])
            bg = cv2.warpAffine(src, A, (OW, OH), flags=cv2.INTER_CUBIC if k > 1.05 else cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REFLECT)
        bg = bg.astype(np.float32) / 255.0
        Aw = np.float32([[z, 0, -z * ox], [0, z, -z * oy]])      # world -> screen
        if plate_fx is not None:
            bg = plate_fx(bg, Aw)
        occ = None
        if self.set.occl is not None:
            A = np.float32([[k, 0, -z * ox], [0, k, -z * oy]])
            occ = cv2.warpAffine(self.set.occl[L], A, (OW, OH), flags=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255.0
        sharp = bg
        if dof > 0.3:
            bg = blur_half(bg, dof)
        C = np.array([[z, 0, -z * ox], [0, z, -z * oy], [0, 0, 1]], np.float64)
        layer = np.zeros((OH, OW, 4), np.float32)
        for actor, st, body, alpha in sorted(actors, key=lambda a: a[0].z):
            if alpha > 0.001: self.draw_actor(layer, C, actor, st, body, alpha)
        a = layer[..., 3:4]
        frame = layer[..., :3] + bg * (1 - a)
        if occ is not None:
            od = dof if occ_dof is None else occ_dof
            fg = blur_half(sharp, od) if od > 0.3 else sharp
            frame = fg * occ + frame * (1 - occ)
        if fg_actors:
            layer2 = np.zeros((OH, OW, 4), np.float32)
            for actor, st, body, alpha in sorted(fg_actors, key=lambda a: a[0].z):
                if alpha > 0.001: self.draw_actor(layer2, C, actor, st, body, alpha)
            frame = layer2[..., :3] + frame * (1 - layer2[..., 3:4])
        if post_fx is not None:
            frame = post_fx(frame, Aw)
        return frame

    def draw_actor(self, layer, C, actor, st, body, alpha):
        M = C @ actor.matrix(body)
        sc = math.sqrt(abs(M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0]))     # screen px per full-res part px
        Lv = 1.0 if sc > 0.62 else (0.5 if sc > 0.31 else 0.25)
        base = actor.d.base(Lv, actor.clip)
        Mf = M @ np.array([[1 / Lv, 0, 0], [0, 1 / Lv, 0], [0, 0, 1]])
        H, W = layer.shape[:2]
        hh, ww = base.shape[:2]
        c = cv2.transform(np.float32([[[0, 0], [ww, 0], [0, hh], [ww, hh]]]), Mf[:2].astype(np.float32))[0]
        bx0, by0 = int(max(0, np.floor(c[:, 0].min()) - 2)), int(max(0, np.floor(c[:, 1].min()) - 2))
        bx1, by1 = int(min(W, np.ceil(c[:, 0].max()) + 2)), int(min(H, np.ceil(c[:, 1].max()) + 2))
        if bx1 <= bx0 or by1 <= by0: return
        # the actor goes into its own buffer first (the head patch replaces the base's head), then over the layer
        loc = np.zeros((by1 - by0, bx1 - bx0, 4), np.float32)
        T = np.array([[1, 0, -bx0], [0, 1, -by0], [0, 0, 1]], np.float64)
        E.warp_into(loc, base, (T @ Mf)[:2].astype(np.float32))
        p = actor.d.patch(Lv, st, actor.clip) if st is not None else None
        if p is not None:
            px0, py0, pimg = p
            Mp = T @ Mf @ np.array([[1, 0, px0], [0, 1, py0], [0, 0, 1]], np.float64)
            E.warp_into(loc, pimg, Mp[:2].astype(np.float32), mode="replace")
        if actor.light != 1.0:
            loc[..., :3] *= actor.light
        if actor.shade:
            loc[..., :3] *= (1 - actor.shade)
        rimspec = actor.rim or self.rim
        if rimspec:
            dx, dy, strength, col = rimspec
            loc = E.rim(loc, dx, dy, strength, col, max(1.2, 1.4 * sc * 4 * Lv))
        loc[..., :3] *= self.ambient
        if alpha != 1.0: loc *= alpha
        reg = layer[by0:by1, bx0:bx1]
        layer[by0:by1, bx0:bx1] = loc + reg * (1 - loc[..., 3:4])
