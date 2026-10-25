import json, math
from shapely.geometry import box
import place as P
res,pend=P.solve()
assert not pend
placed={'T':[box(*r['box']).buffer(P.GAP_TXT) for r in res.values() if r['side']=='T'],'B':[box(*r['box']).buffer(P.GAP_TXT) for r in res.values() if r['side']=='B']}
# ---- free texts: connector labels next to the USB-C bodies ----
P.BLK['T1']=(0.9,1.2,0.25,0.18)
free=[]
for ref,lab in [('J12','J12 IN'),('J1','J1 OUT'),('J2','J2 OUT'),('J3','J3 OUT'),('J4','J4 OUT')]:
    c=P.comps[ref]
    best=None
    for blk in ('S1','S2'):
        w_,h_,cs_,pw_=P.BLK[blk]; L_=P.tlen(len(lab),blk)+pw_; H_=h_+pw_
        bx0,by0,bx1,by1=c['body'].bounds
        cl=[]
        import numpy as np
        for rot in (0,90):
            tw,th=(L_,H_) if rot==0 else (H_,L_)
            for d in np.arange(0.15,5.0,0.25):
                for f in np.arange(0,1.0001,0.05):
                    if ref=='J12': x=bx0+f*(bx1-bx0-tw); y=by0-d-th
                    elif ref in ('J1','J2'): x=bx1+d; y=by0+f*(by1-by0-th)
                    else: x=bx0+f*(bx1-bx0-tw); y=by1+d
                    cl.append((rot,box(x,y,x+tw,y+th),d+abs(f-0.5)))
                    if ref in ('J3','J4'):
                        yy=by0+f*(by1-by0-th)
                        cl.append((rot,box(bx0-d-tw,yy,bx0-d,yy+th),d+abs(f-0.5)+1))
                        cl.append((rot,box(bx1+d,yy,bx1+d+tw,yy+th),d+abs(f-0.5)+1))
        for rot,tb,pen in cl:
            if not P.static_ok(c,tb,0): continue
            if any(p.intersects(tb) for p in placed['T']): continue
            bx0,by0,bx1,by1=c['body'].bounds; tx0,ty0,tx1,ty1=tb.bounds
            inward={'J12':ty1<=by0,'J1':tx0>=bx1,'J2':tx0>=bx1,'J3':(rot==90 and tx0>=bx1),'J4':(rot==90 and tx1<=bx0)}[ref]
            if not inward: continue
            sc=P.score(c,rot,tb,pen)
            if best is None or sc<best[0]: best=(sc,rot,tb,blk)
        if best: break
    print(ref,best and best[0]); sc,rot,tb,blk=best
    placed['T'].append(tb.buffer(P.GAP_TXT))
    free.append(dict(text=lab,blk=blk,rot=rot,box=tb.bounds,side='T',near=ref))
# title: search the board for a free spot
def title(txt,blk,region):
    w,h,cs,pw=P.BLK[blk]; L=P.tlen(len(txt),blk); m=pw/2
    bw,bh=L+2*m,h+2*m
    best=None
    x0r,y0r,x1r,y1r=region
    import numpy as np
    for x in np.arange(x0r,x1r-bw,0.25):
        for y in np.arange(y0r,y1r-bh,0.25):
            tb=box(x,y,x+bw,y+bh)
            if not P.BOARD.contains(tb): continue
            if P.hits(P.TREE['T']['mask'],P.OB['T']['mask'],tb): continue
            if P.hits(P.TREE['T']['silk'],P.SG['T'],tb): continue
            if P.hits(P.TREE['T']['body'],P.BG['T'],tb.buffer(0.3)): continue
            if any(p.intersects(tb) for p in placed['T']): continue
            # prefer far from everything (centered in free space)
            d=min(g.distance(tb) for g in P.BG['T'])
            if best is None or d>best[0]: best=(d,tb)
    return best
b=title('USB-C HUB 1x4  USB5744','T1',(98,62,134,79))
tb=b[1]; placed['T'].append(tb.buffer(P.GAP_TXT)); free.append(dict(text='USB-C HUB 1x4  USB5744',blk='T1',rot=0,box=tb.bounds,side='T',near='-'))
txt='REV A  10/2026'; w,h,cs,pw=P.BLK['S1']; L=P.tlen(len(txt),'S1')+pw; cx=(tb.bounds[0]+tb.bounds[2])/2
rb=box(cx-L/2,tb.bounds[1]-0.35-(h+pw),cx+L/2,tb.bounds[1]-0.35)
ok=P.BOARD.contains(rb) and not P.hits(P.TREE['T']['mask'],P.OB['T']['mask'],rb) and not P.hits(P.TREE['T']['silk'],P.SG['T'],rb) and not P.hits(P.TREE['T']['body'],P.BG['T'],rb) and not any(p.intersects(rb) for p in placed['T'][:-1])
print('rev ok',ok,rb.bounds)
if ok: placed['T'].append(rb.buffer(P.GAP_TXT)); free.append(dict(text=txt,blk='S1',rot=0,box=rb.bounds,side='T',near='-'))
json.dump(dict(res=res,free=free),open('silk_plan.json','w'),indent=1)
print('free',free)
