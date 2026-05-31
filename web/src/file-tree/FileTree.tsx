// web/file-tree — placeholder (Day 2). Real .touch project navigation
// (open / new / rename) lands later; native dialogs go through web/platform.
export function FileTree() {
  return (
    <nav className="file-tree" data-testid="file-tree" aria-label="Project files">
      <div className="panel-title">Explorer</div>
      <ul className="file-tree-list">
        <li className="file-tree-empty">No project open</li>
      </ul>
    </nav>
  )
}
