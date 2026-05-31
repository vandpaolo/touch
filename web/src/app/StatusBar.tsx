// web/app — bottom status bar, VS-Code-style shell chrome. The connection
// indicator is a placeholder until web/transport lands (Day 4), which will
// drive it connected/disconnected; cost + latency join it in later phases.
import { isElectron } from '../platform'

export function StatusBar() {
  return (
    <footer className="statusbar" aria-label="Status bar">
      <span className="statusbar-item" data-testid="status-connection">
        <span className="status-dot disconnected" aria-hidden="true">
          ●
        </span>
        Disconnected
      </span>
      <span className="statusbar-item" data-testid="status-mode">
        {isElectron() ? 'Electron' : 'browser-dev'}
      </span>
    </footer>
  )
}
