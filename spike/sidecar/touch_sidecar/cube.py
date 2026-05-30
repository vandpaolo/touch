"""Hand-authored cube mesh for the T0 spike.

8 vertices, 12 triangles (2 per face), 6 distinct face tags — exactly the
shape called out in the Day-1 plan (docs/phases/phase-T0.md). The mesh is
deterministic so the Day-2 frontend wiring is exercised against a known
input (risk R5).

Cube is centred at the origin, edge length 2 (corners at +/-1 on each axis).
"""

from __future__ import annotations

import math

# 8 corners of the cube.
VERTICES: list[tuple[float, float, float]] = [
    (-1.0, -1.0, -1.0),  # 0
    (1.0, -1.0, -1.0),   # 1
    (1.0, 1.0, -1.0),    # 2
    (-1.0, 1.0, -1.0),   # 3
    (-1.0, -1.0, 1.0),   # 4
    (1.0, -1.0, 1.0),    # 5
    (1.0, 1.0, 1.0),     # 6
    (-1.0, 1.0, 1.0),    # 7
]

# Per-vertex normals. With 8 shared corners the only consistent per-vertex
# normal is the (normalised) corner direction — picking uses the face tag,
# not the normal, so smooth corner normals are fine for the spike. Day 2 can
# switch to a 24-vertex flat-shaded cube if faceting matters for the demo.
_INV_SQRT3 = 1.0 / math.sqrt(3.0)
NORMALS: list[tuple[float, float, float]] = [
    tuple(c * _INV_SQRT3 for c in v) for v in VERTICES  # type: ignore[misc]
]

# 12 triangles, grouped 2-per-face, wound CCW when viewed from outside.
# Each row is (i0, i1, i2). Face tags run 0..5 in the order:
#   0 = +X (right), 1 = -X (left), 2 = +Y (back),
#   3 = -Y (front), 4 = +Z (top),  5 = -Z (bottom)
TRIANGLES: list[tuple[int, int, int]] = [
    (1, 2, 6), (1, 6, 5),   # +X
    (0, 4, 7), (0, 7, 3),   # -X
    (3, 7, 6), (3, 6, 2),   # +Y
    (0, 1, 5), (0, 5, 4),   # -Y
    (4, 5, 6), (4, 6, 7),   # +Z
    (0, 3, 2), (0, 2, 1),   # -Z
]

# One tag per triangle (length == len(TRIANGLES)).
FACE_TAG_PER_TRIANGLE: list[int] = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
