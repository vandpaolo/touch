// Decode the sidecar's binary mesh frame.
//
// Mirrors spike/sidecar/touch_sidecar/wire.py, which follows
// docs/02-data-model.md §Mesh. Little-endian layout:
//
//   offset  type        count          field
//   0       uint8       1              version = 1
//   1       uint8       3              reserved
//   4       uint32      1              vertex_count   (N)
//   8       uint32      1              triangle_count (M)
//   12      uint32      1              edge_segment_count (L)
//   16      float32     N*3            vertices
//   ...     float32     N*3            normals
//   ...     uint32      M*3            indices
//   ...     uint32      M              face_tag_per_triangle
//   ...     uint32      L              edge_tag_per_segment

export interface Mesh {
  version: number;
  vertices: Float32Array; // N*3
  normals: Float32Array; // N*3
  indices: Uint32Array; // M*3
  faceTagPerTriangle: Uint32Array; // M
  edgeTagPerSegment: Uint32Array; // L
}

const VERSION = 1;

export function decodeMesh(buffer: ArrayBuffer): Mesh {
  const view = new DataView(buffer);
  const version = view.getUint8(0);
  if (version !== VERSION) {
    throw new Error(`unsupported mesh-frame version: ${version}`);
  }
  const n = view.getUint32(4, true);
  const m = view.getUint32(8, true);
  const l = view.getUint32(12, true);

  // All sections are 4-byte aligned (header is 16 bytes; every field is a
  // multiple of 4 bytes), so typed-array views over the buffer are safe.
  let off = 16;
  const vertices = new Float32Array(buffer, off, n * 3);
  off += n * 3 * 4;
  const normals = new Float32Array(buffer, off, n * 3);
  off += n * 3 * 4;
  const indices = new Uint32Array(buffer, off, m * 3);
  off += m * 3 * 4;
  const faceTagPerTriangle = new Uint32Array(buffer, off, m);
  off += m * 4;
  const edgeTagPerSegment = new Uint32Array(buffer, off, l);

  return { version, vertices, normals, indices, faceTagPerTriangle, edgeTagPerSegment };
}
