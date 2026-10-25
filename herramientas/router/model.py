import re, math
from pads import load as load_pads
D='/mnt/user-data/uploads/projects--hub/'
Y1FIX={'SMD140X120':(0.7,0.6)}   # broken padstack -> intended 1.4x1.2 mm
def pad_geoms(p):
    """return list of (layer, kind, params) copper for a pin; layer 0=TOP 1=BOT"""
    out=[]
    for li,pd in ((0,p['top']),(1,p['bot'])):
        if not pd: continue
        f,(x0,y0,x1,y1)=pd
        if p['ps'] in Y1FIX:
            hx,hy=Y1FIX[p['ps']]; x0,y0,x1,y1=-hx,-hy,hx,hy
        X0,Y0,X1,Y1=p['x']+x0,p['y']+y0,p['x']+x1,p['y']+y1
        if f=='CIRCLE':
            out.append((li,'circ',(p['x'],p['y'],(x1-x0)/2)))
        elif f.startswith('OBLONG'):
            wx,wy=X1-X0,Y1-Y0
            if wx>=wy:
                r=wy/2; out.append((li,'cap',(X0+r,p['y'],X1-r,p['y'],r)))
            else:
                r=wx/2; out.append((li,'cap',(p['x'],Y0+r,p['x'],Y1-r,r)))
        else:
            out.append((li,'rect',(X0,Y0,X1,Y1)))
    return out
def load_segs(fn='claude_etch48.txt'):
    segs=[]; vias=[]
    for l in open(D+fn):
        m=re.match(r'SEG (\S+) ETCH/(\S+) ([-\d.]+) \(\(([-\d.]+) ([-\d.]+)\) \(([-\d.]+) ([-\d.]+)\)\)',l)
        if m:
            net,lay,w,x0,y0,x1,y1=m.groups()
            if lay in ('TOP','BOTTOM'):
                segs.append(dict(net=net,layer=0 if lay=='TOP' else 1,w=float(w),p0=(float(x0),float(y0)),p1=(float(x1),float(y1))))
        m=re.match(r'VIA (\S+) \(([-\d.]+) ([-\d.]+)\)',l)
        if m: vias.append(dict(net=m.group(1),x=float(m.group(2)),y=float(m.group(3))))
    return segs,vias
def board():
    pins,_=load_pads()
    segs,vias=load_segs()
    return pins,segs,vias
