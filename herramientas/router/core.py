import time, math, collections
from drive import *
WID={}
for n in ('12V_RAW','12V_IN'): WID[n]=(1.0,0.6,0.4,0.25)
for n in ('PWR1','PWR2','PWR3','PWR4'): WID[n]=(0.6,0.5,0.4,0.3,0.2)
for n in ('VDD12','1V2_REG','N327857','5V_REG_1V2','5V_REG_3V3'): WID[n]=(0.5,0.4,0.3,0.2)
for n in ('3V3','VDD33','UP_VBUS','GND_EARTH'): WID[n]=(0.4,0.3,0.2)
DEF=(0.2,0.15,0.127)
def mstlen(ps):
    pts=[(p['x'],p['y']) for p in ps]; inn=[0]; out=list(range(1,len(pts))); L=0
    while out:
        d,j=min((math.hypot(pts[i][0]-pts[j][0],pts[i][1]-pts[j][1]),j) for i in inn for j in out)
        L+=d; inn.append(j); out.remove(j)
    return L
def escape_pin(R,p):
    B=R.B
    if abs(p['y']-83.4)<1e-6: d=(0,1)
    elif abs(p['y']-76.6)<1e-6: d=(0,-1)
    elif abs(p['x']-84.6)<1e-6: d=(-1,0)
    else: d=(1,0)
    nid=p['nid']; key=(p['ref'],p['num'])
    before=set(R.tree_cells[nid])
    done=False
    B.tag=key
    for w in (0.25,0.2,0.15):
        for L in [0.9+0.05*i for i in range(30)]:
            vx,vy=round(p['x']+d[0]*L,4),round(p['y']+d[1]*L,4)
            if B.seg_clear((p['x'],p['y']),(vx,vy),w,0,nid) and B.via_clear(vx,vy,nid):
                B.commit_seg((p['x'],p['y']),(vx,vy),w,0,nid); B.commit_via(vx,vy,nid)
                tc=R.tree_cells[nid]; iy,ix=c2i(vx,vy); tc.add((0,iy,ix)); tc.add((1,iy,ix))
                done=True; break
        if done: break
    B.tag=None
    if not done:
        w=R.fanout(p,(0.2,0.15,0.127),margin=4.0)
        if w is None: w=R.fanout(p,(0.2,0.15,0.127),margin=4.0,vr=VR2)
        done = w is not None
    R.esc[key]=set(R.tree_cells[nid])-before
    return done
PRE=['N210668','N208498','TESTEN','RBIAS','VBUS_DET','N18966','N18954','N18947','N18933']
def setup(ep_pts=None, verbose=True):
    R=Router(); B=R.B
    GND=B.nid['GND']
    def ep_vias(ref,pts):
        for x,y in pts:
            gq=Point(x,y).buffer(VR+CLR,16)
            ok=all(B.tnet[1][i]==GND for i in B.tree[1].query(gq,predicate='intersects'))
            if ok: B.commit_via(x,y,GND)
            else: print('EP via blocked',ref,x,y)
    ep_vias('U1',[(88+dx,80+dy) for dx in (-1.15,0,1.15) for dy in (-1.15,0,1.15)])
    for p in B.pins:
        if p['ps']=='EP150X090': ep_vias(p['ref'],[(p['x']-0.4,p['y']),(p['x']+0.4,p['y'])])
    B.rebuild_tree()
    B.snapshot_hard()
    R.pre_fail={}
    import manual
    before=set(R.tree_cells[B.nid['VDD33']])
    mb=manual.apply_manual(R)
    if mb: print('MANUAL BAD',mb)
    R.esc[('U1','55')]=set(R.tree_cells[B.nid['VDD33']])-before
    R.tree_cells[B.nid['VDD33']]=set()
    for n in PRE:
        f=R.route_net(n,WID.get(n,DEF))
        if f: R.pre_fail[n]=f
    if verbose: print('pre-route fails',R.pre_fail)
    esc_fail=[]
    for p in B.pins:
        if p['ref']!='U1' or p['net'] not in ('VDD12','VDD33'): continue
        if p['num']=='55': continue
        if p['net']=='VDD12' and p['num'] not in ('43','28'): continue
        if not escape_pin(R,p): esc_fail.append(p['num'])
    if verbose: print('U1 escape fails',esc_fail)
    B.rebuild_tree()
    R.fo_widths={'GND':(0.4,0.3,0.2),'5V':(0.5,0.4,0.3,0.2)}
    fo_fail=[]
    for net,ws in (('GND',(0.4,0.3,0.2)),('5V',(0.5,0.4,0.3,0.2))):
        nid=B.nid[net]
        for p in B.pins:
            if p['nid']!=nid or p['drill']>0 or p['ps'] in ('PAD_TERMICO','EP150X090'): continue
            if R.fanout(p,ws) is None: fo_fail.append(p['ref']+'.'+p['num'])
        B.rebuild_tree()
    if verbose: print('fanout fails',fo_fail)
    keep={B.nid[n]:R.tree_cells[B.nid[n]] for n in PRE}
    R.tree_cells.clear(); R.tree_cells.update(keep)
    return R
def nets_of(B):
    nets=collections.defaultdict(list)
    for p in B.pins:
        if p['net']: nets[p['net']].append(p)
    return nets
def default_order(B):
    nets=nets_of(B)
    todo=[n for n in nets if n not in ('GND','5V') and n not in B.hsnets and len(nets[n])>1 and n not in PRE]
    u1=[n for n in todo if any(p['ref']=='U1' for p in nets[n]) and n not in ('VDD12','VDD33')]
    pw=sorted(u1,key=lambda n:mstlen(nets[n]))+['VDD12','VDD33']+['12V_RAW','12V_IN','N327857','1V2_REG','5V_REG_1V2','5V_REG_3V3','3V3','PWR1','PWR2','PWR3','PWR4','UP_VBUS','GND_EARTH']
    sg=[n for n in todo if n not in WID and n not in u1]
    return [n for n in pw if n in todo]+sorted(sg,key=lambda n:mstlen(nets[n]))
def route_all(R,order,verbose=False):
    allfail={}
    for n in order:
        f=R.route_net(n,WID.get(n,DEF))
        if f: allfail[n]=f
        if verbose: print(n,f,flush=True)
    return allfail

import copy
def hard_dother(B,nid):
    hd1,hd2,hn1=B.hard[0],B.hard[1],B.hard[2]
    return np.where(hn1==nid,hd2,hd1)
def find_blockers(R,net,failed_pins):
    B=R.B; nid=B.nid[net]; w=WID.get(net,DEF)[-1]
    sd1,sd2,sn1,sn2=B.soft_fields()
    so=np.where(sn1==nid,sd2,sd1); sid=np.where(sn1==nid,sn2,sn1)
    hd=hard_dother(B,nid)
    pins=[p for p in B.pins if p['nid']==nid]
    bl=set(); tags=set()
    for fp in failed_pins:
        p=[q for q in pins if q['ref']+'.'+q['num']==fp][0]
        src=list(R.tree_cells[nid])
        if not src: src=R.pin_cells([q for q in pins if q is not p][0])
        path,st=R.run_astar(nid,w,src,R.pin_cells(p),margin=12,penal=(hd,so),via_cost=R.via_cost)
        if path is None:
            print('   hard-blocked',net,fp,st); continue
        viacells=set()
        for i in range(len(path)-1):
            if path[i][0]!=path[i+1][0]:
                _,y,x=path[i]; viacells.add((0,y,x)); viacells.add((1,y,x))
        for l,y,x in list(path)+sorted(viacells):
            lim=(VR+CLRA) if (l,y,x) in viacells else (w/2+CLRA)
            if so[l,y,x]<lim and sid[l,y,x]>0:
                k=int(sid[l,y,x]); px,py=i2c(y,x)
                found=False
                for o in B.segs:
                    if o['soft'] and o['nid']==k and o['layer']==l:
                        g=(o['p0'][0],o['p0'][1],o['p1'][0],o['p1'][1],o['w']/2)
                        if float(dist_obj('cap',g,np.array(px),np.array(py)))<lim:
                            found=True
                            if o.get('tag'): tags.add(o['tag'])
                            else: bl.add(k)
                for o in B.vias:
                    if o['soft'] and o['nid']==k and math.hypot(o['x']-px,o['y']-py)-o['vr']<lim:
                        found=True
                        if o.get('tag'): tags.add(o['tag'])
                        else: bl.add(k)
                if not found: bl.add(k)
    bl.discard(nid)
    return bl,tags
def count(af): return sum(len(v) for v in af.values())
def repair(R,af,rounds=4,verbose=True):
    B=R.B
    best=(count(af),copy.deepcopy(B.segs),copy.deepcopy(B.vias),copy.deepcopy(dict(R.tree_cells)),dict(af),copy.deepcopy(R.esc))
    for rd in range(rounds):
        if not af: break
        for net in list(af.keys()):
            if net not in af or net.startswith('FANOUT_') or net=='ESC': continue
            bl,tags=find_blockers(R,net,af[net])
            names=[B.names[i] for i in bl if i in B.names]
            names=[n for n in names if n not in ('GND','5V') and n not in PRE]
            tags={t for t in tags if t!=('U1','55')}
            esc_t=[t for t in tags if t[0]=='U1']
            fo_t=[t for t in tags if t[0]!='U1']
            for t in esc_t:
                pn=[q for q in B.pins if (q['ref'],q['num'])==t][0]['net']
                if pn not in names and pn!=net: names.append(pn)
            rip=[net]+names
            B.rip([B.nid[n] for n in rip],tags)
            for n in rip: R.tree_cells[B.nid[n]]=set()
            for t in esc_t: R.esc.pop(t,None)
            for n in rip: af.pop(n,None)
            f=R.route_net(net,WID.get(net,DEF))
            if f: af[net]=f
            for tg in fo_t:
                p=[q for q in B.pins if (q['ref'],q['num'])==tg][0]
                if R.fanout(p,R.fo_widths[p['net']]) is None and R.fanout(p,R.fo_widths[p['net']],margin=6.0) is None:
                    af.setdefault('FANOUT_'+p['net'],[]).append(p['ref']+'.'+p['num'])
            for tg in esc_t:
                p=[q for q in B.pins if (q['ref'],q['num'])==tg][0]
                if not escape_pin(R,p): af.setdefault('ESC',[]).append(p['ref']+'.'+p['num'])
                R.tree_cells[p['nid']]=set()
            B.rebuild_tree()
            for n in rip[1:]:
                f=R.route_net(n,WID.get(n,DEF))
                if f: af[n]=f
            if verbose: print(' repair',net,'ripped',names,'fo',sorted(tags),'->',count(af),dict(af),flush=True)
        if count(af)<best[0]:
            best=(count(af),copy.deepcopy(B.segs),copy.deepcopy(B.vias),copy.deepcopy(dict(R.tree_cells)),dict(af),copy.deepcopy(R.esc))
    # restore best
    n,segs,vias,tc,baf,esc=best
    B.segs=segs; B.vias=vias; B.rip([]); R.esc=esc
    R.tree_cells.clear(); R.tree_cells.update(tc)
    return baf
