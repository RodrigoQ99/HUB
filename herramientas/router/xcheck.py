import pickle, sys, math, numpy as np
from shapely.geometry import box, Point, LineString
from shapely.strtree import STRtree
from model import board, pad_geoms
from router import MOVES, KEEPIN, shp_obj
def check(segs, vias, clr=0.127-0.001):
    pins,oldsegs,oldvias=board()
    objs=[[],[]]   # (geom, net, desc)
    for p in pins:
        if p['ref'] in MOVES:
            dx,dy=MOVES[p['ref']]; p['x']+=dx; p['y']+=dy
        net=p['net'] or ('NC_'+p['ref']+p['num'])
        for li,k,g in pad_geoms(p):
            objs[li].append((shp_obj(k,g),net,'pad %s.%s'%(p['ref'],p['num'])))
        if p['drill']>0 and p['plat']=='NON_PLATED':
            for li in (0,1): objs[li].append((Point(p['x'],p['y']).buffer(p['drill']/2+0.0762,32),'NPTH','npth %s'%p['ref']))
    for s in list(oldsegs)+list(segs):
        g=LineString([s['p0'],s['p1']]).buffer(s['w']/2,16) if s['p0']!=s['p1'] else Point(s['p0']).buffer(s['w']/2,16)
        objs[s['layer']].append((g,s['net'],'seg %s'%s['net']))
    for v in vias:
        for li in (0,1): objs[li].append((Point(v['x'],v['y']).buffer(v.get('vr',0.3048),32),v['net'],'via %s'%v['net']))
    viol=[]
    for li in (0,1):
        gs=[o[0] for o in objs[li]]; tree=STRtree(gs)
        for i,(g,n,d) in enumerate(objs[li]):
            for j in tree.query(g.buffer(clr),predicate='intersects'):
                if j<=i: continue
                g2,n2,d2=objs[li][j]
                if n2==n: continue
                dist=g.distance(g2)
                if dist<clr: viol.append((li,round(dist,4),d,d2,tuple(round(c,2) for c in g.centroid.coords[0])))
    # keepin
    kb=box(*KEEPIN)
    for s in segs:
        g=LineString([s['p0'],s['p1']]).buffer(s['w']/2)
        if not kb.contains(g): viol.append((s['layer'],'keepin',s['net'],s['p0'],s['p1']))
    # via to via / drill spacing (hole to hole >= 0.25)
    holes=[(v['x'],v['y'],0.1651 if v.get('vr',0.3048)>0.3 else 0.1,v['net']) for v in vias]+[(p['x'],p['y'],p['drill']/2,p['net']) for p in pins if p['drill']>0]
    for i in range(len(holes)):
        for j in range(i+1,len(holes)):
            a=holes[i]; b=holes[j]
            d=math.hypot(a[0]-b[0],a[1]-b[1])-a[2]-b[2]
            if d<0.2: viol.append(('hole',round(d,3),a,b))
    return viol
if __name__=='__main__':
    segs,vias,_,af=pickle.load(open(sys.argv[1],'rb'))
    v=check(segs,vias)
    print('violations',len(v))
    for x in v[:40]: print(x)
