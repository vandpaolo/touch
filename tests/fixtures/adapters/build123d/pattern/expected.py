# build123d source for Intent: pattern_basic
from build123d import *

body = Box(10.0, 10.0, 10.0)

body = body * LinearLocations(15.0, 4, axis=Axis.X)

export_step(body, "part.step")
