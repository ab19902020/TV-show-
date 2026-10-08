"""ChatGPT director's polish for The White Pelé, layered over Claude's v3.

Called by direction.py before `finish(SH, ...)`: no source assets or audio are replaced.
Five short concert inserts preserve the complete 177.520-second timeline; the
original shot resumes after each insert. All poses and instruments already
exist in Claude's v3 project. This is source code, not a claimed final render.
"""
from copy import deepcopy


def apply(namespace):
    """Mutate the completed raw shot list before frame-boundary normalization."""
    shots = namespace["SH"]
    make = namespace["S_"]
    move = namespace["move"]
    frame = namespace["frame"]
    pub2 = namespace["pub2"]
    st8 = namespace["st8"]
    b = namespace["b"]
    originals = list(shots)

    # Five *additional* on-beat musical cutaways. The original shot comes back
    # after <1 second so Rooney's lead vocal and the story are not interrupted.
    inserts = (
        (14.38, "sesko", "B02", 0.78),
        (15.82, "maguire", "B02", 0.78),
        (90.68, "cunha", "B08", 0.88),
        (118.18, "maguire", "B08", 0.78),
        (159.12, "sesko", "B08", 0.88),
    )
    for t, musician, plate, duration in inserts:
        active = max((s for s in originals if s["t"] <= t),
                     key=lambda s: s["t"], default=None)
        if active is None or active["plate"] != plate:
            raise ValueError(f"Band insert at {t:.2f}s requires {plate}; inspect the baseline shot list")
        band = namespace["BAND2"] if plate == "B02" else namespace["BAND8"]
        focus = next(a for a in band if a["who"] == musician)
        blur = {a["who"]: (0.0 if a["who"] == musician else 5.5) for a in band}
        layers = pub2(blur=blur) if plate == "B02" else st8(blur=blur)
        cam = frame(focus["feet"], focus["h"], "mcu", dy=-0.06)
        # Keep the instrument visible and avoid a sudden 10x close-up.
        cam = (cam[0], cam[1], min(cam[2], 3.7))
        end_cam = (cam[0] + 7, cam[1] - 4, cam[2] * 1.065)
        settings = dict(namespace["VERSE"] if plate == "B02" else namespace["CHORUS"])
        settings.update(drift=1.15, blur=1.1, polish_lights=True,
                        band_insert=musician, flash=min(settings.get("flash", 0), 0.85))
        inserts_shot = make(t, plate, move(t, t + duration, cam, end_cam), layers, **settings)
        restore = deepcopy(active)
        restore["t"] = t + duration
        shots.extend((inserts_shot, restore))

    # Give Goldbridge a performance change inside his v3 selfie close-up
    # using only drawings already in the repository (no invented phone sprite).
    for shot in originals:
        if abs(shot["t"] - b(98)) < 0.04:
            for kind, group in shot.get("layers", []):
                if kind == "actors" and isinstance(group, list):
                    for actor in group:
                        if actor["who"] == "mark":
                            actor["keys"] = [(shot["t"], "mark-goldbridge:shouting"),
                                             (shot["t"] + 0.38, "mark-goldbridge:cheer"),
                                             (shot["t"] + 0.81, "mark-goldbridge:shouting")]
                            actor["look_cam"] = True
                            actor["dance"] = 1.2
            shot["drift"] = 2.35
            shot["rec_flash"] = [shot["t"] + 0.16, shot["t"] + 0.95]

        # Stadium and pub-performance beams now get a subtle beat-driven
        # lift in camera.py, not an indiscriminate full-screen strobe.
        if (shot["plate"] in ("B01", "B02", "B08")
                and isinstance(shot.get("lights"), (int, float))
                and shot["lights"] > 0.9):
            shot["polish_lights"] = True
            shot["beams"] = min(2.15, float(shot.get("beams", 0)) * 1.12)

    shots.sort(key=lambda shot: shot["t"])
    return len(inserts)
