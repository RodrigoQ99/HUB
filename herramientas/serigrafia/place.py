import math, json, sys
from shapely.geometry import box, LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
from gerbonara import GerberFile
from gerbonara.utils import MM
from parse import load
syms,texts,geo=load()
BX0,BY0,BX1,BY1=50.0,50.0,160.0,110.0
EDGE=0.35
# text blocks (w,h,cs,pw)
BLK={'S1':(0.75,1.0,0.2,0.15),'S2':(0.6,0.8,0.15,0.15)}
def tlen(n,b):
    w,h,cs,pw=BLK[b]; return n*w+(n-1)*cs
# ---------- mask openings (vias excluded: same circle on both sides) ----------
def flashes(n):
    g=GerberFile.open('/mnt/user-data/uploads/projects--hub/%s.art'%n)
    out=[]
    for o in g.objects:
        (x0,y0),(x1,y1)=o.bounding_box(MM)
        out.append((round(o.x,3),round(o.y,3),str(o.aperture),(x0,y0,x1,y1)))
    return out
mt=flashes('MASK_TOP'); mb=flashes('MASK_BOTTOM')
VIAAP={'<circle aperture d=1.12 [mm]>','<circle aperture d=0.7 [mm]>'}
bset={(x,y,a) for x,y,a,_ in mb}; tset={(x,y,a) for x,y,a,_ in mt}
def masks(lst,other):
    return [box(*bb) for x,y,a,bb in lst if not (a in VIAAP and (x,y,a) in other)]
MASK={'T':masks(mt,bset),'B':masks(mb,tset)}
print('mask openings (no vias): top',len(MASK['T']),'bottom',len(MASK['B']))
# ---------- silk geometry ----------
def seggeom(g):
    w=g.get('w') or 0.0
    w=w if w>0 else 0.15
    if g['kind']=='L':
        (a,b)=g['se']; 
        if a==b: return Point(a).buffer(w/2)
        return LineString([a,b]).buffer(w/2)
    if g['kind']=='A':
        (s,e)=g['se']; c=g['c']; r=g['r']
        a0=math.atan2(s[1]-c[1],s[0]-c[0]); a1=math.atan2(e[1]-c[1],e[0]-c[0])
        if abs(s[0]-e[0])<1e-6 and abs(s[1]-e[1])<1e-6: return Point(c).buffer(r+w/2).difference(Point(c).buffer(max(r-w/2,0)))
        # unknown direction: use both? take ccw from a0 to a1
        if a1<=a0: a1+=2*math.pi
        pts=[(c[0]+r*math.cos(a0+(a1-a0)*i/24),c[1]+r*math.sin(a0+(a1-a0)*i/24)) for i in range(25)]
        return LineString(pts).buffer(w/2)
    if g['kind']=='G':
        (x0,y0),(x1,y1)=g['bb']; return box(x0,y0,x1,y1).exterior.buffer(0.075)
def side_of(layer): return 'B' if layer.endswith('BOTTOM') else 'T'
SILKG={'T':[],'B':[]}; PB={}  # place bounds per ref
for g in geo:
    L=g['layer']
    if 'SILKSCREEN' in L:
        SILKG[side_of(L)].append((g['ref'],seggeom(g)))
    if 'PLACE_BOUND' in L and g['kind']=='G':
        (x0,y0),(x1,y1)=g['bb']; PB.setdefault(g['ref'],[]).append(box(x0,y0,x1,y1))
# fixed silk texts that stay (not refdes, not deleted part-number texts)
DELTXT=[]
FIXT={'T':[],'B':[]}
for t in texts:
    L=t['layer']
    if L not in ('PACKAGE GEOMETRY/SILKSCREEN_TOP','BOARD GEOMETRY/SILKSCREEN_TOP','PACKAGE GEOMETRY/SILKSCREEN_BOTTOM','BOARD GEOMETRY/SILKSCREEN_BOTTOM'): continue
    if len(t['text'])>3: DELTXT.append(t); continue
    (x0,y0),(x1,y1)=t['bb']; FIXT[side_of(L)].append(box(x0,y0,x1,y1))
print('delete texts:',[(t['ref'],t['text']) for t in DELTXT])
# ---------- components ----------
comps={}
for r,s in syms.items():
    side='B' if s['mir'] else 'T'
    parts=[box(*p[0],*p[1]) for p in s['pins']]+PB.get(r,[])
    if not parts: continue
    body=unary_union(parts).envelope
    comps[r]=dict(ref=r,side=side,body=body,own=unary_union(parts))
refs=[t for t in texts if t['layer'] in ('REF DES/SILKSCREEN_TOP','REF DES/SILKSCREEN_BOTTOM')]
print('refdes texts',len(refs))
# ---------- placement ----------
GAP_MASK=0.12; GAP_SILK=0.10; GAP_TXT=0.20; GAP_BODY=0.15
def obst(side):
    o={}
    o['mask']=[m.buffer(GAP_MASK,join_style=2) for m in MASK[side]]
    o['silk']=[(r,g.buffer(GAP_SILK)) for r,g in SILKG[side]]+[('-',b.buffer(GAP_SILK)) for b in FIXT[side]]
    o['body']=[(r,c['own']) for r,c in comps.items() if c['side']==side]
    return o
OB={s:obst(s) for s in 'TB'}
TREE={}
for s in 'TB':
    TREE[s]=dict(mask=STRtree(OB[s]['mask']),silk=STRtree([g for _,g in OB[s]['silk']]),body=STRtree([g for _,g in OB[s]['body']]))
BOARD=box(BX0+EDGE,BY0+EDGE,BX1-EDGE,BY1-EDGE)
def hits(tree,geoms,g):
    idx=tree.query(g)
    return [i for i in idx if geoms[i].intersects(g)]
def cands(c,txt,blk,allow_rot90=True):
    w,h,cs,pw=BLK[blk]; m=pw/2
    L=tlen(len(txt),blk)
    x0,y0,x1,y1=c['body'].bounds; cx,cy=(x0+x1)/2,(y0+y1)/2
    out=[]
    rots=[0,90] if (allow_rot90 and c['side']=='T') else [0]
    for rot in rots:
        bw,bh=(L+2*m,h+2*m) if rot==0 else (h+2*m,L+2*m)
        G=GAP_BODY
        offs=[k*0.25 for k in range(-12,13)]
        for d in offs:
            # above / below
            out.append((rot,cx+d-bw/2,y1+G,abs(d)))
            out.append((rot,cx+d-bw/2,y0-G-bh,abs(d)))
            # left / right
            out.append((rot,x0-G-bw,cy+d-bh/2,abs(d)))
            out.append((rot,x1+G,cy+d-bh/2,abs(d)))
        for dd in (0.5,1.0,1.5):  # further away
            out.append((rot,cx-bw/2,y1+G+dd,dd*1.5)); out.append((rot,cx-bw/2,y0-G-bh-dd,dd*1.5))
            out.append((rot,x0-G-bw-dd,cy-bh/2,dd*1.5)); out.append((rot,x1+G+dd,cy-bh/2,dd*1.5))
    res=[]
    for rot,bx,by,pen in out:
        bw,bh=(L+2*m,h+2*m) if rot==0 else (h+2*m,L+2*m)
        res.append((rot,box(bx,by,bx+bw,by+bh),pen))
    return res
def feasible(c,tb,placed,level):
    s=c['side']; o=OB[s]; T=TREE[s]
    if not BOARD.contains(tb): return False
    if hits(T['mask'],o['mask'],tb): return False
    for p in placed[s]:
        if p.buffer(GAP_TXT).intersects(tb): return False
    if level<2:
        if hits(T['silk'],[g for _,g in o['silk']],tb): return False
        bh=hits(T['body'],[g for _,g in o['body']],tb)
        if bh: return False
    else:
        # allow crossing silk lines of own comp only, never other bodies' pads (mask covers)
        bh=[i for i in hits(T['body'],[g for _,g in o['body']],tb)]
        if bh: return False
    return True
def score(c,rot,tb,pen):
    s=c['side']
    d_own=tb.distance(c['own'])
    # ambiguity: nearest other body
    near=min((tb.distance(g) for r,g in OB[s]['body'] if r!=c['ref'] and g.distance(tb)<3.0),default=9)
    amb=0 if d_own<near-0.05 else 1.5+ (d_own-near)
    return d_own*2+pen*0.15+(0.35 if rot==90 else 0)+amb
SG={s:[g for _,g in OB[s]['silk']] for s in 'TB'}
BG={s:[g for _,g in OB[s]['body']] for s in 'TB'}
def static_ok(c,tb,lev):
    s=c['side']; o=OB[s]; T=TREE[s]
    if not BOARD.contains(tb): return False
    if hits(T['mask'],o['mask'],tb): return False
    if lev<2 and hits(T['silk'],SG[s],tb): return False
    if hits(T['body'],BG[s],tb): return False
    return True
def solve():
    placed={'T':[],'B':[]}; result={}
    levels=[('S1',0),('S2',0),('S2',2)]
    pending=[t for t in refs if t['ref'] in comps]
    for blk,lev in levels:
        opts={}
        for t in pending:
            c=comps[t['ref']]
            opts[t['ref']]=sorted([(score(c,rot,tb,pen),rot,tb) for rot,tb,pen in cands(c,t['text'],blk) if static_ok(c,tb,lev)],key=lambda x:x[0])
        while True:
            live={}
            for t in pending:
                r=t['ref']; s=comps[r]['side']
                fs=[x for x in opts[r] if not any(p.intersects(x[2]) for p in placed[s])]
                opts[r]=fs
                if fs: live[r]=fs
            if not live: break
            r=min(live,key=lambda k:(len(live[k]),live[k][0][0]))
            sc,rot,tb=live[r][0]
            t=[x for x in pending if x['ref']==r][0]; c=comps[r]
            placed[c['side']].append(tb.buffer(GAP_TXT)); result[r]=dict(blk=blk,rot=rot,box=tb.bounds,score=sc,side=c['side'],text=t['text'],level=lev)
            pending=[x for x in pending if x['ref']!=r]
        print('after',blk,lev,'placed',len(result),'pending',len(pending))
    return result,pending
if __name__=='__main__':
    res,pend=solve()
    print('UNPLACED',[t['ref'] for t in pend])
    json.dump(dict(res=res,unplaced=[t['ref'] for t in pend]),open('silk_plan.json','w'),indent=1)
