"""Build isolated animation pieces from the approved cartoon model sheets."""
from pathlib import Path
import os,json,cv2,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parent
ART=ROOT/'src/art';OUT=ROOT/'build/parts';OUT.mkdir(parents=True,exist_ok=True)
(ROOT/'qa').mkdir(exist_ok=True)
SCALE=3;meta={}

def save(name,a,info):
    target=OUT/(name+'.png');temp=target.with_suffix('.tmp')
    Image.fromarray(a).save(temp,format='PNG');os.replace(temp,target);meta[name]=info

def extract(sh,n,box,mirror=False):
    im=np.asarray(Image.open(ART/f'{sh}.png').convert('RGB'));x0,y0,x1,y1=box
    rgb=im[y0:y1,x0:x1].copy();mn=rgb.min(2);mx=rgb.max(2).astype(float)
    paper=(mn>181)&((mx-mn)<32)
    if n=='fifty_back':
        guard=np.zeros(paper.shape,np.uint8)
        cv2.fillPoly(guard,[np.int32([(35,112),(115,112),(128,211),(22,211)])],1)
        paper[guard.astype(bool)]=False
    lab,_=ndi.label(paper);border=np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]])
    fg=~np.isin(lab,border[border>0]);labels,_=ndi.label(fg)
    sizes=np.bincount(labels.ravel());sizes[0]=0;mask=labels==np.argmax(sizes)
    yy,xx=np.nonzero(mask);a,b,c,d=max(0,xx.min()-2),max(0,yy.min()-2),min(rgb.shape[1],xx.max()+3),min(rgb.shape[0],yy.max()+3)
    rgb=rgb[b:d,a:c];mask=mask[b:d,a:c]
    core=ndi.binary_erosion(mask,iterations=1)
    ix=ndi.distance_transform_edt(~core,return_distances=False,return_indices=True)
    rgb=rgb[ix[0],ix[1]]
    wh=(rgb.shape[1]*SCALE,rgb.shape[0]*SCALE)
    rgb=cv2.resize(rgb,wh,interpolation=cv2.INTER_LANCZOS4)
    alpha=np.clip(cv2.resize(mask.astype(np.float32),wh,interpolation=cv2.INTER_CUBIC),0,1)
    rgba=np.dstack((rgb,np.uint8(alpha*255)))
    if mirror:rgba=rgba[:,::-1].copy()
    save(n,rgba,{'sheet':sh,'off':[int(x0+a),int(y0+b)],'scale':SCALE,'size':list(rgba.shape[1::-1]),'mirror':mirror})

for sh in ['rooney','rio','fifty']:
    hero={'rooney':(13,114,286,823),'rio':(9,111,284,844),'fifty':(8,114,302,808)}[sh]
    front={'rooney':(298,143,454,445),'rio':(297,145,457,458),'fifty':(298,140,455,459)}[sh]
    back={'rooney':(946,143,1083,445),'rio':(939,143,1096,461),'fifty':(940,140,1097,461)}[sh]
    extract(sh,sh+'_front',front);extract(sh,sh+'_back',back)
    if sh!='fifty':
        extract(sh,sh+'_right',hero);extract(sh,sh+'_left',hero,mirror=True)
    else:
        extract(sh,'fifty_right',(465,141,627,459));extract(sh,'fifty_left',(465,141,627,459),mirror=True)
        extract(sh,'fifty_pose_perform',hero)

exprs={
 'rooney':[('neutral',(285,741,415,866)),('grin',(419,741,550,866)),('proud',(553,741,685,866)),('confused',(687,741,821,866)),('laugh',(823,741,961,866)),('awkward',(963,741,1100,866))],
 'rio':[('neutral',(292,758,421,896)),('side',(424,758,556,896)),('confused',(558,758,690,896)),('deadpan',(692,758,824,896)),('laugh',(824,758,960,896)),('awkward',(962,758,1102,896))],
 'fifty':[('neutral',(302,770,428,914)),('grin',(430,770,562,914)),('brow',(563,770,695,914)),('amused',(696,770,829,914)),('laugh',(829,770,963,914)),('shock',(964,770,1101,914))]
}
for sh,items in exprs.items():
    for n,b in items:extract(sh,sh+'_expr_'+n,b)

# Mouth strips retain the exact young Rooney drawing language.
for n,box in {'REST':(27,928,130,990),'A':(136,928,238,990),'E':(243,928,347,990),
              'I':(351,928,453,990),'O':(459,928,560,990),'U':(566,928,667,990),
              'MBP':(672,928,775,990),'FV':(782,928,883,990)}.items():
    im=np.asarray(Image.open(ART/'rooney.png').convert('RGB'));x0,y0,x1,y1=box
    a=im[y0:y1,x0:x1].copy();hh,ww=a.shape[:2]
    # All mouth artwork lies within this lower-face patch; isolated from borders.
    q=np.float32([[.12,.25],[.30,.17],[.70,.17],[.88,.25],[.83,.59],[.69,.80],[.31,.80],[.17,.59]])*[ww,hh]
    mask=np.zeros((hh,ww),np.uint8);cv2.fillPoly(mask,[np.int32(q)],255,lineType=cv2.LINE_AA)
    mask=cv2.GaussianBlur(mask,(0,0),.8)
    rgba=cv2.resize(np.dstack((a,mask)),(ww*3,hh*3),interpolation=cv2.INTER_LANCZOS4)
    save('mouth_'+n,rgba,{'sheet':'rooney','off':[x0,y0],'scale':3,'size':list(rgba.shape[1::-1]),'mirror':False})

for n in ['fifty-beckon','rio-laugh']:
    p=ART/(n+'.png')
    if p.exists():
        a=np.asarray(Image.open(p).convert('RGBA'));ys,xs=np.nonzero(a[...,3]>15)
        x0,y0,x1,y1=max(0,xs.min()-3),max(0,ys.min()-3),min(a.shape[1],xs.max()+4),min(a.shape[0],ys.max()+4)
        a=a[y0:y1,x0:x1]
        info={'sheet':n,'off':[int(x0),int(y0)],'scale':1,'size':list(a.shape[1::-1]),'mirror':False}
        save('fifty_pose_beckon' if n.startswith('fifty') else 'rio_pose_laugh',a,info)
        if n.startswith('fifty'):save('fifty_left',a,info)

# Complete held-microphone poses retain a single native head. Remove the
# generator's faint translucent backdrop while preserving the ink silhouette.
new_poses={
 'fifty-exit':['fifty_exit'],
 'rooney-mic':['rooney_mic_right'],
 'rooney-mic-raised':['rooney_mic_up'],
 'rio-mic':['rio_mic_right','rio_mic_left'],
 'rio-laugh-mic':['rio_pose_laugh_mic'],
}
for src,names in new_poses.items():
    path=ART/(src+'.png')
    if not path.exists():continue
    a=np.asarray(Image.open(path).convert('RGBA')).copy()
    core=a[...,3]>230;labels,count=ndi.label(core);sizes=np.bincount(labels.ravel());sizes[0]=0
    core=labels==np.argmax(sizes)
    # The true figure is opaque; soft background haze has lower alpha.
    aa=np.clip(cv2.GaussianBlur(core.astype(np.float32),(0,0),.55),0,1)
    a[...,3]=np.uint8(aa*255)
    ys,xs=np.nonzero(a[...,3]>15)
    x0,y0,x1,y1=max(0,xs.min()-3),max(0,ys.min()-3),min(a.shape[1],xs.max()+4),min(a.shape[0],ys.max()+4)
    cropped=a[y0:y1,x0:x1]
    for n in names:
        mirror=n.endswith('_left');part=cropped[:,::-1].copy() if mirror else cropped.copy()
        save(n,part,{'sheet':src,'off':[int(x0),int(y0)],'scale':1,'size':list(part.shape[1::-1]),'mirror':mirror})

temp=OUT/'meta.tmp';temp.write_text(json.dumps(meta,indent=2));os.replace(temp,OUT/'meta.json')
cw,ch=180,230;names=list(meta);out=Image.new('RGB',(cw*6,((len(names)+5)//6)*ch),'#344252');d=ImageDraw.Draw(out)
for i,n in enumerate(names):
    a=Image.open(OUT/(n+'.png'));a.thumbnail((cw-10,ch-28));x=(i%6)*cw+(cw-a.width)//2;y=(i//6)*ch
    out.paste(a,(x,y),a);d.text(((i%6)*cw+4,y+ch-23),n,fill='white')
out.save(ROOT/'qa/parts.jpg',quality=94)
print('Prepared',len(meta),'new cartoon cutouts',flush=True)
