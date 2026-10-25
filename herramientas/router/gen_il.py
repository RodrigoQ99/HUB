import pickle, sys
src=sys.argv[1]; out=sys.argv[2]; tagname=sys.argv[3]
segs,vias,viol,af=pickle.load(open(src,'rb'))
L=[]
L.append('; auto-routed etch from Claude grid router (%s)'%tagname)
L.append('CQDIR = "C:/Users/Maria Priscila Quiro/OneDrive/Documentos/Escritorio/Orcad/cdssetup/workspace/projects/hub/"')
L.append('''procedure(cqP(lay net w x0 y0 x1 y1)
  let((p r) p = axlPathStart(list(x0:y0) w) axlPathLine(p w x1:y1)
    r = car(errset(axlDBCreatePath(p lay net nil) t))
    if(r then cqNP = cqNP + 1 else cqEP = cons(list(net x0 y0 x1 y1) cqEP))))
procedure(cqV(ps x y net)
  let((r) r = car(errset(axlDBCreateVia(ps x:y net) t))
    if(r then cqNV = cqNV + 1 else cqEV = cons(list(net x y) cqEV))))
cqNP = 0 cqNV = 0 cqEP = nil cqEV = nil''')
L.append('procedure(cqRoute_%s()'%tagname)
L.append('  axlDBRefreshId(nil)')
for v in vias:
    ps='"via"' if v.get('vr',0.3048)>0.3 else '"VIA02B"'
    L.append(f'  cqV({ps} {v["x"]:.4f} {v["y"]:.4f} "{v["net"]}")')
for s in segs:
    lay='"ETCH/TOP"' if s['layer']==0 else '"ETCH/BOTTOM"'
    L.append(f'  cqP({lay} "{s["net"]}" {s["w"]:.4f} {s["p0"][0]:.4f} {s["p0"][1]:.4f} {s["p1"][0]:.4f} {s["p1"][1]:.4f})')
L.append('''  let((p) p = outfile(strcat(CQDIR "claude_rt_%s.txt"))
    fprintf(p "NP %%d NV %%d\\nEP %%L\\nEV %%L\\n" cqNP cqNV cqEP cqEV) close(p))
  printf("route %s: paths %%d vias %%d errP %%d errV %%d\\n" cqNP cqNV length(cqEP) length(cqEV))
  t)
cqRoute_%s()'''%(tagname,tagname,tagname))
open(out,'w').write('\n'.join(L)+'\n')
print(len(segs),'segs',len(vias),'vias ->',out)
