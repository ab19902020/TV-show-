import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from film import sprites as SP
W,H=1280,720; S=2; w,h=W*S,H*S
cx,cy=w*0.47,h*0.55
yy,xx=np.mgrid[0:h,0:w]
ang=np.degrees(np.arctan2(yy-cy,xx-cx))%360; ray=(ang//9)%2==0
left=xx<(w*0.5+(yy-h/2)*0.35)
r=np.where(left,np.where(ray,255,245),np.where(ray,215,170))
g=np.where(left,np.where(ray,214,180),np.where(ray,30,10))
b=np.where(left,np.where(ray,40,0),np.where(ray,40,25))
bg=np.dstack([r,g,b]).astype(np.float32)
d2=np.sqrt(((xx-cx)/w)**2+((yy-cy)/h)**2); bg*=np.clip(1.15-0.9*d2,0.35,1)[...,None]
im=Image.fromarray(bg.astype(np.uint8)).convert('RGBA')
dd=ImageDraw.Draw(im)
def strip(off,wid): return [(w*0.5+off-0.175*h,0),(w*0.5+off+wid-0.175*h,0),(w*0.5+off+wid+0.175*h,h),(w*0.5+off+0.175*h,h)]
dd.polygon(strip(-14,28),fill=(255,255,255)); dd.polygon(strip(-6,12),fill=(29,66,138))
def outlined(p,width):
    a=p.getchannel('A').filter(ImageFilter.MaxFilter(width*2+1)); o=Image.new('RGBA',p.size,(255,255,255,255)); o.putalpha(a); o.alpha_composite(p); return o
def load(path,hpx,crop,flip=False):
    p=Image.open(path).convert('RGBA'); p=p.crop((0,0,p.width,int(p.height*crop)))
    if flip: p=p.transpose(Image.FLIP_LEFT_RIGHT)
    s=hpx/p.height; return p.resize((int(p.width*s),hpx),Image.LANCZOS)
def place(p,x,y):
    pad=40; q=Image.new('RGBA',(p.width+2*pad,p.height+2*pad)); q.alpha_composite(p,(pad,pad)); q=outlined(q,9)
    sh=Image.new('RGBA',q.size,(0,0,0,255)); sh.putalpha(q.getchannel('A').point(lambda v:int(v*0.6)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)),(x-pad+18,y-pad+22)); im.alpha_composite(q,(x-pad,y-pad))
wil=load('build/film/jason-wilcox/l-scream.png',int(h*1.10),0.70)
place(wil,int(0.0*w),int(0.13*h))
d=ImageDraw.Draw(im)
for (x,y,s) in [(0.05,0.30,1.0),(0.32,0.25,1.2),(0.35,0.40,0.9)]:
    X,Y,R=x*w,y*h,22*S*s
    d.polygon([(X,Y-2.2*R),(X+R,Y),(X-R,Y)],fill=(170,215,255),outline=(20,40,80))
    d.ellipse([X-R,Y-R*0.6,X+R,Y+R*1.1],fill=(170,215,255),outline=(20,40,80),width=5)
p=SP.plant(False); pw=0.62*w/p['size'][0]
def sp(img,x,y,s,ang=0,anchor=None):
    arr=np.zeros((h,w,3),np.float32); al=np.zeros((h,w,3),np.float32)
    SP.paste(arr,img,x,y,s,ang,anchor); white=np.concatenate([img[...,:3]*0+255,img[...,3:4]],2).astype(np.uint8)
    SP.paste(al,white,x,y,s,ang,anchor)
    im.alpha_composite(Image.fromarray(np.dstack([np.clip(arr/np.maximum(al,1e-3),0,1)*255,al[...,:1]*255]).astype(np.uint8)))
px,py=0.80*w,1.05*h
sp(p['back'],px,py,pw,0,p['pivot'])
lic=load('build/film/lisandro-martinez/c-point.png',int(h*1.0),0.66,flip=True)
place(lic,int(0.52*w),int(0.12*h))
sp(p['fl'],px,py,pw,-48,p['pivot']); sp(p['fr'],px,py,pw,48,p['pivot'])
d=ImageDraw.Draw(im); rng=np.random.default_rng(3); n=0
while n<45:
    x=rng.uniform(0.40,0.70)*w; y=rng.uniform(0.25,0.95)*h
    if 0.52*w<x<0.68*w and 0.62*h<y<0.80*h: continue      # keep the pointing hand clear
    rr=rng.uniform(6,16)*S; n+=1
    if rng.random()<0.7: d.ellipse([x-rr,y-rr*0.8,x+rr,y+rr*0.8],fill=(92,60,36),outline=(30,20,12),width=3)
    else: d.polygon([(x-rr*2,y),(x,y-rr*0.8),(x+rr*2,y),(x,y+rr*0.8)],fill=(70,150,62),outline=(24,40,20))
F=lambda s:ImageFont.truetype('library/fonts/BebasNeue-Regular.ttf',s*S)
def bigtext(s,xy,size,fill,rot=0):
    lay=Image.new('RGBA',(w,h)); L=ImageDraw.Draw(lay)
    for k in range(14,0,-1): L.text((xy[0]+k*S,xy[1]+k*S),s,font=F(size),fill=(60,10,10),anchor='mm',stroke_width=10*S,stroke_fill=(0,0,0))
    L.text(xy,s,font=F(size),fill=fill,anchor='mm',stroke_width=10*S,stroke_fill=(0,0,0))
    im.alpha_composite(lay.rotate(rot,center=xy,resample=Image.BICUBIC))
bigtext('I KNEW IT!',(int(0.74*w),int(0.14*h)),160,(255,232,0),rot=4)
# the accusation: banner, the Leeds badge circled with an arrow, name tags
ban=Image.new('RGBA',(w,h)); B=ImageDraw.Draw(ban); c=(0.225*w,0.095*h)
B.rounded_rectangle([0.015*w,0.02*h,0.435*w,0.17*h],radius=16*S,fill=(29,66,138),outline=(255,205,0),width=7*S)
B.text(c,'SECRET LEEDS FAN?!',font=F(66),fill=(255,232,0),anchor='mm',stroke_width=4*S,stroke_fill=(0,0,0))
im.alpha_composite(ban.rotate(-3,center=c,resample=Image.BICUBIC))
d=ImageDraw.Draw(im)
bx,by,br=0.245*w,0.885*h,0.075*w
for wd,col in ((16*S,(0,0,0)),(9*S,(255,30,30))):
    d.ellipse([bx-br,by-br*0.8,bx+br,by+br*0.8],outline=col,width=wd)
ax0,ay0,ax1,ay1=0.47*w,0.60*h,bx+br*0.95,by-br*0.35
for wd,col in ((22*S,(0,0,0)),(12*S,(255,30,30))):
    d.line([(ax0,ay0),(ax1,ay1)],fill=col,width=wd)
ang=math.atan2(ay1-ay0,ax1-ax0); L=48*S
for col,e in (((0,0,0),10*S),((255,30,30),0)):
    pts=[(ax1+math.cos(ang)*e,ay1+math.sin(ang)*e),(ax1-L*math.cos(ang-0.5),ay1-L*math.sin(ang-0.5)),(ax1-L*math.cos(ang+0.5),ay1-L*math.sin(ang+0.5))]
    d.polygon(pts,fill=col)
def tag(text,x,y,fill,fg,rot):
    t=Image.new('RGBA',(w,h)); T=ImageDraw.Draw(t); f=F(52)
    tw=T.textlength(text,font=f); pad=18*S
    T.rounded_rectangle([x-tw/2-pad,y-34*S,x+tw/2+pad,y+34*S],radius=10*S,fill=fill,outline=(255,255,255),width=5*S)
    T.text((x,y),text,font=f,fill=fg,anchor='mm',stroke_width=3*S,stroke_fill=(0,0,0))
    im.alpha_composite(t.rotate(rot,center=(x,y),resample=Image.BICUBIC))
tag('JASON WILCOX',0.20*w,0.235*h,(255,205,0),(255,255,255),-3)
tag('LISANDRO MARTINEZ',0.80*w,0.93*h,(200,16,30),(255,255,255),2)
out=im.convert('RGB').resize((W,H),Image.LANCZOS); a=np.asarray(out).astype(np.float32)
Y,X=np.mgrid[0:H,0:W]; v=np.sqrt(((X-W/2)/W)**2+((Y-H/2)/H)**2)
a*=np.clip(1.1-0.55*v,0.6,1)[...,None]; a=(a-128)*1.08+128
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('/home/user/TV-show-/the-mole/The_Mole_thumbnail.jpg',quality=93)
