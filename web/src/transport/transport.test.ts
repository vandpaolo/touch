import { describe, expect, it } from 'vitest'
import type { MsgMeshFrame } from '../protocol-types'
import { decodeMeshFrame, resolveWsUrl } from './index.ts'

// Build a binary frame in the exact wire layout frames.pack produces:
// vertices(f32) · normals(f32) · indices(u32) · faceTag(u32) · edgeTag(u32),
// little-endian. (Test host is little-endian, matching the backend.)
function packFrame(
  vertices: number[],
  normals: number[],
  indices: number[],
  faceTags: number[],
  edgeTags: number[],
): ArrayBuffer {
  const bytes = (vertices.length + normals.length + indices.length + faceTags.length + edgeTags.length) * 4
  const buf = new ArrayBuffer(bytes)
  let off = 0
  const writeF32 = (xs: number[]) => {
    new Float32Array(buf, off, xs.length).set(xs)
    off += xs.length * 4
  }
  const writeU32 = (xs: number[]) => {
    new Uint32Array(buf, off, xs.length).set(xs)
    off += xs.length * 4
  }
  writeF32(vertices)
  writeF32(normals)
  writeU32(indices)
  writeU32(faceTags)
  writeU32(edgeTags)
  return buf
}

describe('decodeMeshFrame', () => {
  it('slices a single-triangle frame into typed buffers', () => {
    const vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    const normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    const indices = [0, 1, 2]
    const faceTags = [7]
    const edgeTags: number[] = []
    const env: MsgMeshFrame = {
      type: 'meshFrame',
      version: 3,
      vertex_count: 3,
      triangle_count: 1,
      edge_segment_count: 0,
      face_id_to_finder_hint: {},
    }

    const mesh = decodeMeshFrame(env, packFrame(vertices, normals, indices, faceTags, edgeTags))

    expect(mesh.version).toBe(3)
    expect(Array.from(mesh.vertices)).toEqual(vertices)
    expect(Array.from(mesh.normals)).toEqual(normals)
    expect(Array.from(mesh.indices)).toEqual(indices)
    expect(Array.from(mesh.faceTagPerTriangle)).toEqual(faceTags)
    expect(mesh.edgeTagPerSegment.length).toBe(0)
  })

  it('decodes edge segments when present', () => {
    const env: MsgMeshFrame = {
      type: 'meshFrame',
      version: 1,
      vertex_count: 1,
      triangle_count: 0,
      edge_segment_count: 2,
      face_id_to_finder_hint: {},
    }
    const mesh = decodeMeshFrame(env, packFrame([0, 0, 0], [0, 0, 1], [], [], [4, 9]))
    expect(Array.from(mesh.edgeTagPerSegment)).toEqual([4, 9])
  })

  it('throws on a size mismatch (truncated or oversized frame)', () => {
    const env: MsgMeshFrame = {
      type: 'meshFrame',
      version: 1,
      vertex_count: 3,
      triangle_count: 1,
      edge_segment_count: 0,
      face_id_to_finder_hint: {},
    }
    // Frame for vertex_count=2 — too short for the envelope's claim of 3.
    const tooShort = packFrame([0, 0, 0, 1, 0, 0], [0, 0, 1, 0, 0, 1], [0, 1, 2], [7], [])
    expect(() => decodeMeshFrame(env, tooShort)).toThrow(/size mismatch/)
  })
})

describe('resolveWsUrl', () => {
  it('prefers an explicit url', () => {
    expect(resolveWsUrl({ url: 'ws://example:1234/x' })).toBe('ws://example:1234/x')
  })

  it('defaults to the localhost sidecar on 8765', () => {
    expect(resolveWsUrl()).toBe('ws://localhost:8765')
  })

  it('honours an explicit port', () => {
    expect(resolveWsUrl({ port: 9000 })).toBe('ws://localhost:9000')
  })
})
