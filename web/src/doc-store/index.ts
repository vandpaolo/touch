// web/doc-store — FE-side mirror of the document state: the current mesh, the
// operation-history (stub until T3/T4), and a dirty flag. Pure state container
// with a subscribe API; it has no outbound module deps (the transport pushes
// into it; the viewport subscribes to it). MeshData is a type-only import (the
// decoded value object originates in transport).
import type { MsgDocument, Operation } from '../protocol-types'
import type { MeshData } from '../transport'

export interface DocState {
  /** The mesh currently displayed, or null before the first frame. */
  mesh: MeshData | null
  /** Document name (from the backend snapshot). */
  name: string
  /** Operation history mirror (authoritative copy from the backend snapshot). */
  history: Operation[]
  /** Unsaved-changes flag. */
  dirty: boolean
  /** Undo/redo availability (drives the controls). */
  canUndo: boolean
  canRedo: boolean
}

type Listener = (state: DocState) => void

const EMPTY: DocState = {
  mesh: null,
  name: 'untitled',
  history: [],
  dirty: false,
  canUndo: false,
  canRedo: false,
}

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

  /** Mirror an authoritative document snapshot from the backend (T4). */
  applyDocument(snap: MsgDocument): void {
    this.state = {
      ...this.state,
      name: snap.name,
      history: snap.history,
      dirty: snap.dirty,
      canUndo: snap.can_undo,
      canRedo: snap.can_redo,
    }
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
