// web/viewport — placeholder host (Day 2). The real three.js scene + NX camera
// (the Viewport class) mounts into this slot in Day 7. For now it's just the
// centre-panel canvas mount point so the shell layout is complete.
export function ViewportHost() {
  return (
    <div className="viewport-host" data-testid="viewport-host">
      <div className="viewport-placeholder">viewport — three.js scene lands in Day 7</div>
    </div>
  )
}
