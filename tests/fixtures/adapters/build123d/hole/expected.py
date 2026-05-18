# build123d source for Intent: cube_with_hole
from build123d import *

# parameters (units assumed mm in v0)
size = 50.0
hole_diam = 20.0

body = Box(50.0, 50.0, 50.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))

body = body - Cylinder(10.0, 1000.0)

# STEP export will land Day 4
