import { NavLink } from 'react-router-dom'

const ITEMS = [
  { path: '/',        label: 'Главная',          icon: '~', end: true },
  { divider: true },
  { path: '/upload',  label: 'Загрузить файл',   icon: '>' },
  { path: '/history', label: 'История проверок', icon: '#' },
  { divider: true },
  { path: '/docs',    label: 'Документация',      icon: '?' },
  { path: '/help',    label: 'Помощь',            icon: '!' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">[cicd/analyzer]</div>
        <div className="logo-sub">pipeline linter</div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">Навигация</div>
        {ITEMS.map((item, i) =>
          item.divider
            ? <div key={i} className="nav-divider" />
            : (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.end}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
              </NavLink>
            )
        )}
      </nav>

      <div className="sidebar-footer">
        <div style={{ fontSize: 10, letterSpacing: '0.08em', color: 'var(--text-3)' }}>v0.1.0</div>
      </div>
    </aside>
  )
}
