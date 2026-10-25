; DRC + connectivity report (Claude)
CQDIR = "C:/Users/Maria Priscila Quiro/OneDrive/Documentos/Escritorio/Orcad/cdssetup/workspace/projects/hub/"
procedure(cqChk52()
  let((p d n)
    axlShell("drc update")
    d = axlDBGetDesign()
    p = outfile(strcat(CQDIR "claude_chk52.txt"))
    fprintf(p "NDRC %d\n" length(d->drcs))
    n = 0
    foreach(x d->drcs
      when(n < 3 fprintf(p "DRCATTR %L\n" x->??))
      fprintf(p "DRC %L %L %L\n" x->xy x->layer x->name)
      n = n + 1)
    foreach(net d->nets
      when(length(net->branches) > 1
        fprintf(p "OPEN %s %d\n" net->name length(net->branches))))
    close(p)
    printf("chk52 drc=%d\n" length(d->drcs))
    t))
cqChk52()
