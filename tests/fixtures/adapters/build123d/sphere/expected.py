# build123d source for Intent: sphere_basic
from build123d import *

ball = Sphere(10.0)

export_step(ball, "part.step")
