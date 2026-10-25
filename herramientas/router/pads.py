import re
D='/mnt/user-data/uploads/projects--hub/'
num=r'([-\d.]+)'
def parse_pad(s):
    if s.strip()=='nil': return None
    m=re.match(r'\("(\w+)" \(\('+num+' '+num+r'\) \('+num+' '+num+r'\)\)\)',s.strip())
    if not m: return ('?',s)
    f=m.group(1); bb=tuple(map(float,m.groups()[1:]))
    if f=='NULL': return None
    return (f,bb)
def load():
    pins=[]; mp=[]
    for l in open(D+'claude_pads48.txt'):
        if l.startswith('PIN '):
            m=re.match(r'PIN (\S+) "([^"]*)" \('+num+' '+num+r'\) (\S+) (\S+) (\S+) (\S+) (\S+) \(\('+num+' '+num+r'\) \('+num+' '+num+r'\)\) (\(".*?\)\)\)|nil) (\(".*?\)\)\)|nil)\s*$',l)
            if not m: print('BAD',l); continue
            g=m.groups()
            net=g[4].strip('"'); net=None if net in ('nil','') else net
            d=dict(ref=g[0],num=g[1],x=float(g[2]),y=float(g[3]),net=net,ps=g[5].strip('"'),drill=float(g[6]) if g[6]!='nil' else 0.0,plat=g[7].strip('"'),rot=float(g[8]) if g[8]!='nil' else 0,
                   bb=tuple(map(float,g[9:13])),top=parse_pad(g[13]),bot=parse_pad(g[14]))
            pins.append(d)
        elif l.startswith('MPIN'):
            mp.append(l)
    return pins,mp
if __name__=='__main__':
    P,M=load()
    print(len(P),len(M))
    import collections
    seen={}
    for p in P:
        k=p['ps']
        if k not in seen: seen[k]=(p['ref'],p['top'],p['bot'],p['drill'],p['plat'],p['bb'])
    for k,v in seen.items(): print(k,v)
    for l in M[:10]: print(l.strip())
