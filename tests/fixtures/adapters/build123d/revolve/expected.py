# build123d source for Intent: revolve_basic
from build123d import *

solid = revolve(sketch_a, Axis.Z, angle=360.0)

export_step(solid, "part.step")
