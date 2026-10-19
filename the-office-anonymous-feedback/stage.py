"""Drawing one character into a frame: pose (with a short cross-fade between poses), face, placement, desk cut."""
import numpy as np
import cast, engine


def draw(frame, Mcam, z, char, pose, facekey, pl, desk=None, alpha=1.0, rot=0.0, dy=0.0, hands=True):
    """pl: placement dict(pos=(x, y) world, scale, anchor='eyes'|'feet', mirror=bool)
    desk: (cut_y, front_y) world rows: below cut only the hands show, below front nothing."""
    rgb, a = cast.posed(char, pose, facekey)
    r = cast.rig(char, pose)
    anchor = r["eyes_mid"] if pl.get("anchor", "eyes") == "eyes" else r["feet"]
    anchor = anchor + np.array(pl.get("nudge", {}).get(pose, (0, 0))) * 4
    pos = (pl["pos"][0], pl["pos"][1] + dy)
    M = engine.actor_matrix(anchor, pos, pl["scale"], z, Mcam, pl.get("mirror", False), rot)
    hm = engine.hand_mask(char, pose) if desk else None
    placed = engine.place(frame, rgb.astype(np.float32), a.astype(np.float32) / 255, M, hm)
    if placed is None:
        return
    (x0, y0, x1, y1), out, em = placed
    mul = np.full(out.shape[:2], alpha, np.float32)
    if desk:
        cut, front = desk
        yc = cut * Mcam[1, 1] + Mcam[1, 2]
        yf = front * Mcam[1, 1] + Mcam[1, 2]
        rows = np.arange(y0, y1, dtype=np.float32)[:, None] + 0.5
        above = np.clip(yc - rows + 0.5, 0, 1)
        infront = np.clip(yf - rows + 0.5, 0, 1)
        mul *= above + ((1 - above) * np.clip(em, 0, 1) * infront if hands else 0.0)
    engine.comp(frame, placed, mul)
