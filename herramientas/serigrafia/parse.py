import re, ast
SRC='/mnt/user-data/uploads/projects--hub/claude_c70.txt'
def sk(s):
    s=s.strip()
    if s=='nil': return None
    if s=='t': return True
    s2=re.sub(r'\(',' [',s); s2=s2.replace(')',']')
    s2=re.sub(r'(?<=[0-9])\s+(?=[-0-9\[])',',',s2)
    s2=re.sub(r'\]\s+\[','],[',s2)
    s2=re.sub(r'\]\s+(?=[-0-9])','],',s2)
    s2=re.sub(r'(?<=[0-9])\s+(?=\[)',',',s2)
    try: return ast.literal_eval(s2.strip())
    except Exception: return s
def load():
    syms={}; texts=[]; geo=[]
    for line in open(SRC):
        k,_,rest=line.rstrip('\n').partition(' ')
        f=rest.split('|')
        if k=='S':
            ref=sk(f[0]); syms[ref]=dict(ref=ref,name=sk(f[1]),xy=sk(f[2]),rot=sk(f[3]),mir=bool(sk(f[4])),bb=sk(f[5]),pins=[])
        elif k=='P':
            syms[sk(f[0])]['pins'].append(sk(f[2]))
        elif k=='T':
            texts.append(dict(ref=f[0],layer=f[1],text=f[2],xy=sk(f[3]),rot=sk(f[4]),mir=bool(sk(f[5])),just=sk(f[6]),tb=sk(f[7]),bb=sk(f[8])))
        elif k=='L':
            geo.append(dict(kind='L',ref=f[0],layer=f[1],se=sk(f[2]),w=sk(f[3])))
        elif k=='A':
            geo.append(dict(kind='A',ref=f[0],layer=f[1],se=sk(f[2]),c=sk(f[3]),r=sk(f[4]),w=sk(f[5]),bb=sk(f[6])))
        elif k=='G':
            geo.append(dict(kind='G',ref=f[0],layer=f[1],typ=f[2],bb=sk(f[3])))
    return syms,texts,geo
if __name__=='__main__':
    s,t,g=load()
    print(len(s),len(t),len(g))
    import itertools
    print(list(s.values())[0]); print(t[0]); print(g[0]); print([x for x in g if x['kind']=='A'][0]); print([x for x in g if x['kind']=='G'][:3])
