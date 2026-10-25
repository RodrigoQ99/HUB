import re, collections
D='/mnt/user-data/uploads/projects--hub/'
def load(n='37'):
    syms={}; pins=[]; cur=None
    for l in open(D+f'claude_all{n}.txt'):
        if l.startswith('SYM'):
            m=re.match(r'SYM (\S+) "([^"]+)" \(([-\d.]+) ([-\d.]+)\) ([-\d.]+) (.*)$',l)
            ref,fp,x,y,rot,rest=m.groups()
            bbs=[tuple(map(float,b)) for b in re.findall(r'\(\(([-\d.]+) ([-\d.]+)\) \(([-\d.]+) ([-\d.]+)\)\)',rest)]
            syms[ref]=dict(fp=fp,x=float(x),y=float(y),rot=float(rot),bbs=bbs,mir=False)
        elif l.startswith('MIR'):
            _,r,v=l.split(); syms[r]['mir']=(v=='t')
        elif l.startswith('P '):
            m=re.match(r'P (\S+) "([^"]*)" \(([-\d.]+) ([-\d.]+)\) "?([^"]*)"?',l)
            r,num,x,y,net=m.groups(); pins.append(dict(ref=r,num=num,x=float(x),y=float(y),net=net))
    pb={}
    for l in open(D+f'claude_pinbb{n}.txt'):
        m=re.match(r'PB (\S+) "([^"]*)" \(([-\d.]+) ([-\d.]+)\) \(\(([-\d.]+) ([-\d.]+)\) \(([-\d.]+) ([-\d.]+)\)\) "?([^"]*)"?',l)
        if m:
            r,num,x,y,x0,y0,x1,y1,pad=m.groups(); pb[(r,num)]=dict(bb=(float(x0),float(y0),float(x1),float(y1)),pad=pad)
    for p in pins:
        p.update(pb.get((p['ref'],p['num']),{}))
        p['mir']=syms[p['ref']]['mir']
    segs=[]
    for l in open(D+f'claude_etch{n}.txt'):
        m=re.match(r'SEG (\S+) (\S+) ([-\d.]+) \(\(([-\d.]+) ([-\d.]+)\) \(([-\d.]+) ([-\d.]+)\)\)',l)
        if m:
            net,lay,w,x0,y0,x1,y1=m.groups(); segs.append(dict(net=net,layer=lay,w=float(w),p0=(float(x0),float(y0)),p1=(float(x1),float(y1))))
    return syms,pins,segs
