import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import collections, sys
from model import *
def draw(fn, extra_segs=(), extra_vias=(), rats=True, region=None, dpi=150):
    pins,segs,vias=board()
    fig,ax=plt.subplots(figsize=(22,12))
    ax.set_aspect('equal'); ax.add_patch(Rectangle((50,50),110,60,fill=False,ec='k'))
    col={0:'#c33',1:'#33c'}
    for p in pins:
        for li,k,g in pad_geoms(p):
            c=col[li]
            if k=='rect': ax.add_patch(Rectangle((g[0],g[1]),g[2]-g[0],g[3]-g[1],fc=c,alpha=.45,ec='none'))
            elif k=='circ': ax.add_patch(Circle((g[0],g[1]),g[2],fc=c,alpha=.45))
            else:
                ax.plot([g[0],g[2]],[g[1],g[3]],color=c,lw=g[4]*2*72/25.4*fig.dpi/100*0.3,alpha=.45,solid_capstyle='round')
        if p['drill']>0: ax.add_patch(Circle((p['x'],p['y']),p['drill']/2,fc='w',ec='k',lw=.3))
    for s in list(segs)+list(extra_segs):
        ax.plot([s['p0'][0],s['p1'][0]],[s['p0'][1],s['p1'][1]],color=col[s['layer']],lw=max(.4,s['w']*8),alpha=.8)
    for v in list(vias)+list(extra_vias):
        ax.add_patch(Circle((v['x'],v['y']),0.305,fc='#0a0',alpha=.8))
    if rats:
        nets=collections.defaultdict(list)
        for p in pins:
            if p['net'] and p['net'] not in ('GND','5V'): nets[p['net']].append(p)
        routed={s['net'] for s in segs}
        for n,ps in nets.items():
            if n in routed: continue
            # mst
            pts=[(p['x'],p['y']) for p in ps]; inn=[0]; out=list(range(1,len(pts)))
            while out:
                b=min(((i,j) for i in inn for j in out),key=lambda ij:(pts[ij[0]][0]-pts[ij[1]][0])**2+(pts[ij[0]][1]-pts[ij[1]][1])**2)
                ax.plot([pts[b[0]][0],pts[b[1]][0]],[pts[b[0]][1],pts[b[1]][1]],'c-',lw=.4)
                inn.append(b[1]); out.remove(b[1])
    refs={}
    for p in pins: refs.setdefault(p['ref'],[]).append((p['x'],p['y']))
    for r,l in refs.items():
        x=sum(a for a,b in l)/len(l); y=sum(b for a,b in l)/len(l); ax.text(x,y,r,fontsize=5,ha='center',va='center',clip_on=True)
    if region: ax.set_xlim(region[0],region[2]); ax.set_ylim(region[1],region[3])
    else: ax.set_xlim(49,161); ax.set_ylim(49,111)
    fig.savefig(fn,dpi=dpi,bbox_inches='tight'); plt.close(fig)
if __name__=='__main__':
    draw('/tmp/claude-0/-home-claude/7ceff8d4-14f9-5947-b5dc-30cd7969ca45/scratchpad/board0.png')
