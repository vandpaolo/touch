// web/selection — current-selection state (F5). Holds the picked Selection
// (face + point + finder) in the frontend; no backend round-trip. The prompt
// panel (web/prompt) reads this and sends it on submit.
import type { PickHit } from '../picking'
import type { MsgMeshFrame, Selection } from '../protocol-types'

type FinderHints = MsgMeshFrame['face_id_to_finder_hint']

/**
 * Build a protocol `Selection` from a pick. The backend pre-seeds a
 * `contains_point` finder per face in the mesh frame (ADR-0008); we take that
 * hint and pin `point_xyz` to the actual click point for transparency.
 */
export function selectionFromHit(hit: PickHit, hints: FinderHints): Selection | null {
  const hint = hints[String(hit.faceTag)]
  if (!hint) return null
  return {
    ...hint,
    point_xyz: [hit.point.x, hit.point.y, hit.point.z],
    face_id_at_capture: hit.faceTag,
  }
}

type Listener = (selection: Selection | null) => void

export class SelectionStore {
  private current: Selection | null = null
  private readonly listeners = new Set<Listener>()

  get(): Selection | null {
    return this.current
  }

  set(selection: Selection | null): void {
    this.current = selection
    this.notify()
  }

  clear(): void {
    this.set(null)
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notify(): void {
    for (const listener of this.listeners) listener(this.current)
  }
}
