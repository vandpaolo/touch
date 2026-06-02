// web/platform — capability shim (N5). The single seam where native surfaces
// diverge between the Electron renderer (prod) and a plain browser tab (dev).
// This is the ONLY module permitted to touch window.electron / the preload
// bridge (dependency rule, 02-classes.md). Every other module stays mode-blind.

// The preload surface we expect Electron's shell/preload to expose later.
interface ElectronBridge {
  openFile(): Promise<{ path: string; contents: string } | null>
  saveFile(path: string, contents: string): Promise<void>
  keychain: {
    get(account: string): Promise<string | null>
    set(account: string, secret: string): Promise<void>
    clear(account: string): Promise<void>
  }
}

declare global {
  interface Window {
    electron?: ElectronBridge
  }
}

function bridge(): ElectronBridge | undefined {
  return typeof window !== 'undefined' ? window.electron : undefined
}

/** True when running as the Electron renderer; false in a browser-dev tab. */
export function isElectron(): boolean {
  return bridge() !== undefined
}

/**
 * Pick a workspace folder (ADR-0010). The backend owns the filesystem, so this
 * only resolves *which* folder. Electron's native open-directory dialog lands
 * later; for now browser-dev asks for a path on the sidecar host.
 */
export function pickFolder(): string | null {
  if (typeof window === 'undefined') return null
  return window.prompt('Open folder — path on the server:', '/srv/touch')
}

// Native surfaces. Backed by the Electron preload in prod; in browser-dev they
// give a clear, intentional failure rather than silently diverging. The real
// implementations land in their owning phases (keychain T6, file dialogs T9) —
// this stub exists so the seam is in place from day one.
function notWired(surface: string): never {
  throw new Error(
    `platform.${surface} is unavailable in browser-dev mode (Electron-only; wired in a later phase)`,
  )
}

export const platform = {
  isElectron,
  openFile(): Promise<{ path: string; contents: string } | null> {
    return bridge()?.openFile() ?? notWired('openFile')
  },
  saveFile(path: string, contents: string): Promise<void> {
    return bridge()?.saveFile(path, contents) ?? notWired('saveFile')
  },
  keychain: {
    get(account: string): Promise<string | null> {
      return bridge()?.keychain.get(account) ?? notWired('keychain.get')
    },
    set(account: string, secret: string): Promise<void> {
      return bridge()?.keychain.set(account, secret) ?? notWired('keychain.set')
    },
    clear(account: string): Promise<void> {
      return bridge()?.keychain.clear(account) ?? notWired('keychain.clear')
    },
  },
}
