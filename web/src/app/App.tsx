// web/app — the shell (F2). Owns the VS-Code-like layout: menu bar (top),
// activity bar + resizable sidebar (file explorer) + viewport host (centre),
// status bar (bottom). Composition root: wires transport <-> doc-store <->
// viewport and the document lifecycle (open/new/save/undo/redo, T4).
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from 'react'
import { DocStore, type DocState } from '../doc-store'
import { SelectionStore, selectionFromHit } from '../selection'
import { Transport, type TransportOptions } from '../transport'
import { PromptPanel, buildPlanMessage } from '../prompt/PromptPanel.tsx'
import type { Message, Selection } from '../protocol-types'
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
// relative path (wss://<host>/touch/ws). On the localhost dev server, fall
// back to the default ws://localhost:8765.
function transportOpts(): TransportOptions {
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    const base = window.location.pathname.replace(/\/+$/, '')
    return { path: `${base}/ws` }
  }
  return {}
}

const EMPTY_DOC: DocState = {
  mesh: null,
  name: 'untitled',
  history: [],
  dirty: false,
  canUndo: false,
  canRedo: false,
}

export function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarWidth, setSidebarWidth] = useState(240)
  const [connection, setConnection] = useState<ConnectionState>('connecting')
  const [prompt, setPrompt] = useState<{ x: number; y: number; selection: Selection | null } | null>(
    null,
  )
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [doc, setDoc] = useState<DocState>(EMPTY_DOC)
  const [files, setFiles] = useState<string[]>([])

  const viewportRef = useRef<HTMLDivElement>(null)
  const transportRef = useRef<Transport | null>(null)
  const docRef = useRef<DocState>(doc)
  docRef.current = doc

  const send = useCallback((msg: Message) => {
    transportRef.current?.send(msg)
  }, [])

  // Engine wiring: transport <-> doc-store <-> viewport. Mounted once.
  useEffect(() => {
    const container = viewportRef.current
    if (!container) return

    const viewport = new Viewport()
    viewport.mount(container)
    const store = new DocStore()
    const selection = new SelectionStore()
    const transport = new Transport(transportOpts())
    transportRef.current = transport

    viewport.onFaceClick((hit, screen) => {
      if (!hit) {
        selection.clear()
        viewport.setSelectedFace(null)
        setPrompt(null)
        return
      }
      const sel = selectionFromHit(hit, store.getMesh()?.faceIdToFinderHint ?? {})
      selection.set(sel)
      viewport.setSelectedFace(hit.faceTag)
      setPrompt({ x: screen.x, y: screen.y, selection: sel })
    })

    const offs = [
      transport.on('mesh', (m) => {
        store.applyMesh(m)
        viewport.setMesh(m)
        setBusy(false)
        setPrompt(null) // the modification landed — close the prompt
      }),
      transport.on('document', (d) => {
        store.applyDocument(d)
        if (d.history.length === 0) viewport.clear() // new/undone-to-empty
      }),
      transport.on('fileList', (f) => setFiles(f.files)),
      store.subscribe(setDoc),
      transport.on('error', (e) => {
        setBusy(false)
        setError(e.message)
      }),
      transport.on('ready', () => {
        setConnection('connected')
        transport.send({ type: 'listFiles' })
      }),
      transport.on('open', () => setConnection('connected')),
      transport.on('close', () => setConnection('disconnected')),
      transport.on('socketError', () => setConnection('disconnected')),
    ]
    transport.connect()

    return () => {
      for (const off of offs) off()
      transport.close()
      transportRef.current = null
      viewport.dispose()
    }
  }, [])

  // --- document actions ----------------------------------------------------

  const newFile = useCallback(() => send({ type: 'newDoc' }), [send])
  const openFile = useCallback((name: string) => send({ type: 'open', name }), [send])
  const undo = useCallback(() => send({ type: 'undo' }), [send])
  const redo = useCallback(() => send({ type: 'redo' }), [send])
  const saveFile = useCallback(() => {
    const current = docRef.current.name
    const suggested = current && current !== 'untitled' ? current : 'untitled'
    const name = window.prompt('Save as:', suggested)
    if (name) send({ type: 'save', name })
  }, [send])

  const addFeature = useCallback(() => {
    // Prompt with no selection → the planner emits a primary (create-from-scratch).
    setPrompt({ x: window.innerWidth / 2 - 140, y: window.innerHeight / 2 - 60, selection: null })
  }, [])

  const submitPrompt = (text: string) => {
    setBusy(true)
    setError(null)
    send(buildPlanMessage(prompt?.selection ?? null, text))
  }

  // Keyboard: undo / redo / save. Reads the latest state via refs.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return
      const key = e.key.toLowerCase()
      if (key === 'z' && !e.shiftKey) {
        e.preventDefault()
        undo()
      } else if ((key === 'z' && e.shiftKey) || key === 'y') {
        e.preventDefault()
        redo()
      } else if (key === 's') {
        e.preventDefault()
        saveFile()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [undo, redo, saveFile])

  // Drag-to-resize the sidebar.
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
          <button className="menubar-item" type="button" onClick={addFeature}>
            + Feature
          </button>
          <button className="menubar-item" type="button" onClick={undo} disabled={!doc.canUndo}>
            Undo
          </button>
          <button className="menubar-item" type="button" onClick={redo} disabled={!doc.canRedo}>
            Redo
          </button>
          <button className="menubar-item" type="button" onClick={() => setSettingsOpen(true)}>
            Settings
          </button>
        </nav>
        <span className="menubar-doc">
          {doc.name}
          {doc.dirty && (
            <span className="menubar-dirty" title="Unsaved changes">
              ●
            </span>
          )}
        </span>
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
              <FileTree
                files={files}
                activeName={doc.name}
                dirty={doc.dirty}
                onOpen={openFile}
                onNew={newFile}
                onSave={saveFile}
              />
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

      <StatusBar connection={connection} busy={busy} />

      {error && (
        <div className="toast-error" role="alert" onClick={() => setError(null)}>
          {error}
        </div>
      )}

      {prompt && (
        <PromptPanel
          x={prompt.x}
          y={prompt.y}
          busy={busy}
          onSubmit={submitPrompt}
          onCancel={() => setPrompt(null)}
        />
      )}

      {settingsOpen && <SettingsPanel onClose={() => setSettingsOpen(false)} />}
    </div>
  )
}
