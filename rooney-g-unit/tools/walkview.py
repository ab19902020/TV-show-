"""One walker's leg rig in isolation, big, over a step cycle (magenta background, grey floor line at the sole).
python3 tools/walkview.py out.jpg rooney_mic_right [--n 12] [--cycles 1] [--feet] [--h 900]"""
import sys,os,argparse,math
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,ROOT)
OUT=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else None;os.chdir(ROOT)
import cv2,numpy as np
from PIL import Image,ImageDraw
import engine as E
from walkrig import WalkRig
p=argparse.ArgumentParser();p.add_argument('out');p.add_argument('name');p.add_argument('--n',type=int,default=12)
p.add_argument('--cycles',type=float,default=1);p.add_argument('--feet',action='store_true');p.add_argument('--h',type=int,default=900)
p.add_argument('--stride',type=float,default=.37);a=p.parse_args()
mirror=a.name.endswith('right');r=WalkRig(a.name,mirror=mirror)
s=a.h/E.part(a.name).shape[0];step=r.leglen*a.stride
cells=[]
for i in range(a.n):
    dist=a.cycles*2*step*s*i/a.n
    Wc,Hc=int(a.h*.75),int(a.h*1.1);d=np.zeros((Hc,Wc,3),np.float32);d[:]=(1,0,1)
    floor=Hc-40;x=Wc*.5
    cv2.line(d,(0,floor),(Wc,floor),(.4,.4,.4),1)
    M=E.T(x,floor)@np.diag([-s if mirror else s,s,1.])@E.T(-r.hip[0],-r.sole)
    joints,drop=r.pose(dist/s,step,0,moving=1)
    for q in r.layers(joints,drop,M,0,lean=0):E.over(d,q.d.base(1),q.M)
    im=np.uint8(np.clip(d*255,0,255))
    if a.feet:im=im[int(Hc*.55):,:]
    cells.append(Image.fromarray(im))
cols=min(6,len(cells));w,h=cells[0].size;sc=min(1.,1800/(w*cols));w2,h2=int(w*sc),int(h*sc)
out=Image.new('RGB',(w2*cols,(h2+16)*math.ceil(len(cells)/cols)),'#222');dr=ImageDraw.Draw(out)
for i,c in enumerate(cells):
    x=(i%cols)*w2;y=(i//cols)*(h2+16);out.paste(c.resize((w2,h2)),(x,y));dr.text((x+4,y+h2+2),f'{i}/{a.n}',fill='white')
out.save(OUT,quality=92);print(OUT)
