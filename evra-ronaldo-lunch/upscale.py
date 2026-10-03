"""4x Real-ESRGAN (anime 6B) on the CPU, in tiles, for every sheet and background in src/art -> build/up/<name>.png.
python3 upscale.py [names...]   (the model comes from GitHub releases: see make_scene.sh)"""
import sys, os, time, numpy as np, torch, spandrel
from PIL import Image
torch.set_num_threads(int(os.environ.get("THREADS", "4")))
ROOT = os.path.dirname(os.path.abspath(__file__))
_m = None


def model():
    global _m
    if _m is None:
        _m = spandrel.ModelLoader().load_from_file(os.path.join(ROOT, "models/RealESRGAN_x4plus_anime_6B.pth")).eval()
    return _m


def upscale(img, tile=256, pad=16):
    """img: HxWx3 uint8 RGB -> 4x uint8 RGB"""
    m = model(); H, W, _ = img.shape
    x = torch.from_numpy(img).permute(2, 0, 1).float().div(255).unsqueeze(0)
    out = torch.zeros(1, 3, H * 4, W * 4)
    with torch.inference_mode():
        for y0 in range(0, H, tile):
            for x0 in range(0, W, tile):
                y1, x1 = min(y0 + tile, H), min(x0 + tile, W)
                py0, px0, py1, px1 = max(y0 - pad, 0), max(x0 - pad, 0), min(y1 + pad, H), min(x1 + pad, W)
                o = m(x[:, :, py0:py1, px0:px1])
                out[:, :, y0 * 4:y1 * 4, x0 * 4:x1 * 4] = o[:, :, (y0 - py0) * 4:(y0 - py0) * 4 + (y1 - y0) * 4,
                                                            (x0 - px0) * 4:(x0 - px0) * 4 + (x1 - x0) * 4]
    return (out[0].clamp(0, 1).permute(1, 2, 0).numpy() * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, "src/art")) if f.endswith(".png"))
    for n in names:
        dst = os.path.join(ROOT, "build/up", n + ".png")
        if os.path.exists(dst): continue
        t = time.time(); a = np.asarray(Image.open(os.path.join(ROOT, "src/art", n + ".png")).convert("RGB"))
        tmp = dst + ".tmp.png"; Image.fromarray(upscale(a)).save(tmp); os.replace(tmp, dst)
        print("up", n, round(time.time() - t), "s", flush=True)
