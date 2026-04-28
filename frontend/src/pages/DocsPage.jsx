import { useState } from 'react'

const RULES = [
  // Security
  { id:'SEC001', cat:'security',      sev:'error',   title:'Секрет в переменной окружения',         desc:'Переменная содержит потенциальный секрет в открытом виде (не ссылка $VAR).' },
  { id:'SEC002', cat:'security',      sev:'warning',  title:'Образ с тегом latest',                  desc:'Использование latest нарушает детерминированность сборок.' },
  { id:'SEC003', cat:'security',      sev:'error',   title:'Privileged mode',                        desc:'Контейнер запускается с полным доступом к хост-системе.' },
  { id:'SEC004', cat:'security',      sev:'warning',  title:'Публичные артефакты',                   desc:'Артефакты с public: true доступны без аутентификации.' },
  { id:'SEC005', cat:'security',      sev:'info',    title:'Отсутствует проверка подписи образа',    desc:'Образы из внешних реестров не верифицируются.' },
  { id:'SEC006', cat:'security',      sev:'error',   title:'curl/wget piped to shell',               desc:'Загрузка и немедленное исполнение скрипта без верификации.' },
  // Performance
  { id:'PERF001', cat:'performance',  sev:'warning',  title:'Нет кэша зависимостей',                 desc:'Установка pip/npm/maven без секции cache — зависимости скачиваются заново каждый раз.' },
  { id:'PERF002', cat:'performance',  sev:'info',    title:'Артефакты без expire_in',                desc:'Артефакты без срока жизни хранятся бессрочно.' },
  { id:'PERF003', cat:'performance',  sev:'info',    title:'Избыточный timeout',                     desc:'Таймаут джоба превышает 2 часа.' },
  { id:'PERF004', cat:'performance',  sev:'info',    title:'Нет параллельности (needs/parallel)',    desc:'Независимые джобы не используют needs для параллельного запуска.' },
  { id:'PERF005', cat:'performance',  sev:'warning',  title:'Дублирование before_script',            desc:'Идентичный before_script повторяется в нескольких джобах.' },
  // Reliability
  { id:'REL001', cat:'reliability',   sev:'info',    title:'Нет retry у деплоя',                    desc:'Джоб деплоя не настроен на повтор при случайных сбоях раннера.' },
  { id:'REL002', cat:'reliability',   sev:'warning',  title:'Зависимости без версий',                desc:'Пакеты устанавливаются без фиксации версии.' },
  { id:'REL003', cat:'reliability',   sev:'info',    title:'Отсутствует секция stages',             desc:'Порядок выполнения стадий не объявлен явно.' },
  { id:'REL004', cat:'reliability',   sev:'warning',  title:'Отсутствует стадия test',              desc:'Пайплайн не содержит стадии тестирования.' },
  { id:'REL005', cat:'reliability',   sev:'warning',  title:'Деплой без ограничений на ветку',      desc:'Джоб деплоя в прод запускается при любом пуше.' },
  // Best practices
  { id:'BP001', cat:'best_practices', sev:'info',    title:'Нет поля description у джоба',          desc:'Отсутствует описание джоба.' },
  { id:'BP002', cat:'best_practices', sev:'info',    title:'Смешанный стиль именования',            desc:'Имена джобов используют разные стили (kebab-case и snake_case).' },
  { id:'BP003', cat:'best_practices', sev:'info',    title:'Нет секции environment',                desc:'Джоб деплоя не объявляет environment.' },
  { id:'BP004', cat:'best_practices', sev:'warning',  title:'Дублирование конфигурации',            desc:'Несколько джобов содержат идентичные блоки конфигурации.' },
  { id:'BP005', cat:'best_practices', sev:'warning',  title:'Отсутствует секция stages',            desc:'Явное объявление stages улучшает читаемость пайплайна.' },
]

const CATS = [
  { key: 'all',           label: 'Все правила' },
  { key: 'security',      label: 'Безопасность' },
  { key: 'performance',   label: 'Производительность' },
  { key: 'reliability',   label: 'Надёжность' },
  { key: 'best_practices',label: 'Best Practices' },
]

const SEV_CLS = { error: 'err', warning: 'warn', info: 'info' }
const SEV_LBL = { error: 'ERROR', warning: 'WARN', info: 'INFO' }

export default function DocsPage() {
  const [cat, setCat] = useState('all')

  const filtered = cat === 'all' ? RULES : RULES.filter(r => r.cat === cat)

  return (
    <div className="main wide">
      <div className="ph">
        <div className="ph-label">Справочник</div>
        <div className="ph-title">Документация</div>
        <div className="ph-sub">{RULES.length} правил · Swagger API: <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-hi)' }}>localhost:8000/docs</a></div>
      </div>

      <div className="docs-grid">
        {/* Sidebar nav */}
        <nav className="docs-nav">
          <div className="docs-nav-section">Категории</div>
          {CATS.map(c => (
            <button
              key={c.key}
              className={`docs-nav-item ${cat === c.key ? 'active' : ''}`}
              onClick={() => setCat(c.key)}
            >
              {c.label}
              <span style={{ marginLeft: '0.4rem', fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-3)' }}>
                ({c.key === 'all' ? RULES.length : RULES.filter(r => r.cat === c.key).length})
              </span>
            </button>
          ))}

          <div className="docs-nav-section" style={{ marginTop: '0.5rem' }}>API</div>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="docs-nav-item">
            Swagger UI
          </a>
          <a href="http://localhost:8000/redoc" target="_blank" rel="noreferrer" className="docs-nav-item">
            ReDoc
          </a>
        </nav>

        {/* Rules */}
        <div className="fade">
          {filtered.map(rule => (
            <div key={rule.id} className="rule-card">
              <div className="rule-header">
                <span className="rule-id-badge">{rule.id}</span>
                <span className={`sev-badge ${SEV_CLS[rule.sev]}`} style={{ fontSize: 9 }}>
                  {SEV_LBL[rule.sev]}
                </span>
                <span className="rule-title">{rule.title}</span>
              </div>
              <div className="rule-desc">{rule.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
