import numpy as np, math, json, time, collections, sys
from router import *

def pad_cells(k,g,inner_min=0.0):
    bb=bbox_obj(k,g); 
    ix0=max(0,int(math.floor((bb[0]-X0)/RES))); ix1=min(W,int(math.ceil((bb[2]-X0)/RES))+1)
    iy0=max(0,int(math.floor((bb[1]-Y0)/RES))); iy1=min(H,int(math.ceil((bb[3]-Y0)/RES))+1)
    XX,YY=np.meshgrid(XS[ix0:ix1],YS[iy0:iy1])
    inn=inner_obj(k,g,XX,YY)>=inner_min
    ys,xs=np.nonzero(inn)
    return ys+iy0, xs+ix0

class Router:
    def __init__(self):
        self.B=Board(); self.log=[]; self.viol=[]
        self.tree_cells=collections.defaultdict(set)   # nid -> set of (l,y,x) own routed copper centreline cells
        self.esc={}
        self.via_cost=float(__import__('os').environ.get('VIACOST','20'))
    def pin_cells(self,p):
        out=list(self.esc.get((p['ref'],p['num']),()))
        for li,k,g in p['geoms']:
            ys,xs=pad_cells(k,g)
            out+= [(li,y,x) for y,x in zip(ys,xs)]
        return out
    def run_astar(self,nid,w,srcs,tgt_cells,single_layer=None,margin=4.0,via_cost=20,tgt_mask_extra=None,allow_via=True,penal=None):
        B=self.B
        dother=B.dist_other(nid)
        cost=None
        if penal is not None:
            # penal = (hard_dother, soft_dother): free on hard, penalty where soft blocks
            hd,sd=penal
            free=B.free_mask(nid,w,hd)
            cost=np.where(sd<w/2+CLRA,60.0,0.0)
            viaok=B.via_mask(nid,hd)&free[0]&free[1]
        else:
            free=B.free_mask(nid,w,dother)
            viaok=(B.via_mask(nid,dother)|(B.zone_small&B.via_mask(nid,dother,VR2)))&free[0]&free[1] if allow_via else np.zeros((H,W),bool)
        srcs=[c for c in srcs if free[c]]
        if tgt_mask_extra is not None:
            tm=tgt_mask_extra&free
        else:
            tm=np.zeros((2,H,W),bool)
            for c in tgt_cells: tm[c]=True
            tm&=free
        if single_layer is not None:
            free=free.copy(); free[1-single_layer]=False; viaok=np.zeros((H,W),bool)
            srcs=[c for c in srcs if c[0]==single_layer]; tm[1-single_layer]=False
        if not srcs or not tm.any(): return None,'nosrc' if not srcs else 'notgt'
        sy=[c[1] for c in srcs]; sx=[c[2] for c in srcs]
        tl,tyy,txx=np.nonzero(tm)
        m=int(margin/RES)
        y0=max(0,min(min(sy),tyy.min())-m); y1=min(H,max(max(sy),tyy.max())+m+1)
        x0=max(0,min(min(sx),txx.min())-m); x1=min(W,max(max(sx),txx.max())+m+1)
        fr=np.ascontiguousarray(free[:,y0:y1,x0:x1]); vo=np.ascontiguousarray(viaok[y0:y1,x0:x1]); tg=np.ascontiguousarray(tm[:,y0:y1,x0:x1])
        S=np.array([(l,y-y0,x-x0) for l,y,x in srcs],dtype=np.int64)
        cw=np.zeros(fr.shape) if cost is None else np.ascontiguousarray(cost[:,y0:y1,x0:x1])
        # heuristic bbox of targets (window coords)
        idx,par=astar(fr,vo,tg,S,int(tyy.min()-y0),int(txx.min()-x0),int(tyy.max()-y0),int(txx.max()-x0),float(via_cost),1.15,np.array([1.0,1.0]),cw)
        if idx<0: return None,'noroute'
        Hh,Ww=fr.shape[1],fr.shape[2]
        path=[]
        while idx>=0:
            l=idx//(Hh*Ww); rem=idx%(Hh*Ww); y=rem//Ww; x=rem%Ww
            path.append((int(l),int(y+y0),int(x+x0)))
            idx=par[l,y,x]
        return path[::-1],'ok'
    def emit(self,nid,w,path,start_pt=None,end_pt=None,end_via=False,end_vr=VR):
        """convert cell path to segments/vias with string pulling; commit"""
        B=self.B
        runs=[]; cur=[path[0]]
        for c in path[1:]:
            if c[0]!=cur[-1][0]:
                runs.append(cur); cur=[c]
            else: cur.append(c)
        runs.append(cur)
        allsegs=[]; vias=[]
        for ri,run in enumerate(runs):
            l=run[0][0]
            pts=[i2c(y,x) for _,y,x in run]
            if ri==0 and start_pt and B.seg_clear(start_pt,pts[0],w,l,nid): pts=[start_pt]+pts
            if ri==len(runs)-1 and end_pt and B.seg_clear(pts[-1],end_pt,w,l,nid): pts=pts+[end_pt]
            # collinear merge
            v=[pts[0]]
            for i in range(1,len(pts)-1):
                a,b,c=v[-1],pts[i],pts[i+1]
                if abs((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))>1e-9: v.append(b)
            if len(pts)>1: v.append(pts[-1])
            # string pull
            out=[v[0]]; i=0
            while i<len(v)-1:
                j=len(v)-1
                while j>i+1 and not B.seg_clear(v[i],v[j],w,l,nid): j-=1
                if j==i+1 and not B.seg_clear(v[i],v[j],w,l,nid):
                    self.viol.append(('seg',B.names.get(nid),l,v[i],v[j],w))
                out.append(v[j]); i=j
            for a,b in zip(out[:-1],out[1:]):
                if a!=b: allsegs.append((a,b,l))
            if ri<len(runs)-1:
                vx,vy=pts[-1]; vias.append((vx,vy))
        vrs=[]
        for vx,vy in vias:
            if B.via_clear(vx,vy,nid): vrs.append(VR)
            elif B.via_clear(vx,vy,nid,VR2): vrs.append(VR2)
            else: vrs.append(VR2); self.viol.append(('via',B.names.get(nid),vx,vy))
        for a,b,l in allsegs: B.commit_seg(a,b,w,l,nid)
        for (vx,vy),vr in zip(vias,vrs): B.commit_via(vx,vy,nid,vr)
        if end_via:
            vx,vy=end_via
            if not B.via_clear(vx,vy,nid,end_vr): self.viol.append(('via',B.names.get(nid),vx,vy))
            B.commit_via(vx,vy,nid,end_vr)
        # tree cells
        tc=self.tree_cells[nid]
        for a,b,l in allsegs:
            n=max(1,int(math.hypot(b[0]-a[0],b[1]-a[1])/RES*2))
            for t in np.linspace(0,1,n+1):
                x=a[0]+(b[0]-a[0])*t; y=a[1]+(b[1]-a[1])*t
                tc.add((l,)+c2i(x,y))
        for vx,vy in vias+([end_via] if end_via else []):
            iy,ix=c2i(vx,vy)
            for l in (0,1): tc.add((l,iy,ix))
        return len(allsegs),len(vias)
    # ------------------------------------------------------------
    def fanout(self,p,widths=(0.4,0.3,0.2),margin=3.0,vr=VR):
        B=self.B; nid=p['nid']; vr_used=vr
        res=None
        for li,k,g in p['geoms']:
            pass
        li,k,g=p['geoms'][0]
        srcs=[(li,y,x) for y,x in zip(*pad_cells(k,g))]
        for w in widths:
            dother=B.dist_other(nid)
            vm=B.via_mask(nid,dother,vr)
            tm=np.zeros((2,H,W),bool); tm[li]=vm
            # existing own vias as targets
            for v in B.vias:
                if B.nid.get(v['net'])==nid:
                    iy,ix=c2i(v['x'],v['y']); tm[li,iy-3:iy+4,ix-3:ix+4]=True
            path,st=self.run_astar(nid,w,srcs,None,single_layer=li,margin=margin,tgt_mask_extra=tm,allow_via=False)
            if path is None and vr==VR:
                vm2=B.via_mask(nid,dother,VR2); tm2=np.zeros((2,H,W),bool); tm2[li]=vm2|tm[li]
                path,st=self.run_astar(nid,w,srcs,None,single_layer=li,margin=margin,tgt_mask_extra=tm2,allow_via=False)
                if path is not None:
                    l,iy,ix=path[-1]
                    if not vm[iy,ix]: vr_used=VR2
            if path is None: continue
            l,iy,ix=path[-1]; vx,vy=i2c(iy,ix)
            ex=None
            for v in B.vias:
                if B.nid.get(v['net'])==nid and math.hypot(v['x']-vx,v['y']-vy)<0.2: ex=(v['x'],v['y'])
            B.tag=(p['ref'],p['num'])
            if ex: self.emit(nid,w,path,start_pt=(p['x'],p['y']),end_pt=ex)
            else: self.emit(nid,w,path,start_pt=(p['x'],p['y']),end_pt=(vx,vy),end_via=(vx,vy),end_vr=vr_used)
            B.tag=None
            return w
        return None
    def route_net(self,name,widths,margin_list=(4.0,12.0,40.0)):
        B=self.B; nid=B.nid[name]
        pins=[p for p in B.pins if p['nid']==nid]
        pins.sort(key=lambda p:(0 if p['ref']=='U1' else 1))
        conn=[pins[0]]; todo=pins[1:]
        tc=self.tree_cells[nid]
        for c in self.pin_cells(pins[0]): tc.add(c)
        fails=[]
        while todo:
            # nearest pin to connected set
            def dmin(p): return min(math.hypot(p['x']-q['x'],p['y']-q['y']) for q in conn)
            todo.sort(key=dmin)
            p=todo.pop(0)
            tcells=self.pin_cells(p)
            ok=False
            for margin in margin_list:
                for w in widths:
                    path,st=self.run_astar(nid,w,list(tc),tcells,margin=margin,via_cost=self.via_cost)
                    if path is None: continue
                    if len(path)<=1: ok=True; break
                    sp=None
                    # snap start to pin centre if path starts in a pin pad
                    for q in conn:
                        for li,k,g in q['geoms']:
                            if li==path[0][0]:
                                x,y=i2c(path[0][1],path[0][2])
                                if inner_obj(k,g,np.array(x),np.array(y))>=0: sp=(q['x'],q['y'])
                    self.emit(nid,w,path,start_pt=sp,end_pt=(p['x'],p['y']))
                    ok=True; break
                if ok: break
            if ok:
                conn.append(p)
                for c in tcells: tc.add(c)
            else:
                fails.append(p['ref']+'.'+p['num'])
        B.rebuild_tree()
        return fails
