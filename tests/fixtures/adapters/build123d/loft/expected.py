# build123d source for Intent: loft_basic
from build123d import *

shell = loft([sketch_a, sketch_b])

export_step(shell, "part.step")
