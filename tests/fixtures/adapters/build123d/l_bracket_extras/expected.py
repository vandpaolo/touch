# build123d source for Intent: l_bracket_extras
from build123d import *


# --- user extras ---
from build123d import BuildPart, BuildSketch, BuildLine, Plane, Polyline, make_face, extrude, Locations, Hole
with BuildPart() as bp:
    with BuildSketch(Plane.XZ) as sk:
        with BuildLine() as ln:
            Polyline((0, 0), (100, 0), (100, 5), (5, 5), (5, 60), (0, 60), close=True)
        make_face()
    extrude(amount=60)
    with Locations((30, 30, 5), (70, 30, 5)):
        Hole(radius=3, depth=10)
body = bp.part
export_step(body, "part.step")
