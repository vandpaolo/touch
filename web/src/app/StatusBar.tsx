// web/app — bottom status bar. The connection indicator is driven live by the
// transport (via app state); cost + latency join it in later phases.
import { isElectron } from '../platform'

export type ConnectionState = 'connecting' | 'connected' | 'disconnected'

const LABEL: Record<ConnectionState, string> = {
  connecting: 'Connecting…',
  connected: 'Connected',
  disconnected: 'Disconnected',
}

export function StatusBar({
  connection,
  busy = false,
}: {
  connection: ConnectionState
  busy?: boolean
}) {
  return (
    <footer className="statusbar" aria-label="Status bar">
      {busy && (
        <span className="statusbar-item statusbar-busy" data-testid="status-busy">
          ⏳ working…
        </span>
      )}
      <span className="statusbar-item" data-testid="status-connection">
        <span className={`status-dot ${connection}`} aria-hidden="true">
          ●
        </span>
        {LABEL[connection]}
      </span>
      <span className="statusbar-item" data-testid="status-mode">
        {isElectron() ? 'Electron' : 'browser-dev'}
      </span>
    </footer>
  )
}
