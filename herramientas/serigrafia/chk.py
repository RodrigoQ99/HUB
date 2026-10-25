import math
from gerbonara import GerberFile
from gerbonara.utils import MM
from gerbonara.graphic_objects import Line, Arc, Flash, Region
from shapely.geometry import LineString, Point, box, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
src='/mnt/user-data/uploads/projects--hub/'
def geoms(n):
    g=GerberFile.open(src+n+'.art'); out=[]
    for o in g.objects:
        if isinstance(o,Line):
            w=getattr(o.aperture,'diameter',0.1) or 0.1
            ls=LineString([(o.x1,o.y1),(o.x2,o.y2)]) if (o.x1,o.y1)!=(o.x2,o.y2) else Point(o.x1,o.y1)
            out.append(ls.buffer(w/2))
        elif isinstance(o,Arc):
            w=getattr(o.aperture,'diameter',0.1) or 0.1
            ls=o.approximate(max_error=0.01)
            pts=[(ls[0].x1,ls[0].y1)]+[(l.x2,l.y2) for l in ls]
            out.append(LineString(pts).buffer(w/2) if len(pts)>1 else Point(pts[0]).buffer(w/2))
        elif isinstance(o,Flash):
            (x0,y0),(x1,y1)=o.bounding_box(MM); out.append(box(x0,y0,x1,y1))
        elif isinstance(o,Region):
            try: out.append(Polygon(o.outline))
            except Exception: pass
    return out
for side in ('TOP','BOTTOM'):
    S=geoms('SILK_'+side); M=geoms('MASK_'+side)
    tree=STRtree(M)
    hits=[]
    for s in S:
        for i in tree.query(s):
            if M[i].intersects(s): hits.append((s,M[i]))
    print(side,'silk objs',len(S),'mask',len(M),'silk-on-mask overlaps',len(hits))
    pts=sorted({(round(m.centroid.x,1),round(m.centroid.y,1)) for s,m in hits})
    print(pts[:80])
