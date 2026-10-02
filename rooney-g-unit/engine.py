"""Complete cartoon rebuild using the selected model sheets and new arena art.

Rigid cutout parts and planted-foot IK. Expression patches stay inside each
character's original head silhouette so collars and head/body joins remain intact.
"""
from pathlib import Path
from functools import lru_cache
import json,math,cv2,numpy as np
from PIL import Image
from scipy import ndimage as ndi
from reference_face import Face
import performance as perf
import lights as LX
import crowd as CR

ROOT=Path(__file__).resolve().parent
W,H=941,1672;LEVELS=(1.,.5,.25)
META=json.loads((ROOT/'build/parts/meta.json').read_text())
def T(x,y):return np.array([[1.,0,x],[0,1.,y],[0,0,1.]])
def S(s):return np.diag([s,s,1.])
def R(a):
    c,s=math.cos(math.radians(a)),math.sin(math.radians(a));return np.array([[c,-s,0],[s,c,0],[0,0,1.]])
def pivot(x,y,a):return T(x,y)@R(a)@T(-x,-y)
def smooth(u):u=np.clip(u,0,1);return u*u*(3-2*u)
def pm(a):
    x=a.astype(np.float32)/(255 if a.dtype==np.uint8 else 1);x=x.copy();x[...,:3]*=x[...,3:4];return x
@lru_cache(None)
def part(n):return np.asarray(Image.open(ROOT/'build/parts'/f'{n}.png').convert('RGBA')).copy()
def pxy(n,x,y):
    m=META[n];xx=(x-m['off'][0])*m['scale'];yy=(y-m['off'][1])*m['scale']
    if m.get('mirror'):xx=m['size'][0]-1-xx
    return float(xx),float(yy)
def over(dst,src,M):
    h,w=src.shape[:2];oh,ow=dst.shape[:2]
    q=M@np.array([[0,w,w,0],[0,0,h,h],[1,1,1,1.]])
    x0=max(0,int(np.floor(q[0].min()))-2);x1=min(ow,int(np.ceil(q[0].max()))+2)
    y0=max(0,int(np.floor(q[1].min()))-2);y1=min(oh,int(np.ceil(q[1].max()))+2)
    if x1<=x0 or y1<=y0:return
    a=cv2.warpAffine(src,(T(-x0,-y0)@M)[:2],(x1-x0,y1-y0),flags=cv2.INTER_LINEAR)
    roi=dst[y0:y1,x0:x1];roi[:]=a[...,:3]+roi*(1-a[...,3:4])

class Sprite:
    def __init__(self,a):
        self.im=pm(a);self.h,self.w=self.im.shape[:2];self.levels={1.:self.im}
        for k in [.5,.25,.125]:self.levels[k]=cv2.resize(self.im,None,fx=k,fy=k,interpolation=cv2.INTER_AREA)
    def draw(self,dst,M):
        k=float(np.linalg.norm(M[:2,0]));L=1 if k>=.5 else (.5 if k>=.25 else (.25 if k>=.125 else .125))
        over(dst,self.levels[L],M@S(1/L))

# Sheet coordinates: head, neck, eye-height search interval, mouth anchor and width.
CONFIG={
 'rooney_front':((329,146,434,258),(381,252),(186,218),(381,225,36)),
 'rooney_right':((39,119,274,353),(163,340),(198,252),(185,272,74)),
 'rooney_left':((39,119,274,353),(163,340),(198,252),(185,272,74)),
 'rio_front':((323,145,434,284),(378,276),(190,230),(380,248,36)),
 'rio_right':((60,114,246,374),(164,360),(190,255),(189,283,59)),
 'rio_left':((60,114,246,374),(164,360),(190,255),(189,283,59)),
 'fifty_front':((317,141,443,289),(378,280),(195,224),(379,235,37)),
 'fifty_right':((492,141,616,289),(552,278),(195,224),(557,235,36)),
 'fifty_left':((346,36,783,488),(594,472),(240,321),(525,351,130)),
 'fifty_exit':((341,22,771,488),(590,455),(218,301),(590,343,140)),
 'rooney_mic_right':((265,38,724,535),(535,515),(213,316),(586,352,145)),
 'rooney_mic_up':((265,38,724,505),(535,515),(213,316),(586,352,145)),
 'rio_mic_right':((335,24,665,475),(508,453),(183,264),(563,327,100)),
 'rio_mic_left':((335,24,665,475),(508,453),(183,264),(563,327,100)),
}
BLINKS={'rooney':[4.7,9.85,14.6,16.85,20.95,24.1,26.25,30.35,35.8],
        'rio':[3.95,7.7,11.1,15.4,19.7,23.6,28.55,33.05],
        'fifty':[2.2,7.2,10.55,12.3,20.5,34.6]}
def blink(n,t):return perf.blink(n,t)

# Native closed-mouth landmarks: every face keeps its own nose, cheek and jaw.
FACE_MARKS={
 'rooney_right':([(149,269),(221,260),(185,274)],317),
 'rooney_left':([(149,269),(221,260),(185,274)],317),
 'rooney_front':([(362,223),(399,221),(381,225)],248),
 'rio_right':([(162,284),(209,276),(189,283)],333),
 'rio_left':([(162,284),(209,276),(189,283)],333),
 'rio_front':([(363,247),(394,246),(379,249)],270),
 'fifty_front':([(363,235),(395,235),(379,235)],251),
 'fifty_right':([(542,235),(573,235),(557,236)],254),
 'fifty_exit':([(531,343),(645,333),(590,349)],427),
 'rooney_mic_right':([(510,353),(650,338),(585,361)],465),
 'rooney_mic_up':([(510,353),(650,338),(585,361)],465),
 'rio_mic_right':([(516,330),(611,315),(564,327)],410),
 'rio_mic_left':([(516,330),(611,315),(564,327)],410),
}

# Free hands extend below the hips in these new held-microphone drawings.
# Keep them with the torso rather than accidentally cutting them into a leg.
ARM_GUARDS={
 'rooney_mic_right':[
  [(692,704),(787,712),(815,918),(826,998),(805,1067),(760,1080),(711,1054),(706,1009),(737,985),(740,925),(704,850),(686,817)]
 ],
 'rio_mic_right':[
  [(664,760),(745,757),(757,861),(773,930),(766,1009),(742,1043),(699,1050),(664,1021),(660,974),(676,941),(679,884)]
 ],
 'fifty_exit':[
  [(328,720),(408,724),(410,827),(375,850),(392,885),(393,917),(366,952),(323,966),(286,951),(281,908),(314,816)],
  [(731,722),(818,744),(849,866),(850,921),(816,965),(799,1010),(740,1001),(684,977),(694,938),(726,905),(731,827)]
 ],
}

def eyes_in(a,y0,y1):
    h,w=a.shape[:2];mask=((a[...,:3].min(2)>193)&(a[...,3]>180)).astype(np.uint8)
    mask[:max(0,int(y0))]=0;mask[min(h,int(y1)):]=0
    count,l,stats,cents=cv2.connectedComponentsWithStats(mask)
    candidates=[i for i in range(1,count) if stats[i,4]>max(5,w*h*.00012) and stats[i,2]<w*.38 and stats[i,3]<h*.2]
    candidates=sorted(candidates,key=lambda i:stats[i,4],reverse=True)[:2]
    eyes=[]
    for i in sorted(candidates,key=lambda i:cents[i][0]):
        x,y,ww,hh,_=stats[i];eyes.append((float(x+ww/2),float(y+hh/2),float(ww/2),float(hh/2)))
    return eyes

@lru_cache(None)
def mouth_glyph(vis):
    a=part('mouth_'+vis).copy();h,w=a.shape[:2]
    mask=((a[...,:3].max(2)<150)&(a[...,3]>180)).astype(np.uint8)
    count,l,stats,cents=cv2.connectedComponentsWithStats(mask)
    candidates=[i for i in range(1,count) if stats[i,4]>5]
    i=max(candidates,key=lambda i:stats[i,4]);x,y,ww,hh,_=stats[i]
    selected=np.uint8(l==i)*255
    alpha=cv2.GaussianBlur(cv2.dilate(selected,np.ones((11,11),np.uint8)).astype(np.float32),(0,0),2)
    # Include teeth and tongue inside the mouth outline, not just black ink.
    holes=ndi.binary_fill_holes(selected>0)
    alpha=np.maximum(alpha,holes.astype(np.float32)*255)
    a[...,3]=np.minimum(a[...,3],np.uint8(np.clip(alpha,0,255)))
    return a,float(x+ww/2),float(y+hh/2),float(ww)

class Actor:
    def __init__(self,name):
        self.n=name;self.kind=name.split('_')[0];self.a=part(name);self.hh,self.ww=self.a.shape[:2]
        box,neck,band,mouth=CONFIG[name];self.neck=pxy(name,*neck);self.mouth=pxy(name,*mouth[:2]);self.mouthwidth=mouth[2]*META[name]['scale']
        p,q=pxy(name,box[0],box[1]),pxy(name,box[2],box[3]);x0,x1=sorted([p[0],q[0]]);y0,y1=sorted([p[1],q[1]])
        self.hoff=(max(0,int(x0)-4),max(0,int(y0)-3));hx,hy=self.hoff
        xend=min(self.ww,int(x1)+5);yend=min(self.hh,int(y1)+5)
        Y,X=np.mgrid[:self.hh,:self.ww]
        # Head is always backed by its own original drawing, including the collar overlap.
        mask=np.clip((y1-Y)/18,0,1)*np.clip((X-x0+12)/12,0,1)*np.clip((x1-X+12)/12,0,1)*(Y>=y0)
        self.held_prop=None
        if name=='rooney_mic_up':
            # The raised microphone intersects the head box, but belongs to
            # the hand/torso rig. Keep it out of facial and jaw animation.
            guard=np.zeros((self.hh,self.ww),np.uint8)
            poly=[(583,361),(610,367),(631,382),(639,398),(635,422),(624,438),(608,453),(599,462),(580,480),(533,475),(537,452),(544,430),(544,412),(552,393),(566,375)]
            cv2.fillPoly(guard,[np.int32([pxy(name,*q) for q in poly])],255)
            grey=self.a[...,:3].max(2).astype(float)-self.a[...,:3].min(2)<28
            guard=guard.astype(np.float32)/255*grey
            hand=np.zeros((self.hh,self.ww),np.uint8)
            q=[(536,462),(576,464),(596,474),(608,489),(607,511),(593,525),(608,544),(591,598),(555,624),(500,625),(458,581),(454,531),(473,510),(504,479)]
            cv2.fillPoly(hand,[np.int32([pxy(name,*p) for p in q])],255)
            guard=np.maximum(guard,hand.astype(np.float32)/255)
            guard=cv2.GaussianBlur(guard,(0,0),.45)
            prop=self.a.copy();prop[...,3]=np.uint8(prop[...,3]*guard)
            self.held_prop=Sprite(prop)
        clean_head=self.a
        if name=='rooney_mic_up':
            # The low-mic pose has this same unobstructed head in the same
            # source coordinates. Use it as one complete head behind the
            # separately held prop; this prevents alpha holes at the jaw.
            offset=np.array(META['rooney_mic_right']['off'])-META[name]['off']
            clean_head=cv2.warpAffine(part('rooney_mic_right'),T(*offset)[:2],(self.ww,self.hh))
        head=clean_head[hy:yend,hx:xend].copy();head[...,3]=(head[...,3]*mask[hy:yend,hx:xend]).astype(np.uint8)
        by0,by1=pxy(name,box[0],band[0])[1]-hy,pxy(name,box[0],band[1])[1]-hy
        self.eyes=eyes_in(head,by0,by1)
        landmarks={}
        if name in FACE_MARKS:
            line,chin=FACE_MARKS[name];pts=[pxy(name,*q) for q in line]
            if META[name].get('mirror'):pts=[pts[1],pts[0],pts[2]]
            landmarks['mouth']=tuple(float(v) for q in pts for v in (q[0]-hx,q[1]-hy))
            landmarks['chin']=pxy(name,line[2][0],chin)[1]-hy
        self.face=Face(head,eyes=self.eyes,ink=[.025,.02,.025],**landmarks)
        # the body keeps its own collar and shoulders for a band above the head layer's soft lower edge: when the head
        # tilts or nods that edge moves, and a hole cut right up to it showed as a see-through line across the shirt
        pad=.03*self.hh
        hole=(mask>=.999)&(Y<y1-18-pad)
        body=self.a.copy();body[...,3]=(body[...,3]*(~hole)).astype(np.uint8)
        self.cut=self.hh*.59;m=np.clip((self.cut+24-Y)/34,0,1)
        upper=body.copy();upper[...,3]=(upper[...,3]*m).astype(np.uint8)
        lower=body.copy();lower[...,3]=(lower[...,3]*(m<.999)).astype(np.uint8)
        self.upper,self.lower=Sprite(upper),Sprite(lower)

    def placement(self,x,floor,height):return T(x-self.ww*height/self.hh/2,floor-height)@S(height/self.hh)
    def mouth_world(self,x,floor,height):return (self.placement(x,floor,height)@[*self.mouth,1])[:2]
    def head_image(self,t,expr,look,vis):
        st=perf.state(self.kind,t);active=vis!='REST' and self.kind=='rooney'
        amp=.32+.12*perf.voice(t) if active else 1.
        # Episode 1's own-head jaw/brow/eyelid animation, with the selected
        # mouth drawings composited onto that jaw for this caricature style.
        a=self.face.render(vis=('AI' if vis=='A' else vis) if active else 'REST',amp=amp,
                           blink=max(blink(self.kind,t),st['lid']),look=(st['look'],st['looky']),
                           brow=st['brow'],smile=0 if active else st['smile'],paint_mouth=False,blush=st['blush']).copy()
        if vis!='REST' and self.kind=='rooney':
            mx,my=self.mouth;hx,hy=self.hoff;mx-=hx;my-=hy
            if not hasattr(self,'mouth_erase'):
                rgb=np.uint8(np.clip(self.face.img[...,:3]*255,0,255));hh,ww=rgb.shape[:2]
                Y,X=np.mgrid[:hh,:ww]
                # Erase the complete closed smile before an open phoneme is drawn.
                q=np.float32([[-.60,-.14],[-.14,-.095],[.28,-.14],[.68,-.28],[.77,-.10],[.61,.105],[-.15,.16],[-.63,.035]])*self.mouthwidth+[mx,my]
                mask=np.zeros((hh,ww),np.uint8);cv2.fillPoly(mask,[np.int32(q)],255)
                # Fit the surrounding cel-shaded skin; diffusion from the nose
                # creates visible bands when the original smile is removed.
                xx=(X-mx)/self.mouthwidth;yy=(Y-my)/self.mouthwidth
                features=np.stack([np.ones_like(xx),xx,yy,xx**2,xx*yy,yy**2],-1)
                base=self.face.img[...,:3]
                valid=(abs(xx)<.85)&(yy>-.25)&(yy<.45)&(mask==0)&(base[...,0]>.85)&(base[...,1]>.40)&~((abs(xx)<.37)&(yy<.15))
                coef=np.linalg.lstsq(features[valid],base[valid],rcond=None)[0]
                self.mouth_clean=np.clip(features@coef,0,1).astype(np.float32)
                self.mouth_erase=cv2.GaussianBlur(mask.astype(np.float32)/255,(0,0),5)[...,None]
            a[...,:3]=self.mouth_clean*self.mouth_erase+a[...,:3]*(1-self.mouth_erase)
            tile,cx,cy,gwidth=mouth_glyph(vis)
            width=self.mouthwidth*{'A':.94,'E':.94,'I':.88,'O':.48,'U':.32,'MBP':.94,'FV':.94}[vis]
            factor=width/gwidth
            drop={'A':.62,'E':.40,'I':.24,'O':.52,'U':.20,'MBP':0.,'FV':.10}[vis]*amp*.5*self.mouthwidth
            M=T(mx,my+width*.04+drop*.20)@S(factor)@T(-cx,-cy)
            pp=cv2.warpAffine(pm(tile),M[:2],(a.shape[1],a.shape[0]));pp*=a[...,3:4]
            a[...,:3]=pp[...,:3]+a[...,:3]*(1-pp[...,3:4])
        return a

    def draw(self,dst,cam,x,floor,height,t,expr=None,look=0,tilt=0,lean=0,nod=0,vis='REST',hop=0,life=1.):
        st=perf.state(self.kind,t);tilt+=st['tilt'];nod+=st['nod']
        L=perf.life(self.kind,t);lean+=L['lean']*life;tilt+=L['tilt']*life
        # nod: keyed nods in 1/160 of the figure's height (they were sheet px, invisible on the 1x microphone drawings)
        nodpx=nod*self.hh/160+L['nod']*life*self.hh
        M=T(0,-hop)@self.placement(x,floor,height)
        B=T(0,(L['dip']-L['breath'])*life*self.hh)@pivot(self.ww/2,self.cut,lean)
        self.lower.draw(dst,cam@M);self.upper.draw(dst,cam@M@B)
        HM=B@T(0,nodpx)@pivot(*self.neck,tilt)
        over(dst,pm(self.head_image(t,expr,look,vis)),cam@M@HM@T(*self.hoff))
        if self.held_prop:self.held_prop.draw(dst,cam@M@B)

PHONEMES=[(31.69,31.78,'U'),(31.78,31.81,'E'),(31.81,31.90,'U'),(31.90,31.94,'E'),
          (31.94,32.02,'U'),(32.02,32.06,'E'),(32.06,32.20,'U'),(32.20,32.47,'E'),
          (32.47,32.54,'I'),(32.54,32.58,'U'),(32.58,32.67,'I'),(32.67,32.73,'A'),(32.73,32.84,'I')]
def viseme(t):
    for a,b,v in PHONEMES:
        if a+.007<=t<b+.007:return v
    return 'REST'
SHOTS=[(0,1.25,'exterior'),(1.25,3.6,'concert'),(3.6,6.35,'wings'),(6.35,8.25,'rio_warning'),
       (8.25,10.45,'balance'),(10.45,12.7,'beckon'),(12.7,14.4,'rooney_looks'),(14.4,15.95,'rio_looks'),
       (15.95,17.9,'why_not'),(17.9,21.5,'entrance'),(21.5,22.9,'reverse'),(22.9,24.25,'awkward'),
       (24.25,25.85,'rio_deadpan'),(25.85,27.55,'idea'),(27.55,28.4,'microphone'),(28.4,29.25,'rio_no'),
       (29.25,31.25,'strut'),(31.25,33.08,'punchline'),(33.08,33.5,'blank'),(33.5,34.4,'laugh'),
       (34.4,35.,'fifty_amused'),(35.,36.455,'finish'),(36.455,36.488,'black')]
def shot(t):
    for a,b,n in SHOTS:
        if a<=t<b:return n,(t-a)/(b-a)
    return 'black',0

class Scene:
    def __init__(self,width):
        self.ow=width;self.oh=width*16//9
        self.bg={n:np.asarray(Image.open(ROOT/'src/art'/f'{n}.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)).astype(np.float32)/255 for n in ['exterior','stage','wings','crowd','mic-plate']}
        active=['rooney_right','rio_left','fifty_exit','rooney_mic_right','rooney_mic_up','rio_mic_right','rio_mic_left']
        self.actors={n:Actor(n) for n in active};self.sprites={};self.rigs={};self.walkfaces={};self.special={}
        self.lights=LX.Lights(self.ow,self.oh);self.crowd=CR.Crowd();self.t=0.;self.lit=None

    def camera(self,zoom,cx,cy):
        # while the show's on the camera bumps on every beat, like a concert edit (harder in the party)
        t=self.t;ph=(t/LX.BEAT)%1
        zoom*=1+.009*LX.show(t)*(1+.7*LX.party(t))*math.exp(-ph/.11)
        return T(self.ow/2,self.oh/2)@S(zoom*self.ow/W)@T(-cx,-cy)
    def plate(self,n,cam):
        # the camera is a scale and a shift, so plate coords of the output grid are two 1D ramps
        k=float(cam[0,0]);t=self.t
        px=((np.arange(self.ow,dtype=np.float32)+.0-cam[0,2])/k)[None,:].repeat(self.oh,0)
        py=((np.arange(self.oh,dtype=np.float32)+.0-cam[1,2])/k)[:,None].repeat(self.ow,1)
        mv=self.crowd.displace(n,px,py,t)                       # the crowd bounces (crowd.py)
        if mv is None:
            d=cv2.warpAffine(self.bg[n],cam[:2],(self.ow,self.oh),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
        else:
            d=cv2.remap(self.bg[n],(px-mv[0]).astype(np.float32),(py+mv[1]).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
        # the show's lighting goes on the set, under the characters (lights.py)
        self.lights.plate(d,cam,n,t)
        if n=='stage':
            self.lights.mirror_ball(d,cam,t,LX.party(t)*(1 if t<35 else 1.15),ball=(300,250,34) if t>=33.5 else None)
            self.lights.sparks(d,cam,t)
        elif n=='crowd':self.lights.mirror_ball(d,cam,t,LX.party(t))
        self.lit=d.copy();return d
    def shadow(self,dst,cam,x,floor,height):
        a=np.zeros((36,220,4),np.float32);cv2.ellipse(a,(110,18),(101,10),0,0,360,(0,0,0,.3),-1,cv2.LINE_AA)
        a=cv2.GaussianBlur(a,(0,0),3);over(dst,a,cam@T(x-height*.2,floor-height*.025)@S(height*.4/220))
    def actor(self,dst,cam,n,x,floor,height,t,**kw):
        self.shadow(dst,cam,x,floor,height);self.actors[n].draw(dst,cam,x,floor,height,t,**kw)
    def full(self,dst,cam,n,x,floor,height,sway=0.):
        if n not in self.sprites:self.sprites[n]=Sprite(part(n))
        a=self.sprites[n];s=height/a.h;self.shadow(dst,cam,x,floor,height)
        a.draw(dst,cam@T(x-a.w*s/2,floor-height)@S(s)@pivot(a.w/2,a.h,sway))   # sway: rock on the feet (deg)
    def occlude(self,dst,cam,n,poly):
        # foreground pieces of the set come from the same lit plate, so they match the lighting behind the characters
        mask=np.zeros((H,W),np.uint8);cv2.fillPoly(mask,[np.int32(poly)],255)
        m=cv2.warpAffine(mask.astype(np.float32)/255,cam[:2],(self.ow,self.oh),flags=cv2.INTER_LINEAR)[...,None]
        dst[:]=dst*(1-m)+self.lit*m
    def walk(self,dst,cam,n,x,floor,height,distance,phase=0,lean=1.4,moving=1,stop_distance=None,time=0,look=0):
        from walkrig import WalkRig
        mirror=n.endswith('right')
        if n not in self.rigs:self.rigs[n]=WalkRig(n,mirror=mirror)
        r=self.rigs[n];s=height/part(n).shape[0];u=distance/s;step=r.leglen*.37
        if stop_distance is not None:phase=(.55-(stop_distance/s)/(2*step))%1
        joints,drop=r.pose(u,step,phase,moving=moving)
        M=T(x,floor)@np.diag([-s if mirror else s,s,1.])@T(-r.hip[0],-r.sole)
        self.shadow(dst,cam,x,floor,height)
        for p in r.layers(joints,drop,M,0,lean=lean):
            if p.d is r.upper:
                if n not in self.walkfaces:
                    a=r.upper.u8[1.];h,w=a.shape[:2]
                    band=CONFIG[n][2]
                    y0=pxy(n,0,band[0])[1];y1=pxy(n,0,band[1])[1]
                    eyes=eyes_in(a,y0,y1)
                    self.walkfaces[n]=Face(a,eyes=eyes,ink=[.025,.02,.025])
                st=perf.state(n.split('_')[0],time)
                a=self.walkfaces[n].render(blink=max(blink(n.split('_')[0],time),st['lid']),look=(-st['look'] if mirror else st['look'],st['looky']),brow=st['brow'],blush=st['blush'])
                over(dst,pm(a),cam@p.M)
            else:over(dst,p.d.base(1),cam@p.M)

    def performer(self,dst,cam,x,floor,height,t):
        n='fifty_pose_perform';a=part(n);h,w=a.shape[:2];s=height/h
        if n not in self.special:
            eyes=eyes_in(a,h*.16,h*.29);self.special[n]=Face(a,eyes=eyes,ink=[.025,.02,.025])
        a=self.special[n].render(blink=blink('fifty',t),look=(-.6 if t>9.8 else .1,0))
        # cut through the jeans, below both fists, so the hands always stay whole when the top half moves
        Y=np.mgrid[:h,:w][0];mask=np.clip((h*.76+10-Y)/20,0,1)
        upper=a.copy();upper[...,3]*=mask;lower=a.copy();lower[...,3]*=(mask<.999)
        M=cam@T(x-w*s/2,floor-height)@S(s)
        self.shadow(dst,cam,x,floor,height);over(dst,pm(lower),M)
        # performing: knees bounce on every beat (the torso dips), shoulders rock side to side on the bar
        b=t/LX.BEAT;ph=b%1;hit=math.exp(-(ph/.22)**2)+math.exp(-((ph-1)/.22)**2)
        over(dst,pm(upper),M@T(0,h*.011*hit)@pivot(w*.48,h*.76,1.3*math.sin(math.pi*b)+.8*hit))

    def beckon(self,dst,cam,t):
        n='fifty_pose_beckon';a=part(n);h,w=a.shape[:2];s=540/h
        # Rotate the entire free forearm at its elbow; the torso and feet are held.
        Y,X=np.mgrid[:h,:w];elbow=(w*.34,h*.45)
        mask=((X<w*.40)&(Y>h*.28)&(Y<h*.49)).astype(np.float32)
        disk=((X-elbow[0])**2+(Y-elbow[1])**2<(w*.035)**2)
        arm=a.copy();arm[...,3]=(arm[...,3]*mask).astype(np.uint8)
        body=a.copy();body[...,3]=(body[...,3]*(~(mask.astype(bool)&~disk))).astype(np.uint8)
        hip=h*.76;m=np.clip((hip+12-Y)/24,0,1)                # below the hands and the mic
        up=body.copy();up[...,3]=(up[...,3]*m).astype(np.uint8);low=body.copy();low[...,3]=(low[...,3]*(m<.999)).astype(np.uint8)
        M=cam@T(530-w*s/2,975-540)@S(s)
        self.shadow(dst,cam,530,975,540);over(dst,pm(low),M)
        # still in the groove while he invites them on: a dip on the beat, a lean into each 'come on'
        b=t/LX.BEAT;ph=b%1;hit=math.exp(-(ph/.22)**2)+math.exp(-((ph-1)/.22)**2)
        U=M@T(0,h*.01*hit)@pivot(w*.5,hip,1.1*math.sin(math.pi*b)-1.*hit)
        over(dst,pm(up),U)
        theta=6*math.sin(math.pi*smooth((t-10.8)/.6))-4*math.sin(math.pi*smooth((t-11.7)/.6))+5*math.sin(2*math.pi*b)*.4
        over(dst,pm(arm),U@pivot(*elbow,theta))

    def folded_laugh(self,dst,cam,t):
        n='rio_pose_laugh_mic';a=part(n);h,w=a.shape[:2];s=425/h
        if n not in self.special:
            Y=np.mgrid[:h,:w][0];m=np.clip((h*.72+20-Y)/40,0,1)
            up=a.copy();up[...,3]=(up[...,3]*m).astype(np.uint8);low=a.copy();low[...,3]=(low[...,3]*(m<.999)).astype(np.uint8)
            self.special[n]=(Sprite(up),Sprite(low))
        up,low=self.special[n];M=cam@T(225-w*s/2,960-425)@S(s)
        self.shadow(dst,cam,225,960,425);low.draw(dst,M)
        theta=1.6*math.sin(max(0,t-33.5)*8.5)*math.exp(-max(0,t-33.5)*.22)
        shake=h*.007*abs(math.sin(max(0,t-33.5)*19))        # shoulders going with every laugh
        up.draw(dst,M@T(0,-shake)@pivot(w*.55,h*.72,theta))

    def sweat(self,dst,cam,n,x,floor,height,at,t0,t,size=1.):
        """a cartoon sweat drop at a point of the drawing (its own px), sliding down the temple"""
        a=t-t0
        if a<0:return
        act=self.actors[n];p=(act.placement(x,floor,height)@[*pxy(n,*at),1])[:2]
        k=float(cam[0,0])*height/act.hh*META[n]['scale']*size     # output px per sheet px
        grow=smooth(a/.18);slide=40*smooth((a-.25)/1.3)
        q=cam@np.array([p[0],p[1],1.]);cx,cy=q[0],q[1]+slide*k
        r=18*k*grow
        if r<1:return
        ta=-1.95                                                      # a teardrop leaning out, its point up
        tip=(cx+2.1*r*math.cos(ta),cy+2.1*r*math.sin(ta))
        pts=[tip]+[(cx+r*math.cos(th),cy+r*math.sin(th)) for th in np.linspace(ta+1.05,ta+2*math.pi-1.05,28)]
        poly=np.int32(np.round(np.array(pts)*4))
        cv2.fillPoly(dst,[poly],(.62,.84,1.),cv2.LINE_AA,2)
        cv2.polylines(dst,[poly],True,(.02,.02,.04),max(1,int(round(1.3*k))),cv2.LINE_AA,2)
        cv2.ellipse(dst,(int(cx+.3*r),int(cy+.15*r)),(max(1,int(.28*r)),max(1,int(.45*r))),-30,0,360,(1,1,1),-1,cv2.LINE_AA)

    def tumbleweed(self,dst,cam,t,t0,t1):
        """the awkward silence: a tumbleweed rolls across the front of the stage, bouncing"""
        if not t0<=t<t1:return
        u=(t-t0)/(t1-t0);x=900-800*u;r=34
        y=990-r-30*abs(math.sin(u*math.pi*3.2))                       # three little bounces, at the front of the stage
        if not hasattr(self,'_weed'):
            rng=np.random.default_rng(7);self._weed=[(rng.uniform(0,6.3),rng.uniform(.45,1.),rng.uniform(.4,1.1),rng.uniform(0,6.3)) for _ in range(26)]
        k=float(cam[0,0]);q=cam@np.array([x,y,1.]);R=r*k;rot=-u*12
        self.shadow(dst,cam,x,990,r*2.4)
        strokes=[]
        for i,(a0,rr,span,ph) in enumerate(self._weed):           # loose open loops of dry twig, rolling
            ang=a0+rot;cxy=(q[0]+.3*R*math.cos(ang+ph),q[1]+.3*R*math.sin(ang+ph))
            pts=[(cxy[0]+rr*R*math.cos(ang+v),cxy[1]+rr*R*.92*math.sin(ang+v)) for v in np.linspace(0,span*math.pi,9)]
            strokes.append(np.int32(np.round(np.array(pts)*4)))
        for p in strokes:cv2.polylines(dst,[p],False,(.16,.11,.06),max(1,int(round(2.2*k))),cv2.LINE_AA,2)
        for i,p in enumerate(strokes):cv2.polylines(dst,[p],False,(.86,.72,.47) if i%2 else (.74,.58,.35),max(1,int(round(1.1*k))),cv2.LINE_AA,2)

    def glint(self,dst,cam,x,y,t0,t):
        """a four-point star that pops and turns: the 'ting' of a bad idea"""
        a=t-t0
        if a<0 or a>.42:return
        q=cam@np.array([x,y,1.]);s=math.sin(math.pi*a/.42)**.8*float(cam[0,0])*14
        layer=np.zeros_like(dst);th=a*3
        for j in range(4):
            ang=th+j*math.pi/2;w=.16
            pts=[(q[0]+s*math.cos(ang),q[1]+s*math.sin(ang)),(q[0]+s*w*math.cos(ang+math.pi/2),q[1]+s*w*math.sin(ang+math.pi/2)),
                 (q[0],q[1]),(q[0]+s*w*math.cos(ang-math.pi/2),q[1]+s*w*math.sin(ang-math.pi/2))]
            cv2.fillPoly(layer,[np.int32(np.round(np.array(pts)*4))],(1,1,1),cv2.LINE_AA,2)
        layer=np.maximum(layer,cv2.GaussianBlur(layer,(0,0),max(1,s*.12))*1.4)
        dst[:]=1-(1-dst)*(1-np.clip(layer,0,1))

    def phone_glints(self,dst,cam,t,reverse=False):
        if t<32.85 and not reverse:return
        points=[(72,1114),(336,1255),(845,1213),(623,1115),(177,1090)] if not reverse else [(212,610),(697,702),(417,875),(788,905),(91,748)]
        for i,(x,y) in enumerate(points):
            v=max(0,math.sin(t*3.1+i*1.77))**8
            if v<.08:continue
            q=cam@np.array([x,y,1]);r=max(1,int(self.ow/W*2))
            cv2.circle(dst,(int(q[0]),int(q[1])),r,(.65*v,.85*v,1*v),-1,cv2.LINE_AA)

    def render(self,t):
        n,u=shot(t);ss=smooth(u);self.t=t;spots=[]
        if n=='black':return np.zeros((self.oh,self.ow,3),np.uint8)
        if n=='exterior':
            c=self.camera(1+.055*smooth(min(u*2,1)),471,850);d=self.plate('exterior',c)
        elif n=='concert':
            c=self.camera(1.01+.07*ss,470,842);d=self.plate('stage',c)
            self.performer(d,c,515,975,500,t);self.occlude(d,c,'stage',[(0,1063),(941,1063),(941,1672),(0,1672)])
        elif n in ['wings','balance','why_not','rooney_looks','rio_warning','rio_looks']:
            if n in ['rio_warning','rio_looks']:c=self.camera(2.9+.04*ss,536,1000)
            elif n=='rooney_looks':c=self.camera(2.9+.04*ss,285,1108)
            elif n=='why_not':c=self.camera(1.14+.015*ss,457,1085)
            else:c=self.camera(1.01+.025*ss,461,1065)
            d=self.plate('wings',c);self.performer(d,c,723,811,290,t)
            lean=(2.0*math.exp(-((t-8.9)/.43)**2)-1.0*math.exp(-((t-9.5)/.26)**2)) if n=='balance' else 0
            hic=16*math.exp(-((t-9.25)/.045)**2) if n=='balance' else 0         # "a few drinks": one hiccup
            if n not in ['rio_warning','rio_looks']:
                self.actor(d,c,'rooney_mic_right' if t>=12.7 else 'rooney_right',286,1530,700,t,look=.6,lean=lean,hop=hic)
            if n!='rooney_looks':
                self.actor(d,c,'rio_mic_left' if t>=12.7 else 'rio_left',551,1504,762,t,look=-.85)
            self.occlude(d,c,'wings',[(0,711),(126,711),(137,1024),(36,1070),(0,1070)])
        elif n=='beckon':
            c=self.camera(2.2+.045*ss,514,688);d=self.plate('stage',c);self.beckon(d,c,t)
        elif n=='entrance':
            c=self.camera(1.14+.02*ss,411,852);d=self.plate('stage',c)
            tt=min(t-17.9,3.3);st=max(0,tt-2.7);dt=tt-st*st/1.2 if tt>2.7 else tt;moving=max(0,1-st/.6)
            # 50 passes behind them on a separate stage depth, then clears the wing.
            fx=666-210*(t-17.9)
            if fx>-180:self.walk(d,c,'fifty_exit',fx,934,510,210*(t-17.9),.12,time=t,look=.7)
            self.walk(d,c,'rio_mic_right',-128+106*dt,960,540,106*dt,moving=moving,stop_distance=318,time=t,look=-.8 if t>20.3 else .4)
            self.walk(d,c,'rooney_mic_right',128+91*dt,975,475,91*dt,moving=moving,stop_distance=273,time=t,look=.5)
            for p in [[(0,907),(60,907),(100,983),(0,988)],[(859,907),(941,907),(941,988),(834,979)]]:self.occlude(d,c,'stage',p)
            # the follow-spot leaves with 50 Cent; a beat later the operator remembers the two blokes he left behind
            back=0. if t<20.98 else (.55 if t<21.05 else (.15 if t<21.1 else smooth((t-21.1)/.06)))
            spots=[(fx,934,510,1.),(-128+106*dt,960,540,back),(128+91*dt,975,475,back)]
        elif n=='reverse':
            c=self.camera(1.01+.035*ss,470,855);d=self.plate('crowd',c)
            # the backs aren't frozen: Rio stands stiff and rocks a little, Rooney shifts from foot to foot
            self.full(d,c,'rio_back',279,1453,640,sway=.5*math.sin(2*math.pi*t/2.3))
            self.full(d,c,'rooney_back',625,1465,584,sway=1.1*math.sin(2*math.pi*t/1.4+1.)+.4*math.sin(2*math.pi*t/.7))
            self.phone_glints(d,c,t,True)
            spots=[(279,1453,640),(625,1465,584)]
        elif n=='awkward':
            c=self.camera(1.8+.025*ss,330,767);d=self.plate('stage',c)
            self.actor(d,c,'rio_mic_right',190,960,540,t,look=.85 if u<.45 or u>.82 else 0)
            self.actor(d,c,'rooney_mic_right',405,975,475,t,look=-.85 if u<.5 else 0)
            spots=[(190,960,540),(405,975,475)]
            self.sweat(d,c,'rooney_mic_right',405,975,475,(668,170),23.35,t,2.2)
            self.tumbleweed(d,c,t,23.0,24.25)
        elif n in ['rio_deadpan','rio_no','blank']:
            c=self.camera(4.35+.035*ss,207,615);d=self.plate('stage',c)
            self.actor(d,c,'rio_mic_right',190,960,540,t,look=0 if n=='blank' else .8,tilt=2.0*math.sin((t-28.4)*11)*math.sin(math.pi*u) if n=='rio_no' else 0)
            spots=[(190,960,540)]
            if n=='rio_deadpan':self.sweat(d,c,'rio_mic_right',190,960,540,(632,150),24.5,t,1.1)
        elif n=='idea':
            c=self.camera(4.55+.05*ss,422,665);d=self.plate('stage',c)
            self.actor(d,c,'rooney_mic_right',405,975,475,t,look=.9)
            spots=[(405,975,475)]
        elif n=='microphone':
            a=self.actors['rooney_mic_right'];grille=(a.placement(516,975,490)@[*pxy('rooney_mic_right',632,556),1])[:2]
            c=self.camera(7+.05*ss,grille[0]-4,grille[1]+97);d=self.plate('stage',c)
            self.actor(d,c,'rooney_mic_right',516,975,490,t)
            spots=[(516,975,490)]
            self.glint(d,c,grille[0]-10,grille[1]-14,27.82,t)
        elif n=='strut':
            c=self.camera(2.35+.025*ss,468,765);d=self.plate('stage',c)
            self.actor(d,c,'rio_mic_right',190,960,540,t,look=.9)
            tt=t-29.25;dist=55.5*tt
            sway=2.6*math.sin(math.pi*(dist/(490/part('rooney_mic_right').shape[0]))/(self.rigs['rooney_mic_right'].leglen*.37)+.8) if 'rooney_mic_right' in self.rigs else 0
            self.walk(d,c,'rooney_mic_right',405+dist,975,490,dist,.25,lean=1.5+sway,time=t,look=-.95 if 30.05<t<30.33 else .35)
            spots=[(190,960,540),(405+dist,975,490)]
        elif n=='punchline':
            pulse=sum(math.exp(-((t-g)/.052)**2) for g in [31.707,31.817,31.947,32.067])
            # the camera punches in on every G and jolts on UNIT
            kick=sum(math.exp(-max(0,t-g)/.06)*(t>=g) for g in LX.G_HITS)
            jolt=math.exp(-max(0,t-LX.UNIT)/.12)*(t>=LX.UNIT)
            shake=6*jolt*math.sin(t*95),5*jolt*math.cos(t*80)
            c=self.camera(4.9+.035*ss+.16*min(kick,1.3)+.35*jolt,522+shake[0],650+shake[1]);d=self.plate('stage',c)
            self.actor(d,c,'rooney_mic_up',516,975,490,t,look=.25,tilt=-.5*pulse,nod=.35*pulse,vis=viseme(t))
        elif n=='laugh':
            c=self.camera(2.8+.02*ss,251,758);d=self.plate('stage',c);self.folded_laugh(d,c,t)
        elif n=='fifty_amused':
            c=self.camera(2.5+.025*ss,680,1002);d=self.plate('wings',c)
            shake=2.4*math.sin((t-34.45)*13)*smooth((t-34.45)/.12)*(1-smooth((t-34.85)/.15))
            self.actor(d,c,'fifty_exit',665,1450,700,t,look=-.85,tilt=1.0+shake)
        elif n=='finish':
            c=self.camera(1.48+.035*min(ss,.8),395,763);d=self.plate('stage',c)
            self.folded_laugh(d,c,min(t,36.15));self.actor(d,c,'rooney_mic_up',516,975,490,min(t,36.15),look=.1)
            self.phone_glints(d,c,t)
        self.lights.spots(d,c,t,spots)
        self.lights.flash(d,t)
        return np.uint8(np.clip(d*255,0,255))
