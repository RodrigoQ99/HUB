; DRILL_DWG film with drill legends + save (Claude)
CQDIR = "C:/Users/Maria Priscila Quiro/OneDrive/Documentos/Escritorio/Orcad/cdssetup/workspace/projects/hub/"
let((p ok lays)
  p = outfile(strcat(CQDIR "claude_c76.txt"))
  lays = list("MANUFACTURING/NCLEGEND-1-4" "MANUFACTURING/NCLEGEND-SLOTS-1-4" "BOARD GEOMETRY/DESIGN_OUTLINE")
  fprintf(p "SUBS %L\n" axlSubclasses("MANUFACTURING"))
  ok = car(errset(axlFilmCreate("DRILL_DWG" ?undefineLineWidth 0.1 ?sequence 14 ?layers lays) t))
  fprintf(p "FILM DRILL_DWG %L\n" ok)
  close(p) printf("c76 %L\n" ok))
