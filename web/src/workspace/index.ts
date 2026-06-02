// web/workspace — the FE owner of the opened workspace (ADR-0010): the root,
// a lazily-loaded folder tree (per-directory, expand-on-demand), and the active
// part. File I/O is the backend's — this store just sends commands over the WS
// and mirrors the `dir` listings it gets back. Multi-doc-ready (active path is
// a single id today; editor tabs in T4b).
import type { DirEntry, MsgDir } from '../protocol-types'
import type { Transport } from '../transport'

export class Workspace {
  private root: string | null = null
  private active: string | null = null
  /** dir listings keyed by workspace-relative path ("" = root). */
  private readonly dirs = new Map<string, DirEntry[]>()
  private readonly expanded = new Set<string>()
  private readonly listeners = new Set<() => void>()

  constructor(private readonly transport: Transport) {}

  // --- commands (FE → BE over the WS) ---------------------------------

  openFolder(path: string): void {
    this.root = path
    this.dirs.clear()
    this.expanded.clear()
    this.transport.send({ type: 'openFolder', path })
  }

  listDir(path: string): void {
    this.transport.send({ type: 'listDir', path })
  }

  openPart(path: string): void {
    this.active = path
    this.transport.send({ type: 'openPart', path })
    this.notify()
  }

  newPart(path: string): void {
    this.active = path
    this.transport.send({ type: 'newPart', path })
    this.notify()
  }

  savePart(path: string): void {
    this.active = path
    this.transport.send({ type: 'savePart', path })
    this.notify()
  }

  rename(path: string, toPath: string): void {
    this.transport.send({ type: 'renamePart', path, to_path: toPath })
  }

  remove(path: string): void {
    this.transport.send({ type: 'removePart', path })
  }

  // --- state (mirrors backend `dir` listings) -------------------------

  /** Apply a backend directory listing. */
  applyDir(msg: MsgDir): void {
    this.dirs.set(msg.path, msg.entries)
    this.notify()
  }

  isOpen(): boolean {
    return this.root !== null
  }

  rootPath(): string | null {
    return this.root
  }

  activePath(): string | null {
    return this.active
  }

  entries(dirPath: string): DirEntry[] | undefined {
    return this.dirs.get(dirPath)
  }

  isExpanded(dirPath: string): boolean {
    return this.expanded.has(dirPath)
  }

  /** Expand/collapse a folder; lazily fetch its listing on first expand. */
  toggle(dirPath: string): void {
    if (this.expanded.has(dirPath)) {
      this.expanded.delete(dirPath)
    } else {
      this.expanded.add(dirPath)
      if (!this.dirs.has(dirPath)) this.listDir(dirPath)
    }
    this.notify()
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notify(): void {
    for (const listener of this.listeners) listener()
  }
}

/** Join a workspace-relative dir path with a child name. */
export function childPath(dirPath: string, name: string): string {
  return dirPath ? `${dirPath}/${name}` : name
}
