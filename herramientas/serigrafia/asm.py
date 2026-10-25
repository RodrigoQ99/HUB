import json
from shapely.geometry import box
from shapely.ops import unary_union
import place as P
asm={}
geo_by={}
for g in P.geo:
    if 'ASSEMBLY' in g['layer'] and g['layer'].startswith('PACKAGE'):
        if g['kind']=='L': pts=g['se']; gb=(min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts))
        else: (x0,y0),(x1,y1)=g['bb']; gb=(x0,y0,x1,y1)
        geo_by.setdefault(g['ref'],[]).append(gb)
SIZES=[1.5,1.2,1.0,0.8,0.6,0.45,0.35]
for t in P.texts:
    if t['layer'] not in ('REF DES/ASSEMBLY_TOP','REF DES/ASSEMBLY_BOTTOM'): continue
    r=t['ref']; c=P.comps.get(r)
    cb=c['body'].bounds if c else None
    if r in geo_by:
        bs=geo_by[r]; ab=(min(b[0] for b in bs),min(b[1] for b in bs),max(b[2] for b in bs),max(b[3] for b in bs))
        area=lambda b:(b[2]-b[0])*(b[3]-b[1])
        if cb and area(ab)<0.5*area(cb): ab=cb
    elif cb: ab=cb
    else: continue
    x0,y0,x1,y1=ab
    # clip to board for edge connectors
    x0,y0,x1,y1=max(x0,50.3),max(y0,50.3),min(x1,159.7),min(y1,109.7)
    W,H=x1-x0,y1-y0; cx,cy=(x0+x1)/2,(y0+y1)/2
    n=len(t['text'])
    side='B' if t['layer'].endswith('BOTTOM') else 'T'
    rot=0 if (W>=H*0.9 or side=='B') else 90
    lng,sht=(W,H) if rot==0 else (H,W)
    pick=SIZES[-1]
    for h in SIZES:
        L=n*0.75*h+(n-1)*0.2*h
        if L<=0.88*lng and h<=0.62*sht: pick=h; break
    h=pick; L=n*0.75*h+(n-1)*0.2*h
    if rot==0: ox,oy=cx,cy-h/2
    else: ox,oy=cx+h/2,cy
    asm[r]=dict(text=t['text'],side=side,rot=rot,h=h,origin=(round(ox,4),round(oy,4)),body=(x0,y0,x1,y1),L=L)
json.dump(asm,open('asm_plan.json','w'),indent=1)
from collections import Counter
print(len(asm),Counter(a['h'] for a in asm.values()))
print({k:v for k,v in asm.items() if k in ('U1','J12','J3','C75','R117','U14')})
