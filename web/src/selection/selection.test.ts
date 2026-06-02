import * as THREE from 'three'
import { describe, expect, it } from 'vitest'
import type { PickHit } from '../picking'
import type { MsgMeshFrame, Selection } from '../protocol-types'
import { SelectionStore, selectionFromHit } from './index.ts'

const hint: Selection = {
  target: 'face',
  point_xyz: [0, 0, 20],
  finder: [{ kind: 'contains_point', point_xyz: [0, 0, 20], tol_mm: 0.5 }],
  face_id_at_capture: 3,
}
const hints: MsgMeshFrame['face_id_to_finder_hint'] = { '3': hint }

describe('selectionFromHit', () => {
  it('builds a Selection from the face hint, pinned to the click point', () => {
    const hit: PickHit = { faceTag: 3, triangleIndex: 1, point: new THREE.Vector3(1, 2, 20) }
    const sel = selectionFromHit(hit, hints)
    expect(sel).not.toBeNull()
    expect(sel?.target).toBe('face')
    expect(sel?.point_xyz).toEqual([1, 2, 20])
    expect(sel?.face_id_at_capture).toBe(3)
    expect(sel?.finder).toHaveLength(1)
  })

  it('returns null when no hint exists for the picked face', () => {
    const hit: PickHit = { faceTag: 99, triangleIndex: 0, point: new THREE.Vector3() }
    expect(selectionFromHit(hit, hints)).toBeNull()
  })
})

describe('SelectionStore', () => {
  it('set/get/clear and notifies subscribers', () => {
    const store = new SelectionStore()
    let seen: Selection | null | undefined
    store.subscribe((s) => {
      seen = s
    })

    expect(store.get()).toBeNull()
    store.set(hint)
    expect(store.get()).toBe(hint)
    expect(seen).toBe(hint)
    store.clear()
    expect(store.get()).toBeNull()
    expect(seen).toBeNull()
  })
})
