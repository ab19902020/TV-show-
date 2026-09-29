"""Join the 4K render chunks (build/k4_part*.mp4) into the Scenes 1-2 master.

Each chunk's first frame comes from its name / the render logs (START below); its length is counted with ffprobe,
so chunks cut short (e.g. a process killed for memory) are detected. Any missing frame range is rendered now,
then the pieces are concatenated in order and muxed with the mix.
  python3 assemble.py -> episode1_scenes1-2_4k.mp4 and episode1_scenes1-2_1080p.mp4 (< 100 MB)"""
import glob, os, re, subprocess, json
import perf

N = int(round(perf.M["title_end"] * 30))
START = {"k4_part0.mp4": 0, "k4_part0b.mp4": 1079, "k4_part1.mp4": 1480, "k4_part1a.mp4": 1480, "k4_part1b.mp4": 2220,
         "k4_part2.mp4": 2960, "k4_part3.mp4": 4440}


def frames(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_read_packets", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()
    return int(out or 0)


def pieces():
    ps = []
    for f in sorted(glob.glob("build/k4_*.mp4")):
        n = os.path.basename(f)
        if n not in START and not n.startswith("k4_gap"): continue
        s = START.get(n) if n in START else int(re.findall(r"k4_gap(\d+)", n)[0])
        c = frames(f)
        if c: ps.append((s, s + c, f))
    return sorted(ps)


def plan(ps):
    """cover [0, N) with pieces, preferring earlier-starting / longer ones; return (segments, gaps)"""
    segs, t, gaps = [], 0, []
    while t < N:
        cands = [p for p in ps if p[0] <= t < p[1]]
        if not cands:
            nxt = min([p[0] for p in ps if p[0] > t] + [N])
            gaps.append((t, nxt)); t = nxt; continue
        s, e, f = max(cands, key=lambda p: p[1])
        segs.append((f, t - s, e - s)); t = e
    return segs, gaps


if __name__ == "__main__":
    ps = pieces()
    segs, gaps = plan(ps)
    for a, b in gaps:
        print("rendering gap", a, b, flush=True)
        subprocess.run(["python3", "render.py", "chunk", str(a), str(b), f"build/k4_gap{a}.mp4"], check=True)
    if gaps:
        segs, gaps = plan(pieces())
    assert not gaps, gaps
    print(json.dumps(segs, indent=1))
    # trim every piece to its used frame range (re-encoded losslessly-close), then concat
    lst = []
    for k, (f, i0, i1) in enumerate(segs):
        out = f"build/seg{k}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f, "-vf", f"select='between(n\\,{i0}\\,{i1 - 1})',setpts=N/30/TB",
                        "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p",
                        "-x264-params", "rc-lookahead=12", out], check=True)
        lst.append(out)
    open("build/segs.txt", "w").write("".join(f"file '{os.path.basename(x)}'\n" for x in lst))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "build/segs.txt",
                    "-i", "build/scenes12_audio.wav", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow",
                    "-crf", "18", "-pix_fmt", "yuv420p", "-x264-params", "rc-lookahead=20", "-c:a", "aac", "-b:a", "256k",
                    "-shortest", "-movflags", "+faststart", "episode1_scenes1-2_4k.mp4"], check=True)
    # the repo / chat copy: 1080p, two-pass to ~88 MB
    dur = perf.M["title_end"]
    vbit = int((88 * 8 * 1024 * 1024) / dur - 192000)
    for p in (1, 2):
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", "episode1_scenes1-2_4k.mp4", "-vf", "scale=1920:1080:flags=lanczos",
               "-c:v", "libx264", "-preset", "slow", "-b:v", str(vbit), "-pass", str(p), "-passlogfile", "build/x264pass",
               "-pix_fmt", "yuv420p"]
        cmd += (["-an", "-f", "mp4", "/dev/null"] if p == 1 else
                ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "episode1_scenes1-2_1080p.mp4"])
        subprocess.run(cmd, check=True)
    for f in ("episode1_scenes1-2_4k.mp4", "episode1_scenes1-2_1080p.mp4"):
        print(f, round(os.path.getsize(f) / 1e6, 1), "MB", frames(f), "frames")
