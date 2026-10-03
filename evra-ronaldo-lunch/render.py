"""Render the film: 1080 x 1920, 30 fps, in parallel chunks, then mux the original recording (untouched, from the start).
python3 render.py [--width 1080] [--jobs 4] [--out evra_ronaldo_lunch.mp4] [--from T --to T]"""
import os, sys, math, subprocess, argparse, time
from concurrent.futures import ProcessPoolExecutor, as_completed
ROOT = os.path.dirname(os.path.abspath(__file__)); os.chdir(ROOT); sys.path.insert(0, ROOT)
FPS = 30


def chunk(job):
    i, f0, f1, width = job
    import cv2, gc; cv2.setNumThreads(1)
    import cast, engine
    from direction import Film
    # a chunk is 2 s (one to three shots): keep only the rigged drawings it uses, or a worker that has drawn the whole
    # film holds every drawing at 4x with its mip levels (several GB) and the machine runs out of memory
    cast.actor.cache_clear(); engine.part.cache_clear(); gc.collect()
    film = Film(width); oh = width * 16 // 9
    out = os.path.join(ROOT, 'build/render', f'part{width}_{i:03d}.mp4')
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{width}x{oh}', '-r', str(FPS),
                          '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out],
                         stdin=subprocess.PIPE)
    for f in range(f0, f1): p.stdin.write(film.render(f / FPS).tobytes())
    p.stdin.close(); assert p.wait() == 0, out
    return i, out, f1 - f0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--width', type=int, default=1080); ap.add_argument('--jobs', type=int, default=3)
    ap.add_argument('--out', default='evra_ronaldo_lunch.mp4'); ap.add_argument('--from', dest='t0', type=float, default=0.)
    ap.add_argument('--to', dest='t1', type=float, default=None); a = ap.parse_args()
    from direction import DUR
    os.makedirs('build/render', exist_ok=True)
    F0 = int(round(a.t0 * FPS)); F1 = int(math.ceil((a.t1 or DUR) * FPS)); step = 60
    jobs = [(i, f, min(f + step, F1), a.width) for i, f in enumerate(range(F0, F1, step))]
    done = {}; n = 0; t = time.time()
    with ProcessPoolExecutor(a.jobs) as ex:
        for fut in as_completed([ex.submit(chunk, j) for j in jobs]):
            i, out, k = fut.result(); done[i] = out; n += k
            print(f'{n}/{F1 - F0} frames, {time.time() - t:.0f}s', flush=True)
    lst = os.path.join(ROOT, 'build/render/list.txt')
    open(lst, 'w').write(''.join(f"file '{done[i]}'\n" for i in sorted(done)))
    # the original recording, from the same start, encoded once (AAC 320k)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-ss', str(a.t0), '-i', 'src/audio/original.flac',
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-shortest',
                    '-movflags', '+faststart', a.out], check=True)
    print('done ->', a.out)
