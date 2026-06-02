// web/app — top menu bar (F34): lightweight click-to-open dropdowns
// (File / Edit / …). Hover switches between open menus; click-outside closes.
import { useEffect, useRef, useState } from 'react'

export interface MenuItem {
  label: string
  onClick: () => void
  disabled?: boolean
  shortcut?: string
}

export interface MenuSpec {
  label: string
  items: MenuItem[]
}

export function MenuBar({ menus }: { menus: MenuSpec[] }) {
  const [open, setOpen] = useState<string | null>(null)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(null)
    }
    window.addEventListener('mousedown', onDown)
    return () => window.removeEventListener('mousedown', onDown)
  }, [])

  return (
    <div className="menubar-menus" ref={ref} aria-label="Main menu">
      {menus.map((menu) => (
        <div className="menu" key={menu.label}>
          <button
            type="button"
            className={`menubar-item ${open === menu.label ? 'active' : ''}`}
            onClick={() => setOpen(open === menu.label ? null : menu.label)}
            onMouseEnter={() => open && setOpen(menu.label)}
          >
            {menu.label}
          </button>
          {open === menu.label && (
            <div className="menu-dropdown" role="menu">
              {menu.items.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  className="menu-entry"
                  role="menuitem"
                  disabled={item.disabled}
                  onClick={() => {
                    setOpen(null)
                    item.onClick()
                  }}
                >
                  <span>{item.label}</span>
                  {item.shortcut && <span className="menu-shortcut">{item.shortcut}</span>}
                </button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
