// web/picking — raycast → triangle → face id (F4, F5, N1). Pure local lookup
// against the streamed mesh; NO transport (N1: hover/click do zero WS calls).
// The face id comes from the per-triangle faceTag buffer baked into the mesh by
// the backend tessellator (ADR-0008).
import * as THREE from 'three'

export interface PickHit {
  /** Kernel-owned face id of the picked triangle (session-stable; ADR-0008). */
  faceTag: number
  /** Triangle (face) index returned by the raycaster. */
  triangleIndex: number
  /** World-space hit point. */
  point: THREE.Vector3
}

/**
 * Raycast `ndc` (normalized device coords, [-1,1]) against `mesh` and resolve
 * the hit triangle to its baked face id. Returns null on a miss.
 */
export function pickFace(
  raycaster: THREE.Raycaster,
  camera: THREE.Camera,
  mesh: THREE.Object3D,
  faceTagPerTriangle: Uint32Array,
  ndc: THREE.Vector2,
): PickHit | null {
  raycaster.setFromCamera(ndc, camera)
  const hits = raycaster.intersectObject(mesh, false)
  if (hits.length === 0) return null

  const hit = hits[0]
  if (hit.faceIndex == null) return null
  const faceTag = faceTagPerTriangle[hit.faceIndex]
  if (faceTag === undefined) return null

  return { faceTag, triangleIndex: hit.faceIndex, point: hit.point.clone() }
}
