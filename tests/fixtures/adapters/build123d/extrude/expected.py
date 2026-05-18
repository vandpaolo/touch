# build123d source for Intent: extrude_basic
from build123d import *

slab = extrude(sketch_a, 5.0)

export_step(slab, "part.step")
