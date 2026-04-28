import { useEffect, useState } from 'react'
import { getHealth } from '../api'

export default function Topbar() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null))
  }, [])

  return (
    <header className="topbar">
      <div className="api-status">
        <div className={`dot ${health ? '' : 'off'}`} />
        {health ? `api · ${health.rules_loaded} rules loaded` : 'api · offline'}
      </div>
    </header>
  )
}
