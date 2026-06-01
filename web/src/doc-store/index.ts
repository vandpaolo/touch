// web/doc-store — FE-side mirror of the document state: the current mesh, the
// operation-history (stub until T3/T4), and a dirty flag. Pure state container
// with a subscribe API; it has no outbound module deps (the transport pushes
// into it; the viewport subscribes to it). MeshData is a type-only import (the
// decoded value object originates in transport).
import type { Operation } from '../protocol-types'
import type { MeshData } from '../transport'

export interface DocState {
  /** The mesh currently displayed, or null before the first frame. */
  mesh: MeshData | null
  /** Operation history mirror (append-only; populated from T3 onward). */
  history: Operation[]
  /** Unsaved-changes flag (set by history edits, not by mesh refreshes). */
  dirty: boolean
}

type Listener = (state: DocState) => void

const EMPTY: DocState = { mesh: null, history: [], dirty: false }

export class DocStore {
  private state: DocState = EMPTY
  private readonly listeners = new Set<Listener>()

  getState(): DocState {
    return this.state
  }

  getMesh(): MeshData | null {
    return this.state.mesh
  }

  /** Replace the displayed mesh (a backend geometry refresh — not a user edit). */
  applyMesh(mesh: MeshData): void {
    this.state = { ...this.state, mesh }
    this.notify()
  }

  /** Append an operation to the history mirror and mark the document dirty. */
  applyOp(op: Operation): void {
    this.state = { ...this.state, history: [...this.state.history, op], dirty: true }
    this.notify()
  }

  /** Subscribe to state changes; returns an unsubscribe fn. */
  subscribe(listener: Listener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notify(): void {
    for (const listener of this.listeners) listener(this.state)
  }
}
