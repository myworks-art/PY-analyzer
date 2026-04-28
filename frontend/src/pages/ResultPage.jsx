import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getResult } from '../api'
import IssueList from '../components/IssueList'

const fmt = iso => new Date(iso).toLocaleString('ru-RU', {
  day:'2-digit', month:'2-digit', year:'numeric',
  hour:'2-digit', minute:'2-digit', second:'2-digit',
})

export default function ResultPage() {
  const { id } = useParams()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getResult(id).then(setResult).catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div className="main">
      <div className="empty"><div className="spinner" style={{ margin: '0 auto' }} /></div>
    </div>
  )
  if (error) return <div className="main"><div className="err-box fade">{error}</div></div>
  if (!result) return null

  function exportJson() {
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })),
      download: `analysis-${result.id}.json`,
    })
    a.click()
  }

  return (
    <div className="main">
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:'2rem', flexWrap:'wrap', gap:'1rem' }}>
        <div>
          <div style={{ marginBottom:'0.5rem' }}>
            <Link to="/history" style={{ fontFamily:'var(--mono)', fontSize:11, color:'var(--text-3)' }}>
              &lt; История
            </Link>
          </div>
          <div className="ph-title" style={{ marginBottom:'0.25rem' }}>{result.filename}</div>
          <div className="ph-sub">ID: {result.id} · {fmt(result.created_at)}</div>
        </div>
        <div className="row">
          <button className="btn btn-ghost btn-sm" onClick={exportJson}>Экспорт JSON</button>
          <Link to="/upload" className="btn btn-primary btn-sm">Новый анализ</Link>
        </div>
      </div>

      <div className="card fade">
        {result.summary.total === 0
          ? <div className="empty">Проблем не найдено</div>
          : <IssueList issues={result.issues} summary={result.summary} />
        }
      </div>
    </div>
  )
}
