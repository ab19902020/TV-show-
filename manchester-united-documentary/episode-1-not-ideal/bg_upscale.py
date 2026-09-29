"""4x anime-model upscale of every background canvas used in scenes 1-4 -> build/bg/<name>.png"""
import os, numpy as np
from PIL import Image
import upscale
BG = "../assets/backgrounds/"
USE = {"boardroom": "boardroom/cinematic-football-club-boardroom.png",
       "boardroom_sunset": "boardroom/crimson-executive-boardroom-at-sunset.png",
       "locker_wide": "locker-room/cinematic-red-team-locker-room.png",
       "locker_board": "locker-room/cinematic-red-football-locker-room.png",
       "stadium_dusk": "stadium-exterior/cinematic-stadium-at-crimson-dusk.png",
       "tunnel_pitch": "stadium-tunnel/empty-red-football-tunnel-to-stadium.png",
       "training": "training-ground/animated-football-training-ground.png",
       "corridor": "mixed-zone/empty-stadium-interview-corridor.png",
       "corridor_doors": "mixed-zone/red-and-black-press-corridor.png",
       "tunnel_pitchside": "stadium-tunnel/cinematic-red-stadium-tunnel.png",
       "tunnel_view": "stadium-tunnel/stadium-tunnel-to-the-pitch.png"}
os.makedirs("build/bg", exist_ok=True)
for k, f in USE.items():
    out = f"build/bg/{k}.png"
    if os.path.exists(out): continue
    a = np.asarray(Image.open(BG + f).convert("RGB"))
    Image.fromarray(upscale.upscale(a, "RealESRGAN_x4plus_anime_6B")).save(out)
    print("bg", k, flush=True)
