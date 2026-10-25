import sys, json
sys.path.insert(0,'/home/claude/silk')
import parse
from shapely.geometry import LineString, Point, box, MultiLineString
from shapely.ops import unary_union
exec(open('/home/claude/gerb/chk.py').read().split("for side in")[0])
syms,texts,geo=parse.load()
M=geoms('MASK_TOP')
CL=0.10
BOARD=box(50.15,50.15,159.85,109.85)
targets=[]   # (ref, kind, match, edges, w)
for g in geo:
    if g['layer']!='PACKAGE GEOMETRY/SILKSCREEN_TOP': continue
    r=g['ref']
    if r in ('U11','U8','J1','J2','J3','J4','J12') and g['kind']=='G':
        (x0,y0),(x1,y1)=g['bb']
        targets.append(dict(ref=r,kind='G',bb=[[x0,y0],[x1,y1]],edges=[((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))],w=0.15))
    if r=='U1' and g['kind']=='L':
        targets.append(dict(ref=r,kind='L',se=g['se'],edges=[],w=0.15))   # replaced by custom marks
    if r=='J5' and g['kind']=='L' and (g['se'][0][1]==100.0 or g['se'][0][0]==146.6):
        targets.append(dict(ref=r,kind='L',se=g['se'],edges=[tuple(map(tuple,g['se']))],w=g['w']))
new=[]
for t in targets:
    for a,b in t['edges']:
        w=t['w']; ko=unary_union([m.buffer(CL+w/2,join_style=2) for m in M])
        ls=LineString([a,b]).intersection(BOARD.buffer(-w/2)).difference(ko)
        parts=[ls] if ls.geom_type=='LineString' else list(getattr(ls,'geoms',[]))
        for p in parts:
            if p.is_empty or p.length<0.3: continue
            (xa,ya),(xb,yb)=p.coords[0],p.coords[-1]
            new.append(dict(ref=t['ref'],a=(round(xa,4),round(ya,4)),b=(round(xb,4),round(yb,4)),w=w))
# U1 custom corner marks just outside the pad field + pin-1 dot
x0,y0,x1,y1=83.80,75.80,92.20,84.20; Lg=0.9
for (cx,cy,dx,dy) in [(x0,y1,1,-1),(x1,y1,-1,-1),(x1,y0,-1,1),(x0,y0,1,1)]:
    new.append(dict(ref='U1',a=(cx,cy),b=(cx+dx*Lg,cy),w=0.15)); new.append(dict(ref='U1',a=(cx,cy),b=(cx,cy+dy*Lg),w=0.15))
dots=[dict(ref='U1',xy=(83.30,82.60),d=0.35)]
# verify new geometry against mask
bad=0
for n in new:
    g=LineString([n['a'],n['b']]).buffer(n['w']/2)
    if any(g.intersects(m.buffer(0.05)) for m in M): print('BAD',n); bad+=1
for d in dots:
    g=Point(d['xy']).buffer(d['d']/2)
    if any(g.intersects(m.buffer(0.1)) for m in M): print('BAD dot',d); bad+=1
print('targets',len(targets),'new segs',len(new),'bad',bad)
for n in new: print(n)
json.dump(dict(targets=targets,new=new,dots=dots),open('clip_plan.json','w'),indent=1)
