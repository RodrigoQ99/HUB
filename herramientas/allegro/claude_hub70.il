; dump silkscreen / assembly text + geometry for silk cleanup (Claude)
CQDIR = "C:/Users/Maria Priscila Quiro/OneDrive/Documentos/Escritorio/Orcad/cdssetup/workspace/projects/hub/"
procedure(cqTxt70(p tag x)
  fprintf(p "T %s|%s|%s|%L|%L|%L|%L|%L|%L\n" tag x->layer x->text x->xy x->rotation x->isMirrored x->justify x->textBlock x->bBox))
procedure(cqGeo70(p tag x)
  let((segs)
    if(x->objType == "path" || x->objType == "line" || x->objType == "arc" then
      segs = if(x->objType == "path" x->segments list(x))
      foreach(s segs
        if(s->objType == "arc" then
          fprintf(p "A %s|%s|%L|%L|%L|%L|%L\n" tag x->layer s->startEnd s->xy s->radius s->width s->bBox)
        else
          fprintf(p "L %s|%s|%L|%L\n" tag x->layer s->startEnd s->width)))
    else
      fprintf(p "G %s|%s|%s|%L\n" tag x->layer x->objType x->bBox))))
procedure(cqDump70()
  let((p d i nb)
    d = axlDBGetDesign()
    p = outfile(strcat(CQDIR "claude_c70.txt"))
    fprintf(p "EXT %L\n" axlExtentDB())
    for(i 1 16
      nb = car(errset(axlGetParam(sprintf(nil "paramTextBlock:%d" i)) nil))
      when(nb fprintf(p "TB %d %L %L %L %L %L\n" i nb->width nb->height nb->photoWidth nb->charSpace nb->lineSpace)))
    foreach(s d->symbols
      fprintf(p "S %L|%L|%L|%L|%L|%L\n" s->refdes s->name s->xy s->rotation s->isMirrored s->bBox)
      foreach(pn s->pins
        fprintf(p "P %L|%L|%L|%L\n" s->refdes pn->number pn->bBox car(errset(pn->padstack->name nil))))
      foreach(c s->children
        cond(
          (c->objType == "text" cqTxt70(p s->refdes c))
          (t when(c->layer && (rexMatchp("SILK" c->layer) || rexMatchp("ASSEMBLY" c->layer) || rexMatchp("PLACE_BOUND" c->layer))
               cqGeo70(p s->refdes c))))))
    foreach(x car(errset(d->text nil)) cqTxt70(p "-" x))
    foreach(v car(errset(d->vias nil)) fprintf(p "V %L|%L\n" v->xy v->name))
    close(p) printf("dump70 ok\n") t))
cqDump70()
