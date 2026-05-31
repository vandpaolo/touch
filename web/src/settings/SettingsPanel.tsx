// web/settings — placeholder (Day 2). Provider-mode picker + credential
// capture land in T6; keychain access goes through web/platform.
import { isElectron } from '../platform'

export function SettingsPanel({ onClose }: { onClose: () => void }) {
  return (
    <div
      className="settings-overlay"
      role="dialog"
      aria-label="Settings"
      aria-modal="true"
      data-testid="settings-panel"
      onClick={onClose}
    >
      <div className="settings-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <span>Settings</span>
          <button className="settings-close" onClick={onClose} aria-label="Close settings">
            ×
          </button>
        </div>
        <div className="settings-body">
          <p>Provider mode and credentials land in T6.</p>
          <p className="settings-mode">
            Run mode: <strong>{isElectron() ? 'Electron' : 'browser-dev'}</strong>
          </p>
        </div>
      </div>
    </div>
  )
}
