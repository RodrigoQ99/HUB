import cairosvg, sys
from gerbonara import GerberFile
from gerbonara.utils import MM
src='/mnt/user-data/uploads/projects--hub/'
for n in sys.argv[1:]:
    g=GerberFile.open(src+n+'.art')
    open(n+'.svg','w').write(str(g.to_svg(fg='black',bg='white')))
    cairosvg.svg2png(url=n+'.svg',write_to=n+'.png',output_width=1600)
    print(n,[[round(v,2) for v in p] for p in g.bounding_box()], len(g.objects))
