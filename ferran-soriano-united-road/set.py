"""The room behind him: the two drawn backgrounds supplied for this film (src/rooms.png: a portrait panel and a
landscape panel of the same glass-walled media room: pale-blue panel frame left, window wall, planters, a light
strip). Each panel is cut from the sheet inside its frame line, upscaled 4x (clean-line model) and placed in world
units behind him so shot A of its own format is filled with a little to spare; tighter shots see less of it,
larger, with more lens blur (render.py).

-> build/set_portrait.png, build/set_landscape.png, build/set.json (world rect of each plate, px per unit)"""
import json, os, cv2

# world rects (x0, y0, x1, y1): portrait shot A is x +-148, y -272..254; landscape A is x -438..344, y -265..175
RECT = {"portrait": (-155.0, -290.0, 155.0, None), "landscape": (-456.0, -272.0, 364.0, None)}

if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    meta = {}
    for kind, (x0, y0, x1, _) in RECT.items():
        im = cv2.imread(f"src/room_{kind}_x4.png")
        h, w = im.shape[:2]
        px = w / (x1 - x0)
        y1 = y0 + h / px
        cv2.imwrite(f"build/set_{kind}.png", im)
        meta[kind] = {"rect": [x0, y0, x1, y1], "size": [w, h], "px": px}
        print(kind, im.shape, "px/unit %.2f" % px, "rect", [x0, y0, x1, round(y1, 1)])
    json.dump(meta, open("build/set.json", "w"), indent=1)
