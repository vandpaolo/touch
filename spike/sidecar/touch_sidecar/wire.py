"""Binary mesh frame encode/decode for the T0 spike.

Matches docs/02-data-model.md §Mesh for the fields the spike exercises.

The spec lists the logical fields + dtypes but no explicit byte layout
(endianness / header / padding are left to the implementation — see roadmap
"Open decisions #2": custom binary mesh frame is the default). This module
fixes a concrete little-endian framing; T1b promotes it to the real
`protocol/schema.json` codegen, so keep this faithful to the spec field
order and dtypes.

Spec fields and how the spike handles each:
    version: u8                     -> emitted (== 1)
    vertices: float32[N x 3]        -> emitted
    normals:  float32[N x 3]        -> emitted
    indices:  u32[M x 3]            -> emitted
    face_tag_per_triangle: u32[M]   -> emitted (the picking id, F20)
    edge_tag_per_segment:  u32[L]   -> DEFERRED (T1b): the spike renders no
                                       edge wireframe, and the spec does not
                                       define the edge-segment vertex buffer
                                       layout. A zero edge count is encoded so
                                       the frame is already shaped for it.
    face_id_to_finder_hint: JSON    -> DEFERRED (T1b): a separate JSON
                                       envelope, not part of the binary frame;
                                       not needed until click->selection lands.

Concrete layout (little-endian, no implicit padding beyond what is noted):

    offset  type        count          field
    ------  ----------  -------------  ----------------------------
    0       uint8       1              version = 1
    1       uint8       3              reserved = 0 (align counts to 4)
    4       uint32      1              vertex_count   (N)
    8       uint32      1              triangle_count (M)
    12      uint32      1              edge_segment_count (L; 0 in the spike)
    16      float32     N*3            vertices   (x, y, z per vertex)
    ...     float32     N*3            normals    (x, y, z per vertex)
    ...     uint32      M*3            indices    (i0, i1, i2 per triangle)
    ...     uint32      M              face_tag_per_triangle
    ...     uint32      L              edge_tag_per_segment  (empty in spike)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

VERSION = 1


@dataclass(frozen=True)
class Mesh:
    vertices: list[tuple[float, float, float]]
    normals: list[tuple[float, float, float]]
    triangles: list[tuple[int, int, int]]
    face_tag_per_triangle: list[int]
    edge_tag_per_segment: list[int] = field(default_factory=list)


def encode(mesh: Mesh) -> bytes:
    n = len(mesh.vertices)
    m = len(mesh.triangles)
    ell = len(mesh.edge_tag_per_segment)
    if len(mesh.normals) != n:
        raise ValueError(f"normals ({len(mesh.normals)}) must match vertices ({n})")
    if len(mesh.face_tag_per_triangle) != m:
        raise ValueError(
            f"face_tag_per_triangle ({len(mesh.face_tag_per_triangle)}) "
            f"must match triangles ({m})"
        )

    parts: list[bytes] = [struct.pack("<B3xIII", VERSION, n, m, ell)]
    for x, y, z in mesh.vertices:
        parts.append(struct.pack("<3f", x, y, z))
    for x, y, z in mesh.normals:
        parts.append(struct.pack("<3f", x, y, z))
    for i0, i1, i2 in mesh.triangles:
        parts.append(struct.pack("<3I", i0, i1, i2))
    for tag in mesh.face_tag_per_triangle:
        parts.append(struct.pack("<I", tag))
    for tag in mesh.edge_tag_per_segment:
        parts.append(struct.pack("<I", tag))
    return b"".join(parts)


def decode(data: bytes) -> Mesh:
    version, n, m, ell = struct.unpack_from("<B3xIII", data, 0)
    if version != VERSION:
        raise ValueError(f"unsupported mesh-frame version: {version}")

    off = 16
    vertices: list[tuple[float, float, float]] = []
    for _ in range(n):
        vertices.append(struct.unpack_from("<3f", data, off))
        off += 12
    normals: list[tuple[float, float, float]] = []
    for _ in range(n):
        normals.append(struct.unpack_from("<3f", data, off))
        off += 12
    triangles: list[tuple[int, int, int]] = []
    for _ in range(m):
        triangles.append(struct.unpack_from("<3I", data, off))
        off += 12
    face_tags: list[int] = []
    for _ in range(m):
        (tag,) = struct.unpack_from("<I", data, off)
        face_tags.append(tag)
        off += 4
    edge_tags: list[int] = []
    for _ in range(ell):
        (tag,) = struct.unpack_from("<I", data, off)
        edge_tags.append(tag)
        off += 4

    return Mesh(
        vertices=vertices,
        normals=normals,
        triangles=triangles,
        face_tag_per_triangle=face_tags,
        edge_tag_per_segment=edge_tags,
    )
