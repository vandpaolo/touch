"""Binary mesh-frame (de)serialization for the WS protocol (F20, ADR-0005).

A mesh is shipped as a JSON `meshFrame` envelope (counts + face->finder hints)
immediately followed by one binary WS frame holding the raw buffers, in order:
vertices(f32) · normals(f32) · indices(u32) · face_tag_per_triangle(u32) ·
edge_tag_per_segment(u32). The receiver slices the binary frame using the
counts from the envelope.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from touch_backend._generated.protocol import MsgMeshFrame
from touch_backend.tessellate import Mesh


@dataclass
class MeshBuffers:
    """The geometry recovered from a binary frame (no JSON-side hints)."""

    version: int
    vertices: np.ndarray
    normals: np.ndarray
    indices: np.ndarray
    face_tag_per_triangle: np.ndarray
    edge_tag_per_segment: np.ndarray


def mesh_frame_envelope(mesh: Mesh) -> MsgMeshFrame:
    """Build the JSON `meshFrame` envelope that precedes the binary frame.

    Seeds a minimal click->selection finder hint per face (a `contains_point`
    predicate anchored at an on-surface point); richer predicates land with the
    real selection flow (T3).
    """
    hint = {
        str(face_id): {
            "target": "face",
            "point_xyz": list(mesh.face_anchor[face_id]),
            "finder": [
                {
                    "kind": "contains_point",
                    "point_xyz": list(mesh.face_anchor[face_id]),
                    "tol_mm": 0.5,
                }
            ],
            "entity_id_at_capture": face_id,
        }
        for face_id in mesh.face_ids
    }
    return MsgMeshFrame.model_validate(
        {
            "type": "meshFrame",
            "version": mesh.version,
            "vertex_count": int(mesh.vertices.shape[0]),
            "triangle_count": int(mesh.indices.shape[0]),
            "edge_segment_count": int(mesh.edge_tag_per_segment.shape[0]),
            "face_id_to_finder_hint": hint,
        }
    )


def pack(mesh: Mesh) -> bytes:
    """Serialize a mesh's buffers into one little-endian binary frame."""
    return (
        mesh.vertices.astype("<f4").tobytes()
        + mesh.normals.astype("<f4").tobytes()
        + mesh.indices.astype("<u4").tobytes()
        + mesh.face_tag_per_triangle.astype("<u4").tobytes()
        + mesh.edge_tag_per_segment.astype("<u4").tobytes()
    )


def unpack(
    data: bytes,
    *,
    version: int,
    vertex_count: int,
    triangle_count: int,
    edge_segment_count: int,
) -> MeshBuffers:
    """Recover mesh buffers from a binary frame, sliced by the envelope counts."""
    offset = 0

    def take(dtype: str, count: int) -> np.ndarray:
        nonlocal offset
        arr = np.frombuffer(data, dtype=dtype, count=count, offset=offset)
        offset += count * np.dtype(dtype).itemsize
        return arr

    vertices = take("<f4", vertex_count * 3).reshape(-1, 3)
    normals = take("<f4", vertex_count * 3).reshape(-1, 3)
    indices = take("<u4", triangle_count * 3).reshape(-1, 3)
    face_tag = take("<u4", triangle_count)
    edge_tag = take("<u4", edge_segment_count)
    return MeshBuffers(
        version=version,
        vertices=vertices,
        normals=normals,
        indices=indices,
        face_tag_per_triangle=face_tag,
        edge_tag_per_segment=edge_tag,
    )
