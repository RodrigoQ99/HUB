; enlarge drawing extents so the drill chart fits outside the board (Claude)
CQDIR = "C:/Users/Maria Priscila Quiro/OneDrive/Documentos/Escritorio/Orcad/cdssetup/workspace/projects/hub/"
let((p r)
  p = outfile(strcat(CQDIR "claude_c75.txt"))
  fprintf(p "BEFORE %L\n" axlExtentDB())
  fprintf(p "CALLABLE %L\n" isCallable('axlDBChangeDesignExtents))
  r = car(errset(axlDBChangeDesignExtents(list(-50.0:-50.0 350.0:250.0)) t))
  fprintf(p "CHANGE %L\nAFTER %L\n" r axlExtentDB())
  close(p) printf("c75 %L\n" r))
