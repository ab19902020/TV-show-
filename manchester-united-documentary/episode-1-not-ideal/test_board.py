import sys, time, numpy as np, cv2
import sets, stage
from stage import Actor
st = sets.boardroom()
A = [
  (Actor("ck_suit", 232, 470, 0.6, z=3, clip=600), dict(lookx=0.8, turn=0.3, vis="AI"), None, 1.0),
  (Actor("js_tablet", 450, 440, 0.9, flip=True, z=2), dict(blink=1.0), None, 1.0),
  (Actor("om_suit", 640, 432, 1.12, z=1, clip=260), dict(lookx=-0.6, vis="O"), None, 1.0),
  (Actor("jr_suit", 995, 410, 0.8, z=0, clip=260), dict(looky=0.6, tilt=4), None, 1.0),
]
for cam, name in [((836, 470.5, 1672), "wide"), ((240, 425, 470), "ck_mcu"), ((470, 420, 420), "js_ms"), ((995, 395, 330), "jr_ms")]:
    t = time.time()
    fr = st.render(cam, A, dof=0 if name == "wide" else 4)
    print(name, round(time.time() - t, 2))
    cv2.imwrite(f"build/test_{name}.jpg", (np.clip(fr, 0, 1) * 255)[..., ::-1].astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
