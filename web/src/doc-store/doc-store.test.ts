import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { MsgMeshFrame } from '../protocol-types'
import { Transport } from '../transport'
import type { MeshData } from '../transport'
import { DocStore } from './index.ts'

function meshStub(): MeshData {
  return {
    version: 1,
    vertices: new Float32Array([0, 0, 0]),
    normals: new Float32Array([0, 0, 1]),
    indices: new Uint32Array([]),
    faceTagPerTriangle: new Uint32Array([]),
    edgeTagPerSegment: new Uint32Array([]),
    faceIdToFinderHint: {},
  }
}

describe('DocStore', () => {
  it('applyMesh updates state and fires subscribers (not dirty)', () => {
    const store = new DocStore()
    const mesh = meshStub()
    let seen: ReturnType<DocStore['getState']> | undefined
    store.subscribe((s) => {
      seen = s
    })

    store.applyMesh(mesh)

    expect(store.getMesh()).toBe(mesh)
    expect(seen?.mesh).toBe(mesh)
    expect(seen?.dirty).toBe(false)
  })

  it('applyOp appends to history and marks dirty', () => {
    const store = new DocStore()
    const op = {
      id: 'op1',
      kind: 'box',
      params: { length: 1, width: 1, height: 1 },
      selection: null,
      prompt_text: 'x',
      conversation: [],
      created_at: '2026-06-01T00:00:00Z',
    } as unknown as Parameters<DocStore['applyOp']>[0]

    store.applyOp(op)

    expect(store.getState().history).toHaveLength(1)
    expect(store.getState().dirty).toBe(true)
  })

  it('unsubscribe stops notifications', () => {
    const store = new DocStore()
    let calls = 0
    const off = store.subscribe(() => {
      calls += 1
    })
    store.applyMesh(meshStub())
    off()
    store.applyMesh(meshStub())
    expect(calls).toBe(1)
  })
})

// --- transport -> doc-store integration (fake WebSocket) ----------------

class FakeWebSocket {
  static OPEN = 1
  static instances: FakeWebSocket[] = []
  binaryType = 'blob'
  readyState = 1
  onopen: (() => void) | null = null
  onclose: ((e: unknown) => void) | null = null
  onerror: ((e: unknown) => void) | null = null
  onmessage: ((e: { data: string | ArrayBuffer }) => void) | null = null
  constructor(public url: string) {
    FakeWebSocket.instances.push(this)
  }
  send(): void {}
  close(): void {}
}

function packFrame(v: number[], n: number[], idx: number[], face: number[], edge: number[]): ArrayBuffer {
  const buf = new ArrayBuffer((v.length + n.length + idx.length + face.length + edge.length) * 4)
  let off = 0
  const wF = (xs: number[]) => {
    new Float32Array(buf, off, xs.length).set(xs)
    off += xs.length * 4
  }
  const wU = (xs: number[]) => {
    new Uint32Array(buf, off, xs.length).set(xs)
    off += xs.length * 4
  }
  wF(v)
  wF(n)
  wU(idx)
  wU(face)
  wU(edge)
  return buf
}

describe('transport -> doc-store', () => {
  beforeEach(() => {
    FakeWebSocket.instances = []
    vi.stubGlobal('WebSocket', FakeWebSocket)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('a meshFrame envelope + binary frame lands decoded in the store', () => {
    const store = new DocStore()
    const transport = new Transport({ url: 'ws://test' })
    transport.on('mesh', (m) => store.applyMesh(m))
    transport.connect()

    const ws = FakeWebSocket.instances.at(-1)
    expect(ws).toBeDefined()

    const env: MsgMeshFrame = {
      type: 'meshFrame',
      version: 2,
      vertex_count: 3,
      triangle_count: 1,
      edge_segment_count: 0,
      face_id_to_finder_hint: {},
    }
    ws!.onmessage!({ data: JSON.stringify(env) })
    ws!.onmessage!({
      data: packFrame([0, 0, 0, 1, 0, 0, 0, 1, 0], [0, 0, 1, 0, 0, 1, 0, 0, 1], [0, 1, 2], [7], []),
    })

    const mesh = store.getMesh()
    expect(mesh).not.toBeNull()
    expect(mesh?.version).toBe(2)
    expect(Array.from(mesh!.indices)).toEqual([0, 1, 2])
    expect(Array.from(mesh!.faceTagPerTriangle)).toEqual([7])
  })
})
