# build123d source for Intent: chamfer_basic
from build123d import *

body = Box(30.0, 30.0, 30.0)

body = chamfer(body.edges(), 1.5)

export_step(body, "part.step")
