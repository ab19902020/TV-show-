"""4x AI upscale (Real-ESRGAN x4plus-anime via spandrel + torch, CPU).

    python3 tools/ep/upscale.py in.png out.png

The model downloads from the Real-ESRGAN GitHub release into models/ on first use.
Not needed to render: the upscaled images are kept in episode/x4 and episode/characters_x16.
"""
import os, subprocess, sys
import cv2, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL = os.path.join(ROOT, 'models', 'RealESRGAN_x4plus_anime_6B.pth')
URL = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth'
_M = []


def model():
    if not _M:
        import torch, spandrel
        torch.set_num_threads(os.cpu_count() or 4)
        if not os.path.exists(MODEL):
            os.makedirs(os.path.dirname(MODEL), exist_ok=True)
            subprocess.run(['curl', '-sSL', '-o', MODEL, URL], check=True)
        _M.append(spandrel.ModelLoader().load_from_file(MODEL).eval())
    return _M[0]


def upscale(bgr, tile=256, pad=16):
    """HxWx3 uint8 BGR -> 4x uint8 BGR."""
    import torch
    m = model()
    img = np.ascontiguousarray(bgr[..., ::-1])
    H, W, _ = img.shape
    x = torch.from_numpy(img).permute(2, 0, 1).float().div(255).unsqueeze(0)
    out = torch.zeros(1, 3, H * 4, W * 4)
    with torch.inference_mode():
        for y0 in range(0, H, tile):
            for x0 in range(0, W, tile):
                y1, x1 = min(y0 + tile, H), min(x0 + tile, W)
                py0, px0, py1, px1 = max(y0 - pad, 0), max(x0 - pad, 0), min(y1 + pad, H), min(x1 + pad, W)
                o = m(x[:, :, py0:py1, px0:px1])
                out[:, :, y0 * 4:y1 * 4, x0 * 4:x1 * 4] = \
                    o[:, :, (y0 - py0) * 4:(y0 - py0 + y1 - y0) * 4, (x0 - px0) * 4:(x0 - px0 + x1 - x0) * 4]
    res = (out[0].clamp(0, 1).permute(1, 2, 0).numpy() * 255 + 0.5).astype(np.uint8)
    return np.ascontiguousarray(res[..., ::-1])


if __name__ == '__main__':
    cv2.imwrite(sys.argv[2], upscale(cv2.imread(sys.argv[1], cv2.IMREAD_COLOR)))
    print(sys.argv[2], flush=True)
