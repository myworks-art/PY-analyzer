import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getHistory, deleteResult } from '../api'

const fmt = iso => new Date(iso).toLocaleString('ru-RU', {
  day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit'
})

export default function HistoryPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(null)

  useEffect(() => {
    getHistory(50).then(setItems).catch(() => {}).finally(() => setLoading(false))
  }, [])

  async function del(e, id) {
    e.preventDefault(); e.stopPropagation()
    if (!confirm('Удалить запись?')) return
    setDeleting(id)
    try { await deleteResult(id); setItems(p => p.filter(i => i.id !== id)) } catch {}
    setDeleting(null)
  }

  return (
    <div className="main">
      <div className="ph">
        <div className="ph-label">Журнал</div>
        <div className="ph-title">История проверок</div>
        <div className="ph-sub">{items.length} записей</div>
      </div>

      {loading && <div className="empty"><div className="spinner" style={{ margin: '0 auto' }} /></div>}

      {!loading && items.length === 0 && (
        <div className="empty">История пуста — запустите первый анализ</div>
      )}

      {!loading && items.length > 0 && (
        <div className="hist-list">
          {items.map(item => (
            <Link key={item.id} to={`/result/${item.id}`} className="hist-item">
              <div>
                <div className="hist-name">{item.filename}</div>
                <div className="hist-date">{fmt(item.created_at)}</div>
              </div>
              <div className="hist-badges">
                {item.summary.error   > 0 && <span className="hb e">{item.summary.error} ERR</span>}
                {item.summary.warning > 0 && <span className="hb w">{item.summary.warning} WARN</span>}
                {item.summary.info    > 0 && <span className="hb i">{item.summary.info} INFO</span>}
                {item.summary.total  === 0 && <span className="hb ok">OK</span>}
              </div>
              <button
                className="btn btn-ghost btn-sm"
                style={{ opacity: 0.45 }}
                onClick={e => del(e, item.id)}
                disabled={deleting === item.id}
              >
                {deleting === item.id ? <div className="spinner" style={{ width:12, height:12 }} /> : 'x'}
              </button>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
