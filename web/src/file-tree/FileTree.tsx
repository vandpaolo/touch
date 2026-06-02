// web/file-tree — the .touch project explorer (F10/F18), VS-Code/Cursor-style:
// an Explorer header with New/Save actions and a flat list of files; click to
// open, the active file highlighted with a dirty dot. Backend owns the files
// (over WS); this is the view.

function FileIcon() {
  return (
    <svg
      className="ft-icon"
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M14 3v5h5" />
      <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    </svg>
  )
}

export function FileTree({
  files,
  activeName,
  dirty,
  onOpen,
  onNew,
  onSave,
}: {
  files: string[]
  activeName: string
  dirty: boolean
  onOpen: (name: string) => void
  onNew: () => void
  onSave: () => void
}) {
  return (
    <nav className="file-tree" data-testid="file-tree" aria-label="Project files">
      <div className="panel-title">
        <span>Explorer</span>
        <span className="ft-actions">
          <button className="ft-action" type="button" title="New file" onClick={onNew}>
            New
          </button>
          <button className="ft-action" type="button" title="Save (Ctrl+S)" onClick={onSave}>
            Save
          </button>
        </span>
      </div>
      <ul className="file-tree-list">
        {files.length === 0 && <li className="file-tree-empty">No .touch files</li>}
        {files.map((file) => {
          const active = file === activeName
          return (
            <li key={file}>
              <button
                type="button"
                className={`ft-file ${active ? 'active' : ''}`}
                onClick={() => onOpen(file)}
                aria-current={active ? 'true' : undefined}
              >
                <FileIcon />
                <span className="ft-name">{file}</span>
                {active && dirty && (
                  <span className="ft-dirty" title="Unsaved changes" aria-label="unsaved">
                    ●
                  </span>
                )}
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
