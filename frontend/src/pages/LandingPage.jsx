import { useNavigate } from 'react-router-dom'

const FEATURES = [
  { id: 'SEC', title: 'Безопасность', desc: 'Секреты в переменных, небезопасные образы, privileged mode, curl|bash' },
  { id: 'PERF', title: 'Производительность', desc: 'Нет кэша зависимостей, артефакты без expire_in, дублирование before_script' },
  { id: 'REL', title: 'Надёжность', desc: 'Нет стадии test, деплой без условий, зависимости без версий' },
  { id: 'BP', title: 'Best Practices', desc: 'Именование джобов, объявление stages, environment' },
]

export default function LandingPage() {
  const nav = useNavigate()
  return (
    <div className="main">
      <div className="hero">
        <div className="hero-label">CI/CD Pipeline Analyzer</div>
        <h1 className="hero-title">Статический анализ<br /><em>.gitlab-ci.yml</em></h1>
        <p className="hero-desc">
          Проверяет конфигурацию GitLab CI на проблемы безопасности,
          производительности и соответствие best practices.
          Работает локально — без отправки кода в сеть.
        </p>
        <div className="hero-actions">
          <button className="btn btn-primary" onClick={() => nav('/upload')}>Загрузить файл</button>
          <button className="btn btn-ghost" onClick={() => nav('/docs')}>Документация</button>
        </div>
      </div>
      <div className="feature-grid">
        {FEATURES.map(f => (
          <div key={f.id} className="feature-item">
            <div className="fi-id">{f.id}</div>
            <div className="fi-title">{f.title}</div>
            <div className="fi-desc">{f.desc}</div>
          </div>
        ))}
      </div>
      <div className="card">
        <div className="card-label">Как использовать</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(200px,1fr))', gap: '1.5rem' }}>
          {[
            { n: '01', t: 'Загрузите файл',    d: 'Выберите .gitlab-ci.yml с локального диска или вставьте содержимое' },
            { n: '02', t: 'Запустите анализ',  d: 'Анализатор проверит файл по 21 правилу за секунду' },
            { n: '03', t: 'Изучите отчёт',     d: 'Фильтруйте по категории и уровню, смотрите номера строк' },
            { n: '04', t: 'Устраните проблемы',d: 'Каждая находка содержит описание и номер строки' },
          ].map(s => (
            <div key={s.n}>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-3)', marginBottom: '.4rem' }}>{s.n}</div>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: '.3rem' }}>{s.t}</div>
              <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6 }}>{s.d}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
