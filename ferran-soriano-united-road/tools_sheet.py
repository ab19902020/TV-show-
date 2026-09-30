"""Review sheet: render frames at the given times into one contact sheet (one process, rig loaded once).
  python3 tools_sheet.py portrait out.jpg 0.6 8.8 9.8 ...     [--scale 0.25] [--cols 6]"""
import sys, numpy as np, cv2
import render

def main():
    orient, out = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    scale, cols = 0.25, 6
    if "--scale" in args: i = args.index("--scale"); scale = float(args[i + 1]); del args[i:i + 2]
    if "--cols" in args: i = args.index("--cols"); cols = int(args[i + 1]); del args[i:i + 2]
    times = [float(a) for a in args]
    tiles = []
    for t in times:
        f = render.frame(int(round(t * render.FPS)), orient)
        f = cv2.resize(f, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        f = np.ascontiguousarray(f)
        cv2.putText(f, f"{t:.2f}", (6, f.shape[0] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1, cv2.LINE_AA)
        tiles.append(f)
    while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(out, cv2.cvtColor(np.vstack(rows), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])

if __name__ == "__main__":
    main()
