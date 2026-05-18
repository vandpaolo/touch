# build123d source for Intent: shell_basic
from build123d import *

body = Box(30.0, 30.0, 30.0)

body = offset(body, amount=-1.0, openings=body.faces().sort_by(Axis.Z)[-1])

export_step(body, "part.step")
