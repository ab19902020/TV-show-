"""The walk rig's cut pieces (thigh | shin | foot | upper body) on magenta, joints marked (hip green, knee cyan, ankle
yellow, toe/heel floor contacts red), the floor line green.  python3 tools/pieces.py out.png rooney_mic_right"""
import sys,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,ROOT)
OUT=os.path.abspath(sys.argv[1]);os.chdir(ROOT)
import numpy as np,cv2
from PIL import Image
from walkrig import WalkRig
n=sys.argv[2];r=WalkRig(n,mirror=n.endswith('right'));ims=[]
for k in ['thigh','shin','foot']:ims.append(r.pieces[k][0].u8[1.])
ims.append(r.upper.u8[1.])
cells=[]
for a in ims:
    al=a[...,3:4]/255.;bg=np.zeros(a.shape[:2]+(3,));bg[:]=(255,0,255);cells.append(a[...,:3]*al+bg*(1-al))
im=np.hstack(cells).astype(np.uint8).copy();W=ims[0].shape[1]
for k in range(4):
    for p,c in [(r.hip,(0,255,0)),(r.knee,(0,200,255)),(r.ank,(255,255,0)),((r.toe_c,r.sole),(255,0,0)),((r.heel_c,r.sole),(255,0,0))]:
        cv2.circle(im,(int(p[0]+k*W),int(p[1])),6,c,-1)
    cv2.line(im,(k*W,int(r.sole)),(k*W+W,int(r.sole)),(0,255,0),1)
Image.fromarray(im[max(0,int(r.hip[1])-200):]).save(OUT);print(OUT)
