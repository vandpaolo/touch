// web/app — the shell (F2). Owns the VS-Code-like layout: menu bar (top),
// activity bar + resizable sidebar (file-tree) + viewport host (centre),
// status bar (bottom), and Settings reachable from the menu/activity bar.
// The composition root of the renderer.
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from 'react'
import { DocStore } from '../doc-store'
import { Transport, type TransportOptions } from '../transport'
import { FileTree } from '../file-tree/FileTree.tsx'
import { Viewport } from '../viewport/Viewport.ts'
import { ViewportHost } from '../viewport/ViewportHost.tsx'
import { SettingsPanel } from '../settings/SettingsPanel.tsx'
import { ActivityBar } from './ActivityBar.tsx'
import { StatusBar, type ConnectionState } from './StatusBar.tsx'
import './app.css'

const SIDEBAR_MIN = 160
const SIDEBAR_MAX = 480

// When served over HTTPS (behind Caddy at /touch), connect to the WS via a
// relative path (wss://<host>/touch/ws) so the reverse proxy handles it.
// On the localhost dev server, fall back to the default ws://localhost:8765.
function transportOpts(): TransportOptions {
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    const base = window.location.pathname.replace(/\/+$/, '')
    return { path: `${base}/ws` }
  }
  return {}
}

export function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarWidth, setSidebarWidth] = useState(240)
  const [connection, setConnection] = useState<ConnectionState>('connecting')
  const viewportRef = useRef<HTMLDivElement>(null)

  // Engine wiring: transport -> doc-store -> viewport, plus the live
  // connection indicator. Mounted once; torn down on unmount.
  useEffect(() => {
    const container = viewportRef.current
    if (!container) return

    const viewport = new Viewport()
    viewport.mount(container)
    const store = new DocStore()
    const transport = new Transport(transportOpts())

    const offs = [
      transport.on('mesh', (m) => store.applyMesh(m)),
      store.subscribe((s) => {
        if (s.mesh) viewport.setMesh(s.mesh)
      }),
      transport.on('open', () => setConnection('connected')),
      transport.on('ready', () => setConnection('connected')),
      transport.on('close', () => setConnection('disconnected')),
      transport.on('socketError', () => setConnection('disconnected')),
    ]
    transport.connect()

    return () => {
      for (const off of offs) off()
      transport.close()
      viewport.dispose()
    }
  }, [])

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
          <ViewportHost containerRef={viewportRef} />
        </main>
      </div>

      <StatusBar connection={connection} />

      {settingsOpen && <SettingsPanel onClose={() => setSettingsOpen(false)} />}
    </div>
  )
}
