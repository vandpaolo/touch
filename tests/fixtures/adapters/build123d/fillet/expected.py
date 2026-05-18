# build123d source for Intent: fillet_basic
from build123d import *

body = Box(30.0, 30.0, 30.0)

body = fillet(body.edges(), 2.0)

# STEP export will land Day 4
