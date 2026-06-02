// web/transport — the WS client. The ONLY module that opens a WebSocket
// (dependency rule). It speaks the generated protocol: JSON text frames decode
// to typed Messages; a `meshFrame` envelope is paired with the binary frame
// that immediately follows it and decoded into typed buffers (F20, frames.py).
//
// Reconnect-on-restart (F16) is this module's eventual responsibility but is
// realized in T8; Day-4 scope is connect + typed event dispatch.
import type {
  Message,
  MsgConversationTurn,
  MsgDocument,
  MsgError,
  MsgFileList,
  MsgMeshFrame,
  MsgOp,
  MsgProgress,
  MsgReady,
} from '../protocol-types'

const DEFAULT_PORT = 8765

// --- Mesh decode (pure, unit-tested) ------------------------------------

/** A decoded mesh frame: typed buffers + the per-face finder hints. */
export interface MeshData {
  version: number
  vertices: Float32Array // vertex_count * 3
  normals: Float32Array // vertex_count * 3
  indices: Uint32Array // triangle_count * 3
  faceTagPerTriangle: Uint32Array // triangle_count
  edgeTagPerSegment: Uint32Array // edge_segment_count
  faceIdToFinderHint: MsgMeshFrame['face_id_to_finder_hint']
}

/**
 * Slice a binary mesh frame into typed buffers using the envelope counts.
 * Layout (little-endian, matches frames.pack): vertices(f32) · normals(f32) ·
 * indices(u32) · faceTagPerTriangle(u32) · edgeTagPerSegment(u32).
 *
 * Views are zero-copy over `buffer`. Endianness: typed-array views read in
 * platform byte order; all targets (x86/arm desktop) are little-endian, which
 * matches the backend's explicit '<f4'/'<u4' packing.
 */
export function decodeMeshFrame(env: MsgMeshFrame, buffer: ArrayBuffer): MeshData {
  const v = env.vertex_count
  const t = env.triangle_count
  const e = env.edge_segment_count

  // Validate up front: a short buffer would otherwise throw an opaque
  // RangeError from a typed-array constructor mid-slice.
  const expectedBytes = (v * 3 + v * 3 + t * 3 + t + e) * 4
  if (buffer.byteLength !== expectedBytes) {
    throw new Error(
      `meshFrame binary size mismatch: got ${buffer.byteLength} bytes, expected ${expectedBytes}`,
    )
  }

  let off = 0
  const f32 = (n: number): Float32Array => {
    const a = new Float32Array(buffer, off, n)
    off += n * 4
    return a
  }
  const u32 = (n: number): Uint32Array => {
    const a = new Uint32Array(buffer, off, n)
    off += n * 4
    return a
  }
  const vertices = f32(v * 3)
  const normals = f32(v * 3)
  const indices = u32(t * 3)
  const faceTagPerTriangle = u32(t)
  const edgeTagPerSegment = u32(e)

  return {
    version: env.version,
    vertices,
    normals,
    indices,
    faceTagPerTriangle,
    edgeTagPerSegment,
    faceIdToFinderHint: env.face_id_to_finder_hint,
  }
}

// --- URL resolution -----------------------------------------------------

export interface TransportOptions {
  /** Explicit full ws URL; wins over everything. */
  url?: string
  /** Relative ws path for a reverse proxy (e.g. "/ws"); built against the page origin. */
  path?: string
  /** Direct-connection port (default 8765). */
  port?: number
}

/**
 * Resolve the WS endpoint, config-driven (notes/questions.md — keep the FE URL
 * relative-path capable so a future Caddy reverse-proxy is trivial):
 *   1. explicit opts.url
 *   2. ?ws=<full-url> query param
 *   3. relative path (opts.path or ?wsPath=) → wss?://<page-host><path>
 *   4. default → ws://localhost:<port> (the localhost sidecar, ADR-0005)
 */
export function resolveWsUrl(opts: TransportOptions = {}): string {
  if (opts.url) return opts.url
  const loc = typeof window !== 'undefined' ? window.location : undefined
  const params = new URLSearchParams(loc?.search ?? '')

  const wsParam = params.get('ws')
  if (wsParam) return wsParam

  const path = opts.path ?? params.get('wsPath') ?? undefined
  if (path && loc) {
    const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${loc.host}${path}`
  }

  const port = opts.port ?? (Number(params.get('port')) || DEFAULT_PORT)
  return `ws://localhost:${port}`
}

// --- Transport ----------------------------------------------------------

interface TransportEvents {
  open: void
  close: { code: number; reason: string }
  socketError: Event
  ready: MsgReady
  op: MsgOp
  progress: MsgProgress
  error: MsgError
  conversationTurn: MsgConversationTurn
  document: MsgDocument
  fileList: MsgFileList
  mesh: MeshData
}

type Handler<T> = (payload: T) => void

export class Transport {
  readonly endpoint: string
  private ws?: WebSocket
  private pendingMeshFrame?: MsgMeshFrame
  // Stored loosely; the on()/emit() signatures keep the public surface typed.
  private readonly handlers = new Map<keyof TransportEvents, Set<Handler<unknown>>>()

  constructor(opts: TransportOptions = {}) {
    this.endpoint = resolveWsUrl(opts)
  }

  connect(): void {
    const ws = new WebSocket(this.endpoint)
    ws.binaryType = 'arraybuffer'
    ws.onopen = () => this.emit('open', undefined)
    ws.onclose = (e) => this.emit('close', { code: e.code, reason: e.reason })
    ws.onerror = (e) => this.emit('socketError', e)
    ws.onmessage = (e) => this.onMessage(e.data as string | ArrayBuffer)
    this.ws = ws
  }

  /** Send a control message (FE→BE). */
  send(msg: Message): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('transport not open')
    }
    this.ws.send(JSON.stringify(msg))
  }

  close(): void {
    this.ws?.close()
    this.ws = undefined
  }

  /** Subscribe; returns an unsubscribe fn. */
  on<K extends keyof TransportEvents>(
    type: K,
    handler: Handler<TransportEvents[K]>,
  ): () => void {
    let set = this.handlers.get(type)
    if (!set) {
      set = new Set()
      this.handlers.set(type, set)
    }
    set.add(handler as Handler<unknown>)
    return () => set.delete(handler as Handler<unknown>)
  }

  private emit<K extends keyof TransportEvents>(type: K, payload: TransportEvents[K]): void {
    this.handlers.get(type)?.forEach((h) => (h as Handler<TransportEvents[K]>)(payload))
  }

  private onMessage(data: string | ArrayBuffer): void {
    if (typeof data === 'string') this.onJson(data)
    else this.onBinary(data)
  }

  private onJson(text: string): void {
    let msg: Message
    try {
      msg = JSON.parse(text) as Message
    } catch {
      console.warn('[transport] dropped non-JSON text frame')
      return
    }
    if (msg.type === 'meshFrame') {
      // Buffers arrive in the very next WS frame; hold the envelope until then.
      this.pendingMeshFrame = msg
      return
    }
    this.dispatch(msg)
  }

  private onBinary(buffer: ArrayBuffer): void {
    const env = this.pendingMeshFrame
    if (!env) {
      console.warn('[transport] binary frame with no preceding meshFrame envelope; dropped')
      return
    }
    this.pendingMeshFrame = undefined
    this.emit('mesh', decodeMeshFrame(env, buffer))
  }

  private dispatch(msg: Message): void {
    switch (msg.type) {
      case 'ready':
        this.emit('ready', msg)
        break
      case 'op':
        this.emit('op', msg)
        break
      case 'progress':
        this.emit('progress', msg)
        break
      case 'error':
        this.emit('error', msg)
        break
      case 'conversationTurn':
        this.emit('conversationTurn', msg)
        break
      case 'document':
        this.emit('document', msg)
        break
      case 'fileList':
        this.emit('fileList', msg)
        break
      default:
        // FE→BE message types echoed back, or unknown — ignore.
        break
    }
  }
}
