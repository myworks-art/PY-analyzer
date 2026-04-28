import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeText, analyzeFile } from '../api'
import IssueList from '../components/IssueList'

const EXAMPLE = `# Пример с проблемами
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
  const [tab, setTab]         = useState('file')
  const [yamlText, setYaml]   = useState('')
  const [filename, setFn]     = useState('.gitlab-ci.yml')
  const [dragOver, setDrag]   = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState(null)
  const fileRef = useRef(null)
  const nav = useNavigate()

  async function runText() {
    if (!yamlText.trim()) return
    setLoading(true); setError(null); setResult(null)
    try { setResult(await analyzeText(yamlText, filename)) }
    catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  async function runFile(file) {
    if (!file) return
    setFn(file.name); setLoading(true); setError(null); setResult(null)
    try {
      const [data, text] = await Promise.all([analyzeFile(file), file.text()])
      setResult(data); setYaml(text); setTab('file')
    }
    catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="main">
      <div className="ph">
        <div className="ph-label">Анализ</div>
        <div className="ph-title">Загрузить файл</div>
        <div className="ph-sub">Поддерживается .yml / .yaml до 512 KB</div>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="tabs">
          <button className={`tab-btn ${tab === 'file' ? 'active' : ''}`} onClick={() => setTab('file')}>
            Файл с диска
          </button>
          <button className={`tab-btn ${tab === 'paste' ? 'active' : ''}`} onClick={() => setTab('paste')}>
            Вставить текст
          </button>
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
              <input
                ref={fileRef} type="file" accept=".yml,.yaml"
                style={{ display: 'none' }}
                onChange={e => runFile(e.target.files[0])}
              />
              <div className="uz-icon">[  ]</div>
              <div className="uz-title">Перетащить файл или кликнуть для выбора</div>
              <div className="uz-sub">.gitlab-ci.yml · .yml · .yaml</div>
            </div>
            {loading && (
              <div className="row" style={{ marginTop: '1rem', justifyContent: 'center' }}>
                <div className="spinner" /> <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text-2)' }}>Анализ...</span>
              </div>
            )}
          </>
        )}

        {tab === 'paste' && (
          <>
            <div className="row" style={{ marginBottom: '0.75rem' }}>
              <input
                className="input-sm"
                style={{ width: 200 }}
                value={filename}
                onChange={e => setFn(e.target.value)}
                placeholder="Имя файла"
              />
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => { setYaml(EXAMPLE); setFn('example.gitlab-ci.yml'); setResult(null) }}
              >
                Загрузить пример
              </button>
            </div>
            <textarea
              className="yaml-ta"
              placeholder="Вставьте содержимое .gitlab-ci.yml..."
              value={yamlText}
              onChange={e => setYaml(e.target.value)}
            />
            <div className="row" style={{ marginTop: '0.75rem' }}>
              <button
                className="btn btn-primary"
                onClick={runText}
                disabled={loading || !yamlText.trim()}
              >
                {loading ? <><div className="spinner" /> Анализ...</> : 'Запустить анализ'}
              </button>
              {(yamlText || result) && (
                <button className="btn btn-ghost btn-sm" onClick={() => { setYaml(''); setResult(null); setError(null) }}>
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
            : <IssueList issues={result.issues} summary={result.summary} />
          }
        </div>
      )}
    </div>
  )
}
