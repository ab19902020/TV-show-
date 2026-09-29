import sys, numpy as np, torch, spandrel, time
from PIL import Image
torch.set_num_threads(4)
_models = {}
def get(name):
    if name not in _models:
        m = spandrel.ModelLoader().load_from_file(f"models/{name}.pth").eval()
        _models[name] = m
    return _models[name]
def upscale(img, name="RealESRGAN_x4plus_anime_6B", tile=256, pad=16):
    """img: HxWx3 uint8 RGB -> 4x uint8 RGB"""
    m = get(name)
    H, W, _ = img.shape
    x = torch.from_numpy(img).permute(2,0,1).float().div(255).unsqueeze(0)
    out = torch.zeros(1,3,H*4,W*4)
    with torch.inference_mode():
        for y0 in range(0, H, tile):
            for x0 in range(0, W, tile):
                y1, x1 = min(y0+tile, H), min(x0+tile, W)
                py0, px0 = max(y0-pad,0), max(x0-pad,0)
                py1, px1 = min(y1+pad,H), min(x1+pad,W)
                o = m(x[:,:,py0:py1,px0:px1])
                out[:,:,y0*4:y1*4,x0*4:x1*4] = o[:,:,(y0-py0)*4:(y0-py0)*4+(y1-y0)*4,(x0-px0)*4:(x0-px0)*4+(x1-x0)*4]
    return (out[0].clamp(0,1).permute(1,2,0).numpy()*255+0.5).astype(np.uint8)
if __name__ == "__main__":
    src, dst, name = sys.argv[1], sys.argv[2], sys.argv[3]
    t=time.time()
    a = np.asarray(Image.open(src).convert("RGB"))
    Image.fromarray(upscale(a, name)).save(dst)
    print("done", dst, time.time()-t)
