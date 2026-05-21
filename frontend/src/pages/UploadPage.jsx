import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeText, analyzeFile } from '../api.js'
import IssueList from '../components/IssueList.jsx'

const EXAMPLE = `# Пример с проблемами — для тестирования анализатора
image: python:latest

variables:
  DB_PASSWORD: "supersecret123"

stages:
  - build
  - deploy

build-app:
  stage: build
  script:
    - pip install -r requirements.txt
  artifacts:
    paths: [dist/]

deploy-Production:
  stage: deploy
  script:
    - curl https://example.com/deploy.sh | bash
`

export default function UploadPage() {
  const [tab, setTab]       = useState('file')
  const [yaml, setYaml]     = useState('')
  const [fn, setFn]         = useState('.gitlab-ci.yml')
  const [dragOver, setDrag] = useState(false)
  const [loading, setLoad]  = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError]   = useState(null)
  const fileRef = useRef(null)
  const nav = useNavigate()

  async function runText() {
    if (!yaml.trim()) return
    setLoad(true); setError(null); setResult(null)
    try { setResult(await analyzeText(yaml, fn)) }
    catch (e) { setError(e.message) }
    finally { setLoad(false) }
  }

  async function runFile(file) {
    if (!file) return
    setFn(file.name); setLoad(true); setError(null); setResult(null)
    try {
      const [data, text] = await Promise.all([analyzeFile(file), file.text()])
      setResult(data); setYaml(text); setTab('paste')
    }
    catch (e) { setError(e.message) }
    finally { setLoad(false) }
  }

  return (
    <div className="main">
      <div className="ph">
        <div className="ph-label">Анализ</div>
        <div className="ph-title">Загрузить файл</div>
        <div className="ph-sub">.yml / .yaml · до 512 KB</div>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="tabs">
          <button className={`tab-btn ${tab === 'file' ? 'active' : ''}`} onClick={() => setTab('file')}>Файл с диска</button>
          <button className={`tab-btn ${tab === 'paste' ? 'active' : ''}`} onClick={() => setTab('paste')}>Вставить текст</button>
        </div>

        {tab === 'file' && (
          <>
            <div
              className={`upload-zone ${dragOver ? 'over' : ''}`}
              onDragOver={e => { e.preventDefault(); setDrag(true) }}
              onDragLeave={() => setDrag(false)}
              onDrop={e => { e.preventDefault(); setDrag(false); runFile(e.dataTransfer.files[0]) }}
              onClick={() => fileRef.current?.click()}
            >
              <input ref={fileRef} type="file" accept=".yml,.yaml" style={{ display: 'none' }}
                onChange={e => runFile(e.target.files[0])} />
              <div className="uz-icon">[__]</div>
              <div className="uz-title">Перетащить файл или кликнуть для выбора</div>
              <div className="uz-sub">.gitlab-ci.yml · .yml · .yaml</div>
            </div>
            {loading && (
              <div className="row" style={{ marginTop: '1rem', justifyContent: 'center' }}>
                <div className="spinner" />
                <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text-2)' }}>Анализ...</span>
              </div>
            )}
          </>
        )}

        {tab === 'paste' && (
          <>
            <div className="row" style={{ marginBottom: '.75rem' }}>
              <input className="input-sm" style={{ width: 200 }} value={fn}
                onChange={e => setFn(e.target.value)} placeholder="Имя файла" />
              <button className="btn btn-ghost btn-sm"
                onClick={() => { setYaml(EXAMPLE); setFn('example.gitlab-ci.yml'); setResult(null) }}>
                Загрузить пример
              </button>
            </div>
            <textarea className="yaml-ta" placeholder="Вставьте .gitlab-ci.yml..."
              value={yaml} onChange={e => setYaml(e.target.value)} />
            <div className="row" style={{ marginTop: '.75rem' }}>
              <button className="btn btn-primary" onClick={runText} disabled={loading || !yaml.trim()}>
                {loading ? <><div className="spinner" /> Анализ...</> : 'Запустить анализ'}
              </button>
              {(yaml || result) && (
                <button className="btn btn-ghost btn-sm"
                  onClick={() => { setYaml(''); setResult(null); setError(null) }}>
                  Очистить
                </button>
              )}
            </div>
          </>
        )}
      </div>

      {error && <div className="err-box fade" style={{ marginBottom: '1rem' }}>{error}</div>}

      {result && (
        <div className="card fade">
          <div className="card-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Результат — {result.filename}</span>
            <button className="btn btn-ghost btn-sm" onClick={() => nav(`/result/${result.id}`)}>
              Открыть полный отчёт
            </button>
          </div>
          {result.summary.total === 0
            ? <div className="empty">Проблем не найдено</div>
            : <IssueList issues={result.issues} summary={result.summary} />}
        </div>
      )}
    </div>
  )
}
