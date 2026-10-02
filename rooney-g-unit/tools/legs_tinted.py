"""Big close-up of a walker's legs at a few phases (far leg tinted red, near leg green) to check hips and knees.
python3 tools/legs_tinted.py out.png rooney_mic_right [phases...]"""
import sys,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,ROOT)
OUT=os.path.abspath(sys.argv[1]);os.chdir(ROOT)
import numpy as np,cv2
from PIL import Image
import engine as E
from walkrig import WalkRig
n=sys.argv[2];ph=[float(v) for v in sys.argv[3:]] or [0,.25,.5,.75]
mirror=n.endswith('right');r=WalkRig(n,mirror=mirror);s=2000/E.part(n).shape[0];step=r.leglen*.37;out=[]
for p in ph:
    Wc,Hc=1100,2150;d=np.zeros((Hc,Wc,3),np.float32);d[:]=(1,0,1);floor=Hc-30
    M=E.T(550,floor)@np.diag([-s if mirror else s,s,1.])@E.T(-r.hip[0],-r.sole)
    joints,drop=r.pose(p*2*step,step,0,moving=1);L=r.layers(joints,drop,M,0,lean=0)
    for i,q in enumerate(L):
        b=q.d.base(1).copy()
        if i<6:b[...,:3]=np.minimum(1,b[...,:3]+np.float32((.25,0,0) if i<3 else (0,.18,0))*b[...,3:4])
        E.over(d,b,q.M)
    out.append(np.uint8(np.clip(d*255,0,255))[950:,:])
Image.fromarray(np.hstack(out)).save(OUT);print(OUT)
