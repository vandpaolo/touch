// web/viewport — the centre-panel mount point. The Viewport class (three.js)
// is attached to this container by web/app; the canvas fills it.
import type { Ref } from 'react'

export function ViewportHost({ containerRef }: { containerRef: Ref<HTMLDivElement> }) {
  return <div className="viewport-host" data-testid="viewport-host" ref={containerRef} />
}
