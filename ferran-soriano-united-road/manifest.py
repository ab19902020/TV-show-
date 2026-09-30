"""The sprite manifest: every sprite the film is drawn from, with its source image and rectangle, pivots, scale,
z-order, gesture and mouth / expression identity. World units = gesture-sheet px of pose G07, origin at its collar
point; z-order back to front: room 0, master head 1 (its mouth, eyes and brows 1.1-1.3), body 2, forearms 3.

-> sprite_manifest.json"""
import json
from parts import SPEC

GEST = {"g01": "G01 palms up explaining", "g02": "G02 shrug", "g03": "G03 one point (index finger)",
        "g04": "G04 hold on (both palms forward)", "g05": "G05 counting", "g06": "G06 arms folded (compound)",
        "g07": "G07 clasped hands (compound, default)", "g08": "G08 dismissive"}

def main():
    parts = json.load(open("build/parts/meta.json"))
    bodies = json.load(open("build/rig/bodies.json"))
    arms = json.load(open("build/rig/arms.json"))
    head = json.load(open("build/rig/head.json"))
    hp = json.load(open("build/rig/head_place.json"))["main_to_world"]
    mouths = json.load(open("build/rig/mouths.json"))
    sets = json.load(open("build/set.json"))
    from arms import ARMS
    out = []
    out.append({"sprite": "master_head", "file": "build/rig/head.png", "source": "src/main.png",
                "source_rect": [round(v, 1) for v in (head["off"][0], head["off"][1], head["off"][0] + head["size"][0] / 4,
                                                       head["off"][1] + head["size"][1] / 4)],
                "scale": {"px_per_source_px": 4, "source_to_world": hp},
                "pivot": {"neck_source": [440, 392]}, "z": 1,
                "identity": "the one head on every pose and camera; own mouth painted out, neck plug under the collar"})
    for s in mouths["shapes"]:
        base = {"FV": "I", "TH": "E", "L": "A"}.get(s, s)
        out.append({"sprite": f"mouth_{s}", "file": f"build/rig/mouth_{s}.png", "source": "src/main.png",
                    "source_rect": SPEC["mouth_" + base]["box"], "anchor_head_px": mouths["origin"], "z": 1.1,
                    "identity": f"mouth {s}" + ("" if s == base else f" (made from {base})")
                                + (" - also M/B/P" if s == "REST" else "")})
    out.append({"sprite": "eyes", "file": "build/rig/eyes.npz", "source": "src/main.png (master head)", "z": 1.2,
                "identity": "irises move inside the drawn lids (gaze); lids drawn down for half blinks and blinks"})
    out.append({"sprite": "brows", "file": "(cut from build/rig/head_nomouth.png at run time)", "z": 1.3,
                "identity": "each brow a layer that lifts / arches / frowns over painted-in lid skin"})
    for n, p in bodies["poses"].items():
        f = f"build/rig/{n}_base.png" if n in arms else f"build/rig/body_{n}.png"
        out.append({"sprite": f"body_{n}", "file": f, "source": "src/gestures.png", "source_rect": SPEC[n]["box"],
                    "scale": {"px_per_world_unit": 8, "sheet_to_world": p["sheet_to_g07"], "world_origin_of_png": p["origin"]},
                    "z": 2, "gesture": GEST[n],
                    "identity": "own head removed above the collar; forearms cut free and refilled" if n in arms
                                else "complete drawing (compound pose); own head removed above the collar"})
        for side, info in arms.get(n, {}).items():
            spec = ARMS[n][side]
            out.append({"sprite": f"{n}_{side}", "file": f"build/rig/{n}_{side}.png", "source": "src/gestures.png",
                        "source_polygon": spec["sleeve"], "hand_seed": spec["hand"],
                        "pivot": {"elbow_sheet": spec["elbow"], "wrist_sheet": spec["wrist"],
                                  "elbow_world": [round(v, 2) for v in info["elbow"]], "wrist_world": [round(v, 2) for v in info["wrist"]]},
                        "scale": {"px_per_world_unit": 8}, "z": 3, "gesture": GEST[n],
                        "identity": ("his right" if side == "R" else "his left") + " forearm and hand"})
    out.append({"sprite": "combo_r1", "z": 2, "gesture": "G01 one palm up (his right), left hand resting",
                "identity": "body_g01 + g01_R + g03_L attached at g01's left elbow"})
    out.append({"sprite": "combo_l1", "z": 2, "gesture": "G01 one palm up (his left), right hand resting",
                "identity": "body_g01 + g01_L + g03_L mirrored, attached at g01's right elbow"})
    for k in ("portrait", "landscape"):
        out.append({"sprite": f"room_{k}", "file": f"build/set_{k}.png", "source": f"src/room_{k}.png (from src/rooms.png)",
                    "world_rect": sets[k]["rect"], "scale": {"px_per_world_unit": round(sets[k]["px"], 3)}, "z": 0,
                    "identity": "the supplied media-room background, lens-blurred by shot"})
    json.dump(out, open("sprite_manifest.json", "w"), indent=1)
    print(len(out), "sprites")

if __name__ == "__main__":
    main()
