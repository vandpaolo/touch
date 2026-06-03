import { describe, expect, it } from 'vitest'
import type { Selection } from '../protocol-types'
import { buildPlanMessage } from './PromptPanel.tsx'

const selection: Selection = {
  target: 'face',
  point_xyz: [1, 2, 20],
  finder: [{ kind: 'contains_point', point_xyz: [1, 2, 20], tol_mm: 0.5 }],
  entity_id_at_capture: 3,
}

describe('buildPlanMessage', () => {
  it('produces a plan message carrying the selection + prompt text', () => {
    const msg = buildPlanMessage(selection, 'add a 5 mm chamfer here')
    expect(msg.type).toBe('plan')
    expect(msg.prompt_text).toBe('add a 5 mm chamfer here')
    expect(msg.selection).toBe(selection)
  })

  it('allows a null selection (manual prompt, no pick)', () => {
    const msg = buildPlanMessage(null, 'a 40 mm cube')
    expect(msg.type).toBe('plan')
    expect(msg.selection).toBeNull()
  })
})
