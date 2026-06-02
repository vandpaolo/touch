// web/app — activity rail (F33), VS-Code-style. Explorer toggles the sidebar;
// Search / Source-Control / Extensions are inert stubs reserved for a future
// extensions story; Settings is pinned at the bottom. Codicons for the icons.

function Stub({ icon, label }: { icon: string; label: string }) {
  return (
    <button
      type="button"
      className="activity-item activity-stub"
      title={`${label} — coming soon`}
      aria-label={label}
      disabled
    >
      <i className={`codicon ${icon}`} aria-hidden="true" />
    </button>
  )
}

export function ActivityBar({
  explorerActive,
  onToggleExplorer,
  onOpenSettings,
}: {
  explorerActive: boolean
  onToggleExplorer: () => void
  onOpenSettings: () => void
}) {
  return (
    <div className="activitybar" aria-label="Activity bar">
      <button
        type="button"
        className={`activity-item ${explorerActive ? 'active' : ''}`}
        onClick={onToggleExplorer}
        title="Explorer"
        aria-label="Explorer"
        aria-pressed={explorerActive}
      >
        <i className="codicon codicon-files" aria-hidden="true" />
      </button>
      <Stub icon="codicon-search" label="Search" />
      <Stub icon="codicon-source-control" label="Source Control" />
      <Stub icon="codicon-extensions" label="Extensions" />
      <div className="activity-spacer" />
      <button
        type="button"
        className="activity-item"
        onClick={onOpenSettings}
        title="Settings"
        aria-label="Settings"
      >
        <i className="codicon codicon-settings-gear" aria-hidden="true" />
      </button>
    </div>
  )
}
