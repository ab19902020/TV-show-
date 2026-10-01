"""Backgrounds. 1x plates live in build/bg1x/, the 4x plates the engine reads in build/bg/.

  python3 plates.py quick   -> 1x plates + plain cubic 4x copies (for layout checks)
  python3 plates.py up      -> 4x Real-ESRGAN (anime 6B) of every 1x plate (slow; runs after the parts)

The studio is the repo's red-and-black set (1672 x 941), extended 110 px above and below (mirrored, then blurred and
darkened away from the seam) so a portrait window can show all three seats. Wing's backgrounds are portrait 941 x 1672."""
import os, sys, cv2, numpy as np

ART = "src/art/"
STUDIO_SRC = "../manchester-united-documentary/assets/backgrounds/tv-studio/red-and-black-football-studio-set.png"
EXT = 160
WINGS = {"w_exterior": "wings-exterior-lincoln-square", "w_party": "wings-dining-room-50-caps-table", "w_bar": "wings-bar",
         "w_round": "wings-dining-room-round-table", "w_entrance": "wings-entrance-50-caps-balloons",
         "w_panda": "wings-dining-room-panda-painting"}


def studio_1x():
    im = cv2.imread(STUDIO_SRC)
    def fade(ext, k):                                    # k: 0 at the seam .. 1 at the far edge, shape (EXT,)
        k = np.clip(k * 1.15, 0, 1).astype(np.float32)[:, None, None]
        blur = cv2.GaussianBlur(ext, (0, 0), 14)
        return (ext * (1 - k) + blur * k) * (1 - 0.38 * k)
    top = fade(im[:EXT][::-1].astype(np.float32), np.linspace(1, 0, EXT))      # rows run far -> seam
    bot = fade(im[-EXT:][::-1].astype(np.float32), np.linspace(0, 1, EXT))     # rows run seam -> far
    out = np.vstack([top, im.astype(np.float32), bot])
    return np.clip(out, 0, 255).astype(np.uint8)


def one_x():
    os.makedirs("build/bg1x", exist_ok=True)
    cv2.imwrite("build/bg1x/studio.png", studio_1x())
    for k, f in WINGS.items():
        im = cv2.imread(ART + f + ".png")
        im = cv2.resize(im, (941, 1672), interpolation=cv2.INTER_CUBIC) if im.shape[:2] != (1672, 941) else im
        cv2.imwrite(f"build/bg1x/{k}.png", im)


def quick():
    one_x(); os.makedirs("build/bg", exist_ok=True)
    for f in sorted(os.listdir("build/bg1x")):
        if os.path.exists("build/bg/" + f) and "--force" not in sys.argv: continue
        im = cv2.imread("build/bg1x/" + f)
        cv2.imwrite("build/bg/" + f, cv2.resize(im, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC))
        print("quick", f)


def up():
    import upscale
    from PIL import Image
    one_x(); os.makedirs("build/bg", exist_ok=True)
    for f in sorted(os.listdir("build/bg1x")):
        out = "build/bg/" + f
        mark = out + ".esrgan"
        if os.path.exists(mark): continue
        rgb = cv2.cvtColor(cv2.imread("build/bg1x/" + f), cv2.COLOR_BGR2RGB)
        big = upscale.upscale(np.ascontiguousarray(rgb), "RealESRGAN_x4plus_anime_6B", tile=256, pad=16)
        cv2.imwrite(out, cv2.cvtColor(big, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_PNG_COMPRESSION, 1])
        open(mark, "w").write("ok")
        print("up", f, big.shape, flush=True)


if __name__ == "__main__":
    {"quick": quick, "up": up, "1x": one_x}[sys.argv[1]]()
