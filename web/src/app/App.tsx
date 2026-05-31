// web/app — the shell (F2). Owns the VS-Code-like layout: menu bar (top),
// activity bar + resizable sidebar (file-tree) + viewport host (centre),
// status bar (bottom), and Settings reachable from the menu/activity bar.
// The composition root of the renderer.
import { useCallback, useState, type PointerEvent as ReactPointerEvent } from 'react'
import { FileTree } from '../file-tree/FileTree.tsx'
import { ViewportHost } from '../viewport/ViewportHost.tsx'
import { SettingsPanel } from '../settings/SettingsPanel.tsx'
import { ActivityBar } from './ActivityBar.tsx'
import { StatusBar } from './StatusBar.tsx'
import './app.css'

const SIDEBAR_MIN = 160
const SIDEBAR_MAX = 480

export function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarWidth, setSidebarWidth] = useState(240)

  // Drag-to-resize the sidebar. Capture the start geometry on pointer-down and
  // track on window so the drag survives the cursor leaving the thin handle.
  const startResize = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      e.preventDefault()
      const startX = e.clientX
      const startWidth = sidebarWidth
      const onMove = (ev: PointerEvent) => {
        const next = Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, startWidth + (ev.clientX - startX)))
        setSidebarWidth(next)
      }
      const onUp = () => {
        window.removeEventListener('pointermove', onMove)
        window.removeEventListener('pointerup', onUp)
        document.body.style.cursor = ''
      }
      window.addEventListener('pointermove', onMove)
      window.addEventListener('pointerup', onUp)
      document.body.style.cursor = 'col-resize'
    },
    [sidebarWidth],
  )

  return (
    <div className="app">
      <header className="menubar">
        <span className="menubar-brand">Touch</span>
        <nav className="menubar-menus" aria-label="Main menu">
          <button className="menubar-item" type="button" disabled>
            File
          </button>
          <button className="menubar-item" type="button" onClick={() => setSettingsOpen(true)}>
            Settings
          </button>
        </nav>
      </header>

      <div className="body">
        <ActivityBar
          explorerActive={sidebarOpen}
          onToggleExplorer={() => setSidebarOpen((o) => !o)}
          onOpenSettings={() => setSettingsOpen(true)}
        />
        {sidebarOpen && (
          <>
            <aside className="sidebar" style={{ width: sidebarWidth }}>
              <FileTree />
            </aside>
            <div
              className="resizer"
              role="separator"
              aria-orientation="vertical"
              aria-label="Resize sidebar"
              onPointerDown={startResize}
            />
          </>
        )}
        <main className="main" aria-label="Viewport">
          <ViewportHost />
        </main>
      </div>

      <StatusBar />

      {settingsOpen && <SettingsPanel onClose={() => setSettingsOpen(false)} />}
    </div>
  )
}
