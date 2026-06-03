"""T1b day-3 tests: OCP tessellation emits per-face IDs (F20) and the mesh
round-trips through the binary frame helper.
"""

from __future__ import annotations

import numpy as np

from touch_backend.finder import resolve_face
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


def _contains(face, point, tol=0.5) -> bool:
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from OCP.gp import gp_Pnt

    vertex = BRepBuilderAPI_MakeVertex(gp_Pnt(*point)).Vertex()
    return BRepExtrema_DistShapeShape(vertex, face.wrapped).Value() <= tol


def _face_centroids(mesh) -> dict[int, tuple[float, float, float]]:
    """One interior point per face id: the centroid of that face's triangle
    vertices (unlike `face_anchor`, a shared corner)."""
    centroids: dict[int, tuple[float, float, float]] = {}
    for face_id in mesh.face_ids:
        mask = mesh.face_tag_per_triangle == face_id
        verts = mesh.vertices[mesh.indices[mask].reshape(-1)]
        c = verts.mean(axis=0)
        centroids[face_id] = (float(c[0]), float(c[1]), float(c[2]))
    return centroids


def test_resolve_face_by_id_matches_tessellate_ordering():
    # Parity (ADR-0011 R1): the finder's face `i` is the face `tessellate`
    # tagged as face_id `i`. Each face's interior centroid lies on exactly that
    # face; the id-resolved face must contain *its* centroid and no other's.
    # (Lives here, not in test_finder, so the in-process tessellation runs
    # after the OSMesa render test — see _cube's note.)
    cube = _cube()
    centroids = _face_centroids(tessellate(cube))
    assert len(centroids) == 6  # cube
    for face_id, centroid in centroids.items():
        by_id = resolve_face(cube, face_id, (999.0, 999.0, 999.0))  # bogus point
        assert _contains(by_id, centroid)
        others = [c for fid, c in centroids.items() if fid != face_id]
        assert all(not _contains(by_id, o) for o in others)
