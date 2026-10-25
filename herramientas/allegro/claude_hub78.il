; center D8 polarity letters between R74 and D8 pads (Claude)
let((s n) n = 0
  s = car(setof(x axlDBGetDesign()->symbols x->refdes == "D8"))
  foreach(c s->children
    when(c->objType == "text" && member(c->text list("A" "K")) && c->layer == "PACKAGE GEOMETRY/SILKSCREEN_TOP"
      axlTransformObject(c ?move list(0.26 0.0)) n = n + 1))
  printf("c78 moved %d\n" n))
