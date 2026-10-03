"""Review consecutive frames: python3 tools/strip.py out.jpg T0 T1 [--step 1] [--crop x0,y0,x1,y1] [--width 1080] [--cols 6]
Crop coordinates are output pixels at --width. Labels show the time of each frame."""
import sys,os,argparse,math
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,ROOT)
OUT=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else None;os.chdir(ROOT)
import cv2,numpy as np
from PIL import Image,ImageDraw
from engine import Scene
p=argparse.ArgumentParser();p.add_argument('out');p.add_argument('t0',type=float);p.add_argument('t1',type=float)
p.add_argument('--step',type=int,default=1);p.add_argument('--crop');p.add_argument('--width',type=int,default=1080)
p.add_argument('--cols',type=int,default=6);p.add_argument('--cell',type=int,default=300);a=p.parse_args()
cv2.setNumThreads(2);sc=Scene(a.width)
frames=list(range(int(round(a.t0*30)),int(round(a.t1*30))+1,a.step))
ims=[]
for f in frames:
    im=sc.render(f/30)
    if a.crop:x0,y0,x1,y1=map(int,a.crop.split(','));im=im[y0:y1,x0:x1]
    ims.append(Image.fromarray(im))
w=a.cell;h=int(round(ims[0].height*w/ims[0].width));cols=min(a.cols,len(ims));rows=math.ceil(len(ims)/cols)
out=Image.new('RGB',(w*cols,(h+18)*rows),'#111');d=ImageDraw.Draw(out)
for i,(f,im) in enumerate(zip(frames,ims)):
    x=(i%cols)*w;y=(i//cols)*(h+18);out.paste(im.resize((w,h),Image.Resampling.LANCZOS),(x,y));d.text((x+4,y+h+3),f'{f/30:.3f}',fill='white')
out.save(OUT,quality=92);print(OUT,len(ims))
