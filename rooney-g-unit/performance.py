"""Episode 1-style keyed, held performance channels, adapted to this recording.

The selected drawings, edit and silent-narration staging remain unchanged.
Eye darts reach their targets before a reaction is held; blinks are staggered.
"""
import math
from pathlib import Path
from functools import lru_cache
import subprocess
import numpy as np
from collections import defaultdict

KEYS=defaultdict(lambda:defaultdict(list))
DEFAULT=dict(look=0.,looky=0.,brow=0.,smile=0.,tilt=0.,nod=0.,lid=0.,blush=0.)

def key(who,channel,t,value,ramp=.18):
    KEYS[who][channel].append((float(t),float(value),max(.01,ramp)))

def value(who,channel,t):
    v=DEFAULT[channel]
    for tk,vk,ramp in KEYS[who][channel]:
        if t<=tk:break
        u=min(1.,(t-tk)/ramp);u=u*u*(3-2*u);v+=(vk-v)*u
    return v

def state(who,t):return {c:value(who,c,t) for c in DEFAULT}

@lru_cache(None)
def speech_envelope():
    source=Path(__file__).resolve().parent/'src/audio/original.webm'
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(source),'-map','0:a:0','-af','aresample=async=1:first_pts=0','-ac','1','-ar','16000','-f','f32le','-'])
    y=np.frombuffer(raw,np.float32);out=np.zeros(1095,np.float32)
    for i in range(len(out)):
        a=int(i*16000/30);b=min(len(y),int((i+1)*16000/30))
        if b>a:out[i]=np.sqrt(np.mean(y[a:b]**2))
    ref=np.percentile(out[int(31.7*30):int(32.85*30)],85)
    return np.clip(out/max(ref,1e-6),0,1.2)

def voice(t):return float(speech_envelope()[min(1094,max(0,int(t*30)))])

for who,channel,items in [
 ('rooney','look',[(0,.35),(4.2,.65),(9.8,.8),(12.9,.78),(16.2,.65),(20.5,-.6),(22.95,-.8),(23.55,.0),(25.95,.82),(29.25,.4),(30.04,-.86),(30.35,.3),(33.0,.12)]),
 ('rooney','looky',[(0,0),(25.95,.65),(28.35,0),(31.5,-.06)]),
 ('rooney','brow',[(0,-.04),(12.95,.3),(16.2,.12),(20.6,.35),(22.95,.3),(25.95,-.12),(31.45,.18),(33.0,.12)]),
 ('rooney','smile',[(0,.2),(12.9,-.4),(16.2,.55),(20.5,-.55),(22.95,-.6),(25.95,.8),(31.5,.1),(32.9,.8)]),
 ('rooney','tilt',[(0,0),(13.05,1.1),(13.9,0),(16.35,-1.5),(16.8,.4),(17.35,0),(23.0,-.6),(25.95,-.8),(31.2,0),(32.95,-.7)]),
 ('rooney','nod',[(0,0),(16.42,1.8),(16.62,0),(32.94,.7),(33.15,0)]),
 ('rio','look',[(0,-.55),(6.4,-.8),(10.45,-.2),(14.4,-.8),(16.1,-.55),(20.3,-.8),(22.95,.8),(23.45,0),(23.92,.85),(24.5,.55),(28.4,.8),(33.08,0)]),
 ('rio','brow',[(0,-.08),(6.4,-.35),(14.4,-.26),(20.65,.27),(22.95,.2),(24.4,-.28),(28.4,.4),(33.08,-.12)]),
 ('rio','smile',[(0,0),(6.4,-.3),(14.4,-.4),(22.95,-.5),(24.4,-.3),(28.4,-.55),(33.08,0)]),
 ('rio','lid',[(0,0),(6.45,.2),(7.1,0),(14.6,.2),(15.3,0),(24.45,.34),(25.85,0),(33.08,.26)]),
 ('rio','tilt',[(0,0),(6.45,1.3),(8.1,0),(14.4,-1.0),(16.5,0),(22.95,1.0),(24.4,0)]),
 ('fifty','look',[(0,.1),(9.9,-.75),(10.9,-.65),(18.,.75),(34.4,.65)]),
 ('fifty','brow',[(0,-.08),(10.5,.3),(18.,.12),(34.4,.45)]),
 ('fifty','smile',[(0,.05),(10.8,.55),(18.,.45),(34.4,.65)]),
]:
    for t,v in items:key(who,channel,t,v,.16 if channel=='look' else .28)

# A few drinks: both go rosy on "we both had a few drinks" and stay that way all night (Rooney more).
for t,v in [(0,0.),(7.6,.25),(8.6,1.),(10.6,.75),(31.6,.95)]:key('rooney','blush',t,v,.5)
for t,v in [(0,0.),(7.8,.2),(8.8,.6),(10.6,.45)]:key('rio','blush',t,v,.5)
# The hiccup in the wobble: eyes pop, then settle back.
for t,v in [(9.2,.85),(9.42,-.04)]:key('rooney','brow',t,v,.05)
# The idea: an eyebrow waggle (up-down, up-down) behind the grin.
for t,v in [(26.4,.85),(26.57,-.15),(26.74,.85),(26.91,-.15),(27.15,-.1)]:key('rooney','brow',t,v,.07)
# 50, from the wing: a slow amused head shake (in engine.py) with the brows up.
for t,v in [(34.45,.7)]:key('fifty','brow',t,v,.15)

for who in KEYS:
    for channel in KEYS[who]:KEYS[who][channel].sort()

def blink(who,t):
    times={
        'rooney':[4.7,9.85,14.6,16.85,20.95,24.1,26.25,30.35,35.8],
        'rio':[3.95,7.7,11.1,15.4,19.7,23.6,28.55,33.05],
        'fifty':[2.2,7.2,10.55,12.3,20.5,35.1],
    }
    return max([0.]+[math.sin(math.pi*(t-b)/.17)**.7 for b in times.get(who,[]) if 0<=t-b<.17])
