"""Render a 30 fps portrait MP4 against the complete original recording."""
from pathlib import Path
import os,math,subprocess,argparse,time,json
from concurrent.futures import ProcessPoolExecutor,as_completed
from PIL import Image,ImageDraw
import cv2
from engine import Scene,SHOTS,PHONEMES

ROOT=Path(__file__).resolve().parent
for name in ['build','output','qa']:(ROOT/name).mkdir(parents=True,exist_ok=True)
FPS=30;DURATION=36.488;NFRAMES=math.ceil(FPS*DURATION)

def chunk(job):
    idx,start,end,width=job
    os.chdir(ROOT);cv2.setNumThreads(1)
    scene=Scene(width);dest=ROOT/'build'/f'chunk-{width}-{idx:02d}.mp4'
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{scene.oh}',
         '-r',str(FPS),'-i','-','-an','-c:v','libx264','-threads','2','-preset','fast',
         '-crf','18','-pix_fmt','yuv420p',str(dest)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for f in range(start,end):p.stdin.write(scene.render(f/FPS).tobytes())
    finally:p.stdin.close()
    if p.wait()!=0:raise RuntimeError(f'ffmpeg failed: {dest}')
    return idx,str(dest),end-start

def render(width):
    jobs=[(i,s,min(s+150,NFRAMES),width) for i,s in enumerate(range(0,NFRAMES,150))]
    done={};total=0;begin=time.time()
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(chunk,j) for j in jobs]
        for future in as_completed(futures):
            idx,path,n=future.result();done[idx]=path;total+=n
            print(f'Rendered {total}/{NFRAMES} frames ({time.time()-begin:.0f}s)',flush=True)
    concat=ROOT/'build'/f'concat-{width}.txt'
    concat.write_text(''.join(f"file '{done[i]}'\n" for i in sorted(done)))
    output=ROOT/'output'/f'Rooney-G-Unit-Cartoon-{width}x{width*16//9}.mp4'
    # Retain the original stream start offset and entire recording. No sound edits.
    subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),
                    '-i',str(ROOT/'src/audio/original.webm'),'-map','0:v:0','-map','1:a:0',
                    '-c:v','copy','-c:a','aac','-b:a','320k','-t',str(DURATION),
                    '-movflags','+faststart',str(output)],check=True)
    print('OUTPUT',output,flush=True)

def contact(width=270):
    cv2.setNumThreads(1);scene=Scene(width)
    times=[.5,2.2,4.5,7.1,9,11.7,13.5,15.1,16.8,18.6,20.3,22.1,
           23.6,24.9,26.7,27.95,28.8,30.25,31.83,32.56,33.27,33.8,34.65,35.7]
    out=Image.new('RGB',(width*6,(scene.oh+30)*4),'#1b2028');draw=ImageDraw.Draw(out)
    for i,t in enumerate(times):
        x=(i%6)*width;y=(i//6)*(scene.oh+30)
        out.paste(Image.fromarray(scene.render(t)),(x,y));draw.text((x+8,y+scene.oh+7),f'{t:.2f} sec',fill='white')
    dest=ROOT/'qa/contact.jpg';out.save(dest,quality=92);print(dest)

if __name__=='__main__':
    os.chdir(ROOT)
    p=argparse.ArgumentParser();p.add_argument('--width',type=int,default=1080);p.add_argument('--contact',action='store_true')
    p.add_argument('--frame',type=float);args=p.parse_args()
    if args.contact:contact()
    elif args.frame is not None:
        cv2.setNumThreads(1);im=Scene(args.width).render(args.frame)
        path=ROOT/'qa'/f'frame-{args.frame:.3f}.png';Image.fromarray(im).save(path);print(path)
    else:render(args.width)
