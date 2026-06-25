// web/app — the shell (F2). VS-Code-like layout: menu bar (top), activity rail +
// resizable Explorer (folder workspace) + viewport (centre), status bar (bottom).
// Composition root: wires transport <-> doc-store <-> viewport <-> workspace
// (ADR-0010 — backend owns files, FE owns the interaction).
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
import { Workspace } from '../workspace'
import { pickFolder } from '../platform'
import { PromptPanel, buildPlanMessage } from '../prompt/PromptPanel.tsx'
import type { Selection } from '../protocol-types'
import { FileTree } from '../file-tree/FileTree.tsx'
import { Viewport } from '../viewport/Viewport.ts'
import { ViewportHost } from '../viewport/ViewportHost.tsx'
import { SettingsPanel } from '../settings/SettingsPanel.tsx'
import { ActivityBar } from './ActivityBar.tsx'
import { MenuBar, type MenuSpec } from './MenuBar.tsx'
import { StatusBar, type ConnectionState } from './StatusBar.tsx'
import './app.css'

const SIDEBAR_MIN = 160
const SIDEBAR_MAX = 480

// When served over HTTPS (behind Caddy at /touch), connect via a relative WS
// path; on the localhost dev server fall back to ws://localhost:8765.
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
  layers: [],
  revision: 0,
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
  const [ws, setWs] = useState<Workspace | null>(null)
  // Clarification thread (F7): non-empty means the prompt panel is mid-dialogue,
  // so a submit sends a user reply (conversationTurn) rather than a new plan.
  const [thread, setThread] = useState<{ from: 'assistant' | 'user'; text: string }[]>([])

  const viewportRef = useRef<HTMLDivElement>(null)
  const transportRef = useRef<Transport | null>(null)

  // Engine wiring: transport <-> doc-store <-> viewport <-> workspace. Once.
  useEffect(() => {
    const container = viewportRef.current
    if (!container) return

    const viewport = new Viewport()
    viewport.mount(container)
    const store = new DocStore()
    const selection = new SelectionStore()
    const transport = new Transport(transportOpts())
    const workspace = new Workspace(transport)
    transportRef.current = transport
    setWs(workspace)

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
      setThread([]) // a fresh click starts a fresh prompt, not a reply
      setPrompt({ x: screen.x, y: screen.y, selection: sel })
    })

    const offs = [
      transport.on('mesh', (m) => {
        store.applyMesh(m)
        viewport.setMesh(m)
        setBusy(false)
        setThread([]) // op applied — the dialogue (if any) is resolved
        setPrompt(null)
      }),
      transport.on('document', (d) => {
        store.applyDocument(d)
        if (d.layers.length === 0) viewport.clear()
      }),
      // The planner asked a clarifying question (F7): keep the panel open as a
      // chat thread; the user's reply resumes planning.
      transport.on('conversationTurn', (m) => {
        setBusy(false)
        setThread((cur) => [...cur, { from: 'assistant', text: m.turn.text }])
      }),
      transport.on('dir', (d) => workspace.applyDir(d)),
      store.subscribe(setDoc),
      transport.on('error', (e) => {
        setBusy(false)
        setThread([])
        setError(e.message)
      }),
      transport.on('ready', () => setConnection('connected')),
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

  // --- actions -------------------------------------------------------------

  const openFolder = useCallback(() => {
    const path = pickFolder()
    if (path && ws) ws.openFolder(path)
  }, [ws])

  const newPart = useCallback(() => {
    if (!ws?.isOpen()) {
      setError('Open a folder first (File → Open Folder)')
      return
    }
    const raw = window.prompt('New part name:', 'part.touch')
    if (raw) ws.newPart(raw.endsWith('.touch') ? raw : `${raw}.touch`)
  }, [ws])

  const save = useCallback(() => {
    if (!ws?.isOpen()) {
      setError('Open a folder first (File → Open Folder)')
      return
    }
    const active = ws.activePath()
    if (active) {
      ws.savePart(active)
      return
    }
    const raw = window.prompt('Save part as:', 'part.touch')
    if (raw) ws.savePart(raw.endsWith('.touch') ? raw : `${raw}.touch`)
  }, [ws])

  const undo = useCallback(() => transportRef.current?.send({ type: 'undo' }), [])
  const redo = useCallback(() => transportRef.current?.send({ type: 'redo' }), [])

  const addFeature = useCallback(() => {
    setThread([])
    setPrompt({ x: window.innerWidth / 2 - 140, y: window.innerHeight / 2 - 60, selection: null })
  }, [])

  const submitPrompt = (text: string) => {
    const t = transportRef.current
    if (!t) return
    setBusy(true)
    setError(null)
    if (thread.length > 0) {
      // mid-clarification: reply with a user conversation turn (F7).
      t.send({
        type: 'conversationTurn',
        turn: { from: 'user', text, at: new Date().toISOString() },
      })
      setThread((cur) => [...cur, { from: 'user', text }])
    } else {
      t.send(buildPlanMessage(prompt?.selection ?? null, text))
    }
  }

  const cancelPrompt = useCallback(() => {
    setThread([])
    setPrompt(null)
  }, [])

  // Keyboard: undo / redo / save.
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
        save()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [undo, redo, save])

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

  const menus: MenuSpec[] = [
    {
      label: 'File',
      items: [
        { label: 'Open Folder…', onClick: openFolder },
        { label: 'New Part…', onClick: newPart },
        { label: 'Save', onClick: save, shortcut: 'Ctrl+S' },
        { label: 'New feature (prompt)…', onClick: addFeature },
      ],
    },
    {
      label: 'Edit',
      items: [
        { label: 'Undo', onClick: undo, disabled: !doc.canUndo, shortcut: 'Ctrl+Z' },
        { label: 'Redo', onClick: redo, disabled: !doc.canRedo, shortcut: 'Ctrl+Shift+Z' },
      ],
    },
    {
      label: 'View',
      items: [{ label: sidebarOpen ? 'Hide Explorer' : 'Show Explorer', onClick: () => setSidebarOpen((o) => !o) }],
    },
    { label: 'Help', items: [{ label: 'About Touch', onClick: () => window.alert('Touch — AI-native 3D CAD editor (v0)') }] },
  ]

  return (
    <div className="app">
      <header className="menubar">
        <span className="menubar-brand">Touch</span>
        <MenuBar menus={menus} />
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
              {ws && <FileTree ws={ws} onOpen={(p) => ws.openPart(p)} />}
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
          thread={thread}
          onSubmit={submitPrompt}
          onCancel={cancelPrompt}
        />
      )}

      {settingsOpen && <SettingsPanel onClose={() => setSettingsOpen(false)} />}
    </div>
  )
}
