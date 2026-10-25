import numpy as np, math, heapq, collections, json, time
from numba import njit
from shapely.geometry import box, Point, LineString
from shapely.strtree import STRtree
from model import board, pad_geoms

RES=0.05; X0=50.0; Y0=50.0; W=2201; H=1201
KEEPIN=(50.5,50.5,159.5,109.5)
CLR=0.127; CLRA=CLR+0.02; CAP=1.5
VR=0.3048; VR2=0.225; VIA_ANNULAR_SMD=0.10
HS_EXTRA=0.15
MOVES={'R117':(0.5,6.5)}
import os as _os, json as _json
MOVES.update(_json.loads(_os.environ.get('XMOVES','{}')))
EXITL=0.35
XS=X0+np.arange(W)*RES; YS=Y0+np.arange(H)*RES

def c2i(x,y): return int(round((y-Y0)/RES)), int(round((x-X0)/RES))
def i2c(iy,ix): return (round(X0+ix*RES,4), round(Y0+iy*RES,4))

def dist_obj(kind,g,XX,YY):
    if kind=='rect':
        x0,y0,x1,y1=g
        dx=np.maximum(np.maximum(x0-XX,0),XX-x1); dy=np.maximum(np.maximum(y0-YY,0),YY-y1)
        return np.hypot(dx,dy)
    if kind=='circ':
        cx,cy,r=g; return np.maximum(np.hypot(XX-cx,YY-cy)-r,0)
    if kind=='cap':
        ax,ay,bx,by,r=g
        vx,vy=bx-ax,by-ay; L2=vx*vx+vy*vy
        if L2<1e-12: t=0*XX
        else: t=np.clip(((XX-ax)*vx+(YY-ay)*vy)/L2,0,1)
        return np.maximum(np.hypot(XX-(ax+t*vx),YY-(ay+t*vy))-r,0)
def bbox_obj(kind,g):
    if kind=='rect': return g
    if kind=='circ': return (g[0]-g[2],g[1]-g[2],g[0]+g[2],g[1]+g[2])
    if kind=='cap':
        ax,ay,bx,by,r=g; return (min(ax,bx)-r,min(ay,by)-r,max(ax,bx)+r,max(ay,by)+r)
def shp_obj(kind,g):
    if kind=='rect': return box(*g)
    if kind=='circ': return Point(g[0],g[1]).buffer(g[2],32)
    if kind=='cap':
        ax,ay,bx,by,r=g
        if abs(ax-bx)+abs(ay-by)<1e-9: return Point(ax,ay).buffer(r,32)
        return LineString([(ax,ay),(bx,by)]).buffer(r,32)
def inner_obj(kind,g,XX,YY):
    """signed inside distance (>0 inside)"""
    if kind=='rect':
        x0,y0,x1,y1=g; return np.minimum(np.minimum(XX-x0,x1-XX),np.minimum(YY-y0,y1-YY))
    if kind=='circ':
        return g[2]-np.hypot(XX-g[0],YY-g[1])
    if kind=='cap':
        ax,ay,bx,by,r=g; return r-(dist_obj('cap',(ax,ay,bx,by,0),XX,YY))

class Board:
    def __init__(self):
        self.d1=np.full((2,H,W),CAP,np.float32); self.d2=np.full((2,H,W),CAP,np.float32)
        self.n1=np.zeros((2,H,W),np.int32)
        self.dv=np.full((H,W),CAP,np.float32)      # distance to nearest via/drill centre (any net)
        self.dsmd=np.full((H,W),CAP,np.float32)    # distance to nearest SMD pad (any)
        self.nid={}; self.names={}
        self.geoms=[[],[]]   # (shapely, netid)
        self.vias=[]; self.segs=[]   # new routing
        self.pads={}   # netid -> list of (layer,kind,g,pin)
        self.pins,self.oldsegs,self.oldvias=board()
        for p in self.pins:
            if p['ref'] in MOVES:
                dx,dy=MOVES[p['ref']]; p['x']=round(p['x']+dx,4); p['y']=round(p['y']+dy,4)
        self.uniq=100000
        self.build()
    def netid(self,name):
        if name is None:
            self.uniq+=1; return self.uniq
        if name not in self.nid:
            i=len(self.nid)+1; self.nid[name]=i; self.names[i]=name
        return self.nid[name]
    def _win(self,bb,cap=CAP):
        ix0=max(0,int(math.floor((bb[0]-cap-X0)/RES))); ix1=min(W,int(math.ceil((bb[2]+cap-X0)/RES))+1)
        iy0=max(0,int(math.floor((bb[1]-cap-Y0)/RES))); iy1=min(H,int(math.ceil((bb[3]+cap-Y0)/RES))+1)
        return iy0,iy1,ix0,ix1
    def add(self,layer,nid,kind,g,extra=0.0,shape=True):
        bb=bbox_obj(kind,g); iy0,iy1,ix0,ix1=self._win(bb)
        XX,YY=np.meshgrid(XS[ix0:ix1],YS[iy0:iy1])
        d=(dist_obj(kind,g,XX,YY)-extra).astype(np.float32)
        d=np.maximum(d,-1)
        d1=self.d1[layer,iy0:iy1,ix0:ix1]; d2=self.d2[layer,iy0:iy1,ix0:ix1]; n1=self.n1[layer,iy0:iy1,ix0:ix1]
        same=(n1==nid)
        closer=(~same)&(d<d1)
        nd2=np.where(closer,d1,np.where(~same,np.minimum(d2,d),d2))
        nd1=np.where(same,np.minimum(d1,d),np.where(closer,d,d1))
        nn1=np.where(closer,nid,n1)
        self.d1[layer,iy0:iy1,ix0:ix1]=nd1; self.d2[layer,iy0:iy1,ix0:ix1]=nd2; self.n1[layer,iy0:iy1,ix0:ix1]=nn1
        if shape: self.geoms[layer].append((shp_obj(kind,g),nid))
    def add_point_field(self,arr,x,y,r=0.0):
        iy0,iy1,ix0,ix1=self._win((x,y,x,y))
        XX,YY=np.meshgrid(XS[ix0:ix1],YS[iy0:iy1])
        d=np.maximum(np.hypot(XX-x,YY-y)-r,0).astype(np.float32)
        arr[iy0:iy1,ix0:ix1]=np.minimum(arr[iy0:iy1,ix0:ix1],d)
    def add_smd_field(self,kind,g):
        bb=bbox_obj(kind,g); iy0,iy1,ix0,ix1=self._win(bb)
        XX,YY=np.meshgrid(XS[ix0:ix1],YS[iy0:iy1])
        d=dist_obj(kind,g,XX,YY).astype(np.float32)
        self.dsmd[iy0:iy1,ix0:ix1]=np.minimum(self.dsmd[iy0:iy1,ix0:ix1],d)
    def build(self):
        HSN={s['net'] for s in self.oldsegs}
        self.hsnets=HSN
        for p in self.pins:
            nid=self.netid(p['net']); p['nid']=nid
            gs=pad_geoms(p); p['geoms']=gs
            for li,k,g in gs:
                self.add(li,nid,k,g)
                self.pads.setdefault(nid,[]).append((li,k,g,p))
                if p['drill']==0: self.add_smd_field(k,g)
            if p['drill']>0:
                r=p['drill']/2
                if p['plat']=='NON_PLATED':
                    hid=self.netid(None)
                    for li in (0,1): self.add(li,hid,'circ',(p['x'],p['y'],r+0.0762))
                self.add_point_field(self.dv,p['x'],p['y'],r)
        zones=[(81.5,73.5,94.5,86.5)]
        for r in ('J1','J2','J3','J4','J12'):
            xs=[p['x'] for p in self.pins if p['ref']==r]; ys=[p['y'] for p in self.pins if p['ref']==r]
            zones.append((min(xs)-1.5,min(ys)-1.5,max(xs)+1.5,max(ys)+1.5))
        def inz(pt): return any(z[0]<=pt[0]<=z[2] and z[1]<=pt[1]<=z[3] for z in zones)
        for s in self.oldsegs:
            nid=self.netid(s['net'])
            g=(s['p0'][0],s['p0'][1],s['p1'][0],s['p1'][1],s['w']/2)
            ex=0.0 if (inz(s['p0']) or inz(s['p1'])) else HS_EXTRA
            self.add(s['layer'],nid,'cap',g,extra=ex if s['net'] in HSN else 0.0)
        # exit corridors in front of U1 non-HS pins (owned by the pin's net)
        for p in self.pins:
            if p['ref']!='U1' or p['net'] in HSN or p['net'] in (None,'GND'): continue
            if p['net']=='VDD12' and p['num'] not in ('43','28'): continue
            x,y=p['x'],p['y']; L0,L1=0.375,0.375+EXITL; hw=0.127
            if abs(y-83.4)<1e-6: r=(x-hw,y+L0,x+hw,y+L1)
            elif abs(y-76.6)<1e-6: r=(x-hw,y-L1,x+hw,y-L0)
            elif abs(x-84.6)<1e-6: r=(x-L1,y-hw,x-L0,y+hw)
            else: r=(x+L0,y-hw,x+L1,y+hw)
            self.add(0,p['nid'],'rect',r)
        # keepout under U1 body between pin ring and EP (TOP): owned by VDD12 so only VDD12 may use the inner ring
        self.add(0,self.netid('VDD12'),'rect',(85.2,77.2,90.8,82.8))
        from matplotlib.path import Path as _P
        XXg,YYg=np.meshgrid(XS,YS)
        pocket=_P([(84.6,83.8),(87.45,83.8),(85.4,86.75),(84.6,86.75)])
        self.via_keepout=pocket.contains_points(np.c_[XXg.ravel(),YYg.ravel()]).reshape(H,W)
        self.zone_small=np.zeros((H,W),bool)
        iy0,ix0=c2i(82.0,74.0); iy1,ix1=c2i(95.0,86.0)
        self.zone_small[iy0:iy1,ix0:ix1]=True
        for v in self.oldvias:
            nid=self.netid(v['net'])
            for li in (0,1): self.add(li,nid,'circ',(v['x'],v['y'],VR))
            self.add_point_field(self.dv,v['x'],v['y'],VR)
        XX,YY=np.meshgrid(XS,YS)
        self.edge=np.minimum(np.minimum(XX-KEEPIN[0],KEEPIN[2]-XX),np.minimum(YY-KEEPIN[1],KEEPIN[3]-YY)).astype(np.float32)
        self.rebuild_tree()
    def rebuild_tree(self):
        self.tree=[STRtree([g for g,n in self.geoms[l]]) for l in (0,1)]
        self.tnet=[np.array([n for g,n in self.geoms[l]]) for l in (0,1)]
        self.extra=[[],[]]
    def dist_other(self,nid):
        return np.where(self.n1==nid,self.d2,self.d1)
    def free_mask(self,nid,w,dother=None):
        if dother is None: dother=self.dist_other(nid)
        fr=(dother>=w/2+CLRA)&(self.edge[None]>=w/2+0.05)
        # inner own pads
        for li,k,g,p in self.pads.get(nid,[]):
            bb=bbox_obj(k,g); iy0,iy1,ix0,ix1=self._win(bb,0.1)
            XX,YY=np.meshgrid(XS[ix0:ix1],YS[iy0:iy1])
            inn=inner_obj(k,g,XX,YY)>=w/2+0.005
            fr[li,iy0:iy1,ix0:ix1]|=inn
        return fr
    def via_mask(self,nid,dother=None,vr=VR):
        if dother is None: dother=self.dist_other(nid)
        return (dother[0]>=vr+CLRA)&(dother[1]>=vr+CLRA)&(self.edge>=vr+0.15)&(self.dsmd>=vr+VIA_ANNULAR_SMD)&(self.dv>=vr+CLR+0.01)&(~self.via_keepout)
    # ---------- exact check
    def seg_clear(self,a,b,w,layer,nid):
        if min(a[0],b[0])-w/2<KEEPIN[0] or max(a[0],b[0])+w/2>KEEPIN[2] or min(a[1],b[1])-w/2<KEEPIN[1] or max(a[1],b[1])+w/2>KEEPIN[3]: return False
        if abs(a[0]-b[0])+abs(a[1]-b[1])<1e-9: gq=Point(a).buffer(w/2+CLR-1e-4,16)
        else: gq=LineString([a,b]).buffer(w/2+CLR-1e-4,16)
        idx=self.tree[layer].query(gq,predicate='intersects')
        for i in idx:
            if self.tnet[layer][i]!=nid: return False
        for g,n in self.extra[layer]:
            if n!=nid and gq.intersects(g): return False
        return True
    def via_clear(self,x,y,nid,vr=VR):
        gq=Point(x,y).buffer(vr+CLR-1e-4,16)
        for layer in (0,1):
            for i in self.tree[layer].query(gq,predicate='intersects'):
                if self.tnet[layer][i]!=nid: return False
            for g,n in self.extra[layer]:
                if n!=nid and gq.intersects(g): return False
        return True
    soft_mode=False
    tag=None
    def commit_seg(self,a,b,w,layer,nid,record=True):
        g=(a[0],a[1],b[0],b[1],w/2)
        self.add(layer,nid,'cap',g,shape=False)
        sh=shp_obj('cap',g); self.extra[layer].append((sh,nid)); self.geoms[layer].append((sh,nid))
        if record: self.segs.append(dict(net=self.names.get(nid),nid=nid,layer=layer,w=w,p0=a,p1=b,soft=self.soft_mode,tag=self.tag))
    def snapshot_hard(self):
        self.hard=(self.d1.copy(),self.d2.copy(),self.n1.copy(),self.dv.copy(),[list(self.geoms[0]),list(self.geoms[1])])
        self.soft_mode=True
    def rip(self,nids,tags=()):
        nids=set(nids); tags=set(tags)
        def gone(o): return o['soft'] and ((o['nid'] in nids and o.get('tag') is None) or (o.get('tag') in tags))
        self.segs=[s for s in self.segs if not gone(s)]
        self.vias=[v for v in self.vias if not gone(v)]
        d1,d2,n1,dv,gg=self.hard
        self.d1=d1.copy(); self.d2=d2.copy(); self.n1=n1.copy(); self.dv=dv.copy(); self.geoms=[list(gg[0]),list(gg[1])]
        for s in self.segs:
            if s['soft']:
                g=(s['p0'][0],s['p0'][1],s['p1'][0],s['p1'][1],s['w']/2)
                self.add(s['layer'],s['nid'],'cap',g)
        for v in self.vias:
            if v['soft']:
                for li in (0,1): self.add(li,v['nid'],'circ',(v['x'],v['y'],v['vr']))
                self.add_point_field(self.dv,v['x'],v['y'],v['vr'])
        self.rebuild_tree()
    def soft_fields(self):
        d1=np.full((2,H,W),CAP,np.float32); d2=np.full((2,H,W),CAP,np.float32)
        n1=np.zeros((2,H,W),np.int32); n2=np.zeros((2,H,W),np.int32)
        objs=[(s['layer'],s['nid'],'cap',(s['p0'][0],s['p0'][1],s['p1'][0],s['p1'][1],s['w']/2)) for s in self.segs if s['soft']]
        for v in self.vias:
            if v['soft']:
                for li in (0,1): objs.append((li,v['nid'],'circ',(v['x'],v['y'],v['vr'])))
        for layer,nid,kind,g in objs:
            bb=bbox_obj(kind,g); iy0,iy1,ix0,ix1=self._win(bb)
            XX,YY=np.meshgrid(XS[ix0:ix1],YS[iy0:iy1])
            d=dist_obj(kind,g,XX,YY).astype(np.float32)
            a1=d1[layer,iy0:iy1,ix0:ix1]; a2=d2[layer,iy0:iy1,ix0:ix1]; m1=n1[layer,iy0:iy1,ix0:ix1]; m2=n2[layer,iy0:iy1,ix0:ix1]
            same=(m1==nid); closer=(~same)&(d<a1)
            sec=(~same)&(~closer)&(d<a2)
            same2=same&False
            nm2=np.where(closer,m1,np.where(sec,nid,m2))
            nd2=np.where(closer,a1,np.where(sec,d,a2))
            nd1=np.where(same,np.minimum(a1,d),np.where(closer,d,a1))
            nm1=np.where(closer,nid,m1)
            d1[layer,iy0:iy1,ix0:ix1]=nd1; d2[layer,iy0:iy1,ix0:ix1]=nd2; n1[layer,iy0:iy1,ix0:ix1]=nm1; n2[layer,iy0:iy1,ix0:ix1]=nm2
        return d1,d2,n1,n2
    def commit_via(self,x,y,nid,vr=VR):
        for li in (0,1):
            self.add(li,nid,'circ',(x,y,vr),shape=False)
            sh=shp_obj('circ',(x,y,vr)); self.extra[li].append((sh,nid)); self.geoms[li].append((sh,nid))
        self.add_point_field(self.dv,x,y,vr)
        self.vias.append(dict(net=self.names.get(nid),nid=nid,x=x,y=y,vr=vr,soft=self.soft_mode,tag=self.tag))

DY=np.array([0,0,1,-1,1,1,-1,-1]); DX=np.array([1,-1,0,0,1,-1,1,-1]); DC=np.array([1,1,1,1,math.sqrt(2)]*1+[math.sqrt(2)]*3)
@njit(cache=True)
def astar(free,viaok,tgt,srcs,ty0,tx0,ty1,tx1,via_cost,hw,lay_pen,cost):
    L,Hh,Ww=free.shape
    INF=1e30
    g=np.full((L,Hh,Ww),INF)
    par=np.full((L,Hh,Ww),-1,np.int64)
    closed=np.zeros((L,Hh,Ww),np.bool_)
    heap=[(0.0,np.int64(0))]; heap.pop()
    dys=(0,0,1,-1,1,1,-1,-1); dxs=(1,-1,0,0,1,-1,1,-1)
    s2=math.sqrt(2.0)
    for k in range(srcs.shape[0]):
        l=srcs[k,0]; y=srcs[k,1]; x=srcs[k,2]
        if g[l,y,x]>0:
            g[l,y,x]=0.0
            heapq.heappush(heap,(0.0,np.int64((l*Hh+y)*Ww+x)))
    while len(heap)>0:
        f,idx=heapq.heappop(heap)
        l=idx//(Hh*Ww); rem=idx%(Hh*Ww); y=rem//Ww; x=rem%Ww
        if closed[l,y,x]: continue
        closed[l,y,x]=True
        if tgt[l,y,x]:
            return idx,par
        gc=g[l,y,x]
        for d in range(8):
            ny=y+dys[d]; nx=x+dxs[d]
            if ny<0 or nx<0 or ny>=Hh or nx>=Ww: continue
            if not free[l,ny,nx]: continue
            if d>=4:
                if not free[l,y,nx] or not free[l,ny,x]: continue
                c=s2
            else: c=1.0
            nc=gc+c*lay_pen[l]+cost[l,ny,nx]
            if nc<g[l,ny,nx]:
                g[l,ny,nx]=nc; par[l,ny,nx]=idx
                ddx=0
                if nx<tx0: ddx=tx0-nx
                elif nx>tx1: ddx=nx-tx1
                ddy=0
                if ny<ty0: ddy=ty0-ny
                elif ny>ty1: ddy=ny-ty1
                mn=min(ddx,ddy); mx=max(ddx,ddy)
                h=(mx-mn)+s2*mn
                heapq.heappush(heap,(nc+hw*h,np.int64((l*Hh+ny)*Ww+nx)))
        if viaok[y,x]:
            ol=1-l
            if free[ol,y,x]:
                nc=gc+via_cost+cost[ol,y,x]
                if nc<g[ol,y,x]:
                    g[ol,y,x]=nc; par[ol,y,x]=idx
                    heapq.heappush(heap,(nc,np.int64((ol*Hh+y)*Ww+x)))
    return np.int64(-1),par
