import { useState } from 'react'

const SEV = { error: 'err', warning: 'warn', info: 'info' }
const SEV_LBL = { error: 'ERROR', warning: 'WARN', info: 'INFO' }
const CAT = { security: 'SEC', performance: 'PERF', reliability: 'REL', best_practices: 'BP' }
const CATS = ['all', 'security', 'performance', 'reliability', 'best_practices']
const CAT_NAMES = { all: 'Все', security: 'SEC', performance: 'PERF', reliability: 'REL', best_practices: 'BP' }

function Issue({ issue }) {
  const cls = SEV[issue.severity] || 'info'
  return (
    <div className={`issue ${cls}`}>
      <div className={`sev-badge ${cls}`}>{SEV_LBL[issue.severity]}</div>
      <div>
        <div className="issue-meta">
          <span className="rule-id">{issue.rule_id}</span>
          {issue.job_name && <span className="job">{issue.job_name}</span>}
          <span>{CAT[issue.category] || issue.category}</span>
        </div>
        <div className="issue-msg">{issue.message}</div>
        {issue.location && (
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-3)', marginTop: '.2rem' }}>
            {issue.location}
          </div>
        )}
      </div>
      <div className="issue-loc">
        {issue.line > 0 ? `L${issue.line}` : ''}
      </div>
    </div>
  )
}

export default function IssueList({ issues, summary }) {
  const [sev, setSev] = useState('all')
  const [cat, setCat] = useState('all')

  const filtered = issues.filter(i => {
    if (sev !== 'all' && i.severity !== sev) return false
    if (cat !== 'all' && i.category !== cat) return false
    return true
  })

  return (
    <div className="fade">
      <div className="summary-row">
        {[
          { key: 'all',     cls: 's-all',  label: 'Всего',          count: summary.total },
          { key: 'error',   cls: 's-err',  label: 'Ошибки',         count: summary.error },
          { key: 'warning', cls: 's-warn', label: 'Предупреждения', count: summary.warning },
          { key: 'info',    cls: 's-info', label: 'Замечания',      count: summary.info },
        ].map(s => (
          <button key={s.key}
            className={`s-chip ${s.cls} ${sev === s.key ? 'selected' : ''}`}
            onClick={() => setSev(p => p === s.key && s.key !== 'all' ? 'all' : s.key)}
          >
            {s.label} <strong>{s.count}</strong>
          </button>
        ))}
      </div>
      <div className="cat-row">
        {CATS.map(c => (
          <button key={c}
            className={`cat-chip ${cat === c ? 'active' : ''}`}
            onClick={() => setCat(p => p === c && c !== 'all' ? 'all' : c)}
          >
            {CAT_NAMES[c]}
          </button>
        ))}
      </div>
      {filtered.length === 0
        ? <div className="empty">Нет проблем по выбранным фильтрам</div>
        : <div className="issue-list">{filtered.map((iss, i) => <Issue key={i} issue={iss} />)}</div>
      }
    </div>
  )
}
 