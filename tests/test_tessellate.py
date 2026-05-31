"""T1b day-3 tests: OCP tessellation emits per-face IDs (F20) and the mesh
round-trips through the binary frame helper.
"""

from __future__ import annotations

import numpy as np

from touch_backend.frames import mesh_frame_envelope, pack, unpack
from touch_backend.tessellate import tessellate


def _cube():
    # build123d is imported lazily, not at module top-level: importing it at
    # pytest *collection* time loads the OCP GL layer, which poisons VTK-OSMesa
    # for the in-process orthographic render test (auto-memory `render-backend`).
    from build123d import Box

    return Box(10, 10, 10)


def test_cube_has_six_distinct_face_ids():
    mesh = tessellate(_cube())
    # one tag per triangle (the F20 invariant)
    assert mesh.face_tag_per_triangle.shape[0] == mesh.indices.shape[0]
    # a cube: 6 faces, 2 triangles each
    assert mesh.indices.shape[0] == 12
    assert {int(t) for t in mesh.face_tag_per_triangle} == set(range(6))
    assert mesh.face_ids == list(range(6))


def test_cube_normals_are_unit_length():
    mesh = tessellate(_cube())
    lengths = np.linalg.norm(mesh.normals, axis=1)
    assert np.allclose(lengths, 1.0, atol=1e-5)


def test_mesh_frame_envelope_counts_and_hints():
    mesh = tessellate(_cube())
    env = mesh_frame_envelope(mesh)
    assert env.type == "meshFrame"
    assert env.vertex_count == mesh.vertices.shape[0]
    assert env.triangle_count == 12
    assert env.edge_segment_count == 0
    assert set(env.face_id_to_finder_hint.keys()) == {str(i) for i in range(6)}
    # each hint anchors a contains_point finder on the face
    hint0 = env.face_id_to_finder_hint["0"]
    assert hint0.target.value == "face"
    assert len(hint0.finder) == 1


def test_binary_frame_roundtrip():
    mesh = tessellate(_cube())
    env = mesh_frame_envelope(mesh)
    recovered = unpack(
        pack(mesh),
        version=env.version,
        vertex_count=env.vertex_count,
        triangle_count=env.triangle_count,
        edge_segment_count=env.edge_segment_count,
    )
    assert recovered.version == mesh.version
    assert np.array_equal(recovered.vertices, mesh.vertices)
    assert np.array_equal(recovered.normals, mesh.normals)
    assert np.array_equal(recovered.indices, mesh.indices)
    assert np.array_equal(recovered.face_tag_per_triangle, mesh.face_tag_per_triangle)
