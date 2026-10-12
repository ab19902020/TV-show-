"""The Undercard's props hook for the engine's world shots: ("props", "scene") draws the shot's cast
(film/actors.py); plate_image gives the engine sets the pack does not have as a painting of their own:
    E  Dana's dressing room, the blue corner: the red corner's room seen the other way round (mirrored), its reds
       turned to blue (lockers, wall, the poster), the lamps' warm light kept"""
import functools

import cv2
import numpy as np

from film.actors import scene  # noqa: F401


@functools.lru_cache(maxsize=2)
def plate_image(k):
    if k != "E":
        return None
    from studio.episode.upscale import upscaled
    from studio.paths import BACKGROUNDS
    big = upscaled(BACKGROUNDS / "boxing/dressing-room.png", 4.0)[:, ::-1]          # BGR, mirrored
    big = np.ascontiguousarray(big)
    hsv = cv2.cvtColor(big, cv2.COLOR_BGR2HSV)
    h, s = hsv[..., 0].astype(np.float32), hsv[..., 1].astype(np.float32)
    d = np.minimum(h, 180 - h)                                                     # hue distance from red
    w = np.clip((9 - d) / 4, 0, 1) * np.clip((s - 110) / 50, 0, 1)                 # the reds, not the warm lamps
    blue = hsv.copy()
    blue[..., 0] = 112
    blue[..., 2] = (blue[..., 2].astype(np.float32) * 0.85).astype(np.uint8)
    blue = cv2.cvtColor(blue, cv2.COLOR_HSV2BGR).astype(np.float32)
    w = cv2.GaussianBlur(w, (0, 0), 2.0)[..., None]                                # mixed as colours, so no
    out = big.astype(np.float32) * (1 - w) + blue * w                              # in-between (green) hues
    return np.clip(out, 0, 255).astype(np.uint8)[..., ::-1].copy()
