; dump drill-hole polygons of all pins (slots) (Claude)
CQDIR = "C:/Users/Maria Priscila Quiro/OneDrive/Documentos/Escritorio/Orcad/cdssetup/workspace/projects/hub/"
procedure(cqPs74()
  let((p d polys n psn)
    d = axlDBGetDesign()
    p = outfile(strcat(CQDIR "claude_c74.txt"))
    fprintf(p "START\n")
    n = 0
    foreach(s d->symbols
      foreach(pn s->pins
        polys = car(errset(axlPolyFromDrillHole(pn) nil))
        when(polys
          psn = car(errset(pn->padstack->name nil))
          foreach(pl polys
            fprintf(p "H %s|%s|%L|%L|%L|%d\n" s->refdes pn->number psn pn->xy pl->bBox length(car(errset(pl->vertices nil))))
            n = n + 1))))
    fprintf(p "N %d\n" n)
    close(p) printf("ps74 done %d\n" n) t))
cqPs74()
