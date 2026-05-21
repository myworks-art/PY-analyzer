import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import NavMenu from './NavMenu.jsx'
import { getHealth } from '../api.js'

const TITLES = {
  '/': 'Главная', '/upload': 'Загрузить файл',
  '/history': 'История', '/docs': 'Документация', '/help': 'Помощь',
}

export default function Topbar() {
  const loc = useLocation()
  const [health, setHealth] = useState(null)

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null))
  }, [])

  return (
    <header className="topbar">
      <NavMenu />
      {TITLES[loc.pathname] && (
        <span className="topbar-title">/ {TITLES[loc.pathname]}</span>
      )}
      <div className="topbar-right">
        <div className="api-status">
          <div className={`dot ${health ? '' : 'off'}`} />
          {health ? `api · ${health.rules_loaded} rules` : 'api · offline'}
        </div>
      </div>
    </header>
  )
}
 