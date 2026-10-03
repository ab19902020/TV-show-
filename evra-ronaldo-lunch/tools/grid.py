"""A sheet region with a coordinate grid, zoomed: python3 tools/grid.py src/art/evra.png out.png x0 y0 x1 y1 [step] [zoom]"""
import sys
from PIL import Image,ImageDraw
src,out=sys.argv[1],sys.argv[2];x0,y0,x1,y1=map(int,sys.argv[3:7])
step=int(sys.argv[7]) if len(sys.argv)>7 else 20;z=float(sys.argv[8]) if len(sys.argv)>8 else 2
im=Image.open(src).convert('RGB').crop((x0,y0,x1,y1))
im=im.resize((int(im.width*z),int(im.height*z)),Image.Resampling.LANCZOS);d=ImageDraw.Draw(im)
for x in range((x0//step+1)*step,x1,step):
    X=(x-x0)*z;d.line([(X,0),(X,im.height)],fill=(255,0,255) if x%(step*5)==0 else (0,170,255),width=1)
    if x%(step*5)==0:d.text((X+2,2),str(x),fill=(255,0,255))
for y in range((y0//step+1)*step,y1,step):
    Y=(y-y0)*z;d.line([(0,Y),(im.width,Y)],fill=(255,0,255) if y%(step*5)==0 else (0,170,255),width=1)
    if y%(step*5)==0:d.text((2,Y+2),str(y),fill=(255,0,255))
im.save(out);print(out,im.size)
