# build123d source for Intent: cylinder_basic
from build123d import *

cyl = Cylinder(15.0, 40.0)

export_step(cyl, "part.step")
