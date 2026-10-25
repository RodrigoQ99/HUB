import json, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import place as P
PL=json.load(open('silk_plan.json')); plan=PL['res']
for side in 'TB':
    fig,ax=plt.subplots(figsize=(22,12.5),dpi=110)
    ax.add_patch(Rectangle((50,50),110,60,fill=False,ec='k'))
    for m in P.MASK[side]:
        x0,y0,x1,y1=m.bounds; ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,color='#d4a017',lw=0))
    for r,g in P.SILKG[side]:
        try:
            polys=[g] if g.geom_type=='Polygon' else list(g.geoms)
            for pg in polys:
                xs,ys=pg.exterior.xy; ax.fill(xs,ys,color='#888',lw=0)
                for it in pg.interiors:
                    xs,ys=it.xy; ax.fill(xs,ys,color='w',lw=0)
        except Exception as e: pass
    for b in P.FIXT[side]:
        x0,y0,x1,y1=b.bounds; ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='m',lw=0.5))
    for r,c in P.comps.items():
        if c['side']!=side: continue
        x0,y0,x1,y1=c['body'].bounds; ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='#9cf',lw=0.4))
    for r,p in plan.items():
        if p['side']!=side: continue
        x0,y0,x1,y1=p['box']
        col='g' if p['blk']=='S1' else ('orange' if p['level']==0 else 'r')
        ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec=col,lw=0.8))
        ax.text((x0+x1)/2,(y0+y1)/2,p['text'],ha='center',va='center',fontsize=5.5 if p['rot']==0 else 5,rotation=p['rot'],color='k')
        c=P.comps[r]['body'].centroid
        ax.plot([c.x,(x0+x1)/2],[c.y,(y0+y1)/2],color='r',lw=0.25)
    for p in PL['free']:
        if p['side']!=side: continue
        x0,y0,x1,y1=p['box']; ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='b',lw=0.8))
        ax.text((x0+x1)/2,(y0+y1)/2,p['text'],ha='center',va='center',fontsize=5.5,rotation=p['rot'],color='b')
    ax.set_xlim(49,161); ax.set_ylim(49,111); ax.set_aspect('equal')
    if side=='B': ax.invert_xaxis()
    plt.tight_layout(); plt.savefig('prev_%s.png'%side)
