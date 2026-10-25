# hand-planned escapes for the U1 top-left pocket (pins 52-56)
from router import *
W0=0.127
MAN={
 'TESTEN':  [[(87.0,83.4),(87.0,84.178),(84.56,86.618),(84.56,91.9),(83.95,91.9)]],
 'N208498': [[(86.6,83.4),(86.6,84.153),(84.26,86.493),(84.26,89.65),(83.1,89.65)]],
 'N210668': [[(86.2,83.4),(86.2,84.129),(83.379,86.95),(81.3,86.95),(80.9,87.95)]],
 'RBIAS':   [[(85.4,83.4),(85.4,84.0),(83.45,84.0)]],
 'VDD33':   [[(85.8,83.4),(85.8,84.15),(85.35,84.6),(85.0,84.6)]],
 'N18966':  [[(91.4,82.2),(92.25,82.2),(94.25,84.2),(100.9,84.2),(100.9,80.2749),(104.6702,80.2749)]],
 'N18954':  [[(91.4,81.8),(92.274,81.8),(94.374,83.9),(100.6,83.9),(100.6,78.3242),(104.6702,78.3242)]],
 'N18947':  [[(91.4,81.4),(92.299,81.4),(94.499,83.6),(100.3,83.6),(100.3,78.9744),(98.9298,78.9744)]],
 'N18933':  [[(91.4,81.0),(92.323,81.0),(94.623,83.3),(100.0,83.3),(100.0,80.9251),(98.9298,80.9251)]],
 'VBUS_DET':[[(91.4,80.6),(93.9,80.6),(94.454,80.398)],[(94.454,80.398),(94.454,78.547)],[(94.454,80.398),(94.454,81.3),(95.5208,82.198)]],
}
MANVIA={'VDD33':[(85.0,84.6,VR2)]}
MANBOT={'VDD33':[[(85.0,84.6),(85.498,84.754)]]}
def apply_manual(R,check_only=False):
    B=R.B; bad=[]
    for net,polys in MAN.items():
        nid=B.nid[net]
        for poly in polys:
            for a,b in zip(poly[:-1],poly[1:]):
                if not B.seg_clear(a,b,W0,0,nid): bad.append((net,a,b))
    for net,vs in MANVIA.items():
        for x,y,vr in vs:
            if not B.via_clear(x,y,B.nid[net],vr): bad.append((net,'via',x,y))
    for net,polys in MANBOT.items():
        for poly in polys:
            for a,b in zip(poly[:-1],poly[1:]):
                if not B.seg_clear(a,b,0.2,1,B.nid[net]): bad.append((net,'bot',a,b))
    if check_only: return bad
    for net,polys in MAN.items():
        nid=B.nid[net]; tc=R.tree_cells[nid]
        if net=='VDD33': B.tag=('U1','55')
        for poly in polys:
            for a,b in zip(poly[:-1],poly[1:]):
                B.commit_seg(a,b,W0,0,nid)
                n=max(1,int(math.hypot(b[0]-a[0],b[1]-a[1])/RES*2))
                for t in np.linspace(0,1,n+1): tc.add((0,)+c2i(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
        B.tag=None
    for net,vs in MANVIA.items():
        nid=B.nid[net]; B.tag=('U1','55') if net=='VDD33' else None
        for x,y,vr in vs:
            B.commit_via(x,y,nid,vr); iy,ix=c2i(x,y); R.tree_cells[nid].add((0,iy,ix)); R.tree_cells[nid].add((1,iy,ix))
        B.tag=None
    for net,polys in MANBOT.items():
        nid=B.nid[net]; B.tag=('U1','55')
        for poly in polys:
            for a,b in zip(poly[:-1],poly[1:]): B.commit_seg(a,b,0.2,1,nid)
        B.tag=None
    B.rebuild_tree()
    return bad
