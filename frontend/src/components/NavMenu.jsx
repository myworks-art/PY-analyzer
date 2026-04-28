import { useEffect, useRef, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

const ITEMS = [
  { path: '/',          label: 'Главная',           icon: '~' },
  { divider: true },
  { path: '/upload',    label: 'Загрузить файл',    icon: '>' },
  { path: '/history',   label: 'История проверок',  icon: '#' },
  { divider: true },
  { path: '/docs',      label: 'Документация',       icon: '?' },
  { path: '/help',      label: 'Помощь',             icon: '!' },
]

export default function NavMenu() {
  const [open, setOpen] = useState(false)
  const ref  = useRef(null)
  const nav  = useNavigate()
  const loc  = useLocation()

  useEffect(() => {
    const close = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  function go(path) { nav(path); setOpen(false) }

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button className={`menu-btn ${open ? 'open' : ''}`} onClick={() => setOpen(v => !v)}>
        <div className="hamburger">
          <span /><span /><span />
        </div>
        Меню
      </button>

      {open && (
        <div className="dropdown">
          {ITEMS.map((item, i) =>
            item.divider
              ? <div key={i} className="dropdown-divider" />
              : (
                <button
                  key={item.path}
                  className={`dropdown-item ${loc.pathname === item.path ? 'active' : ''}`}
                  onClick={() => go(item.path)}
                >
                  <span className="dropdown-icon" style={{ fontFamily: 'var(--mono)' }}>
                    {item.icon}
                  </span>
                  {item.label}
                </button>
              )
          )}
        </div>
      )}
    </div>
  )
}
