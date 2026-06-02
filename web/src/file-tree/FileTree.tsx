// web/file-tree — the VS-Code/Cursor-style folder Explorer (F18). A hand-rolled
// recursive tree over web/workspace (lazy expand), themed with Codicons. The
// backend owns the files (ADR-0010); this just renders the tree + issues
// open/new commands through the workspace store.
import { useEffect, useReducer } from 'react'
import { childPath, type Workspace } from '../workspace'

function isTouch(name: string): boolean {
  return name.endsWith('.touch')
}

function Row({
  ws,
  name,
  path,
  isDir,
  depth,
  onOpen,
}: {
  ws: Workspace
  name: string
  path: string
  isDir: boolean
  depth: number
  onOpen: (path: string) => void
}) {
  const expanded = isDir && ws.isExpanded(path)
  const active = !isDir && path === ws.activePath()
  const fileIcon = isTouch(name) ? 'codicon-file-code' : 'codicon-file'

  return (
    <>
      <button
        type="button"
        className={`ws-row ${active ? 'active' : ''}`}
        style={{ paddingLeft: 6 + depth * 12 }}
        onClick={() => (isDir ? ws.toggle(path) : onOpen(path))}
        title={name}
      >
        <i
          className={`codicon ws-chevron ${
            isDir ? (expanded ? 'codicon-chevron-down' : 'codicon-chevron-right') : 'ws-chevron-blank'
          }`}
          aria-hidden="true"
        />
        <i
          className={`codicon ${isDir ? (expanded ? 'codicon-folder-opened' : 'codicon-folder') : fileIcon}`}
          aria-hidden="true"
        />
        <span className="ws-name">{name}</span>
      </button>
      {isDir &&
        expanded &&
        (ws.entries(path) ?? []).map((e) => (
          <Row
            key={childPath(path, e.name)}
            ws={ws}
            name={e.name}
            path={childPath(path, e.name)}
            isDir={e.is_dir}
            depth={depth + 1}
            onOpen={onOpen}
          />
        ))}
    </>
  )
}

export function FileTree({ ws, onOpen }: { ws: Workspace; onOpen: (path: string) => void }) {
  const [, rerender] = useReducer((x: number) => x + 1, 0)
  useEffect(() => ws.subscribe(rerender), [ws])

  const newPart = () => {
    const raw = window.prompt('New part name:', 'part.touch')
    if (!raw) return
    ws.newPart(isTouch(raw) ? raw : `${raw}.touch`)
  }

  const root = ws.entries('')

  return (
    <nav className="file-tree" data-testid="file-tree" aria-label="Explorer">
      <div className="panel-title">
        <span>Explorer</span>
        {ws.isOpen() && (
          <span className="ft-actions">
            <button className="ft-action" type="button" title="New part" onClick={newPart}>
              <i className="codicon codicon-new-file" aria-hidden="true" />
            </button>
          </span>
        )}
      </div>
      {!ws.isOpen() ? (
        <div className="file-tree-empty">No folder open — File → Open Folder</div>
      ) : (
        <div className="ws-tree">
          {root === undefined && <div className="file-tree-empty">Loading…</div>}
          {root && root.length === 0 && <div className="file-tree-empty">(empty folder)</div>}
          {(root ?? []).map((e) => (
            <Row
              key={childPath('', e.name)}
              ws={ws}
              name={e.name}
              path={childPath('', e.name)}
              isDir={e.is_dir}
              depth={0}
              onOpen={onOpen}
            />
          ))}
        </div>
      )}
    </nav>
  )
}
