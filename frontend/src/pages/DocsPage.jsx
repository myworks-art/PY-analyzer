import { useState } from 'react'

const RULES = [
  { id:'SEC001',cat:'security',     sev:'error',  title:'Секрет в переменной окружения',       desc:'Переменная содержит потенциальный секрет в открытом виде (не ссылка $VAR).' },
  { id:'SEC002',cat:'security',     sev:'warning', title:'Образ с тегом latest',               desc:'Нарушает детерминированность сборок — в разные дни разный образ.' },
  { id:'SEC003',cat:'security',     sev:'error',  title:'Privileged mode',                     desc:'Контейнер получает почти полный доступ к хост-системе.' },
  { id:'SEC004',cat:'security',     sev:'warning', title:'Публичные артефакты',                desc:'public: true делает артефакты доступными без аутентификации.' },
  { id:'SEC005',cat:'security',     sev:'info',   title:'Нет проверки подписи образа',         desc:'Образы из внешних реестров не верифицируются (cosign/notary).' },
  { id:'SEC006',cat:'security',     sev:'error',  title:'curl/wget piped to shell',            desc:'Загрузка и немедленное исполнение без верификации.' },
  { id:'PERF001',cat:'performance', sev:'warning', title:'Нет кэша зависимостей',             desc:'pip/npm/maven устанавливают пакеты заново каждый раз.' },
  { id:'PERF002',cat:'performance', sev:'info',   title:'Артефакты без expire_in',             desc:'Хранятся бессрочно — занимают место.' },
  { id:'PERF003',cat:'performance', sev:'info',   title:'Избыточный timeout (> 2 ч)',          desc:'Зависшие джобы блокируют runner надолго.' },
  { id:'PERF004',cat:'performance', sev:'info',   title:'Нет параллельности (needs/parallel)', desc:'3+ джоба в стадии выполняются последовательно.' },
  { id:'PERF005',cat:'performance', sev:'warning', title:'Дублирование before_script',        desc:'Вынесите в default: или используйте YAML anchors.' },
  { id:'REL001', cat:'reliability', sev:'info',   title:'Нет retry у деплоя',                 desc:'Нет защиты от временных сбоев раннера.' },
  { id:'REL002', cat:'reliability', sev:'warning', title:'Зависимости без версий',            desc:'pip install requests вместо requests==2.31.0.' },
  { id:'REL003', cat:'reliability', sev:'info',   title:'Нет объявления stages',              desc:'Порядок выполнения неочевиден.' },
  { id:'REL004', cat:'reliability', sev:'warning', title:'Нет стадии тестирования',           desc:'CI без тестов теряет основной смысл.' },
  { id:'REL005', cat:'reliability', sev:'warning', title:'Деплой без условий на ветку',       desc:'Запускается при любом пуше.' },
  { id:'BP001',  cat:'best_practices',sev:'info', title:'Нет description у джоба',            desc:'Затрудняет навигацию в GitLab UI.' },
  { id:'BP002',  cat:'best_practices',sev:'info', title:'Смешанный стиль именования',         desc:'Kebab-case и snake_case одновременно.' },
  { id:'BP003',  cat:'best_practices',sev:'info', title:'Нет секции environment',             desc:'Нет трекинга деплоев в GitLab UI.' },
  { id:'BP004',  cat:'best_practices',sev:'warning',title:'Дублирование конфигурации',        desc:'image/services/variables одинаковы в нескольких джобах.' },
  { id:'BP005',  cat:'best_practices',sev:'warning',title:'Нет секции stages',                desc:'Явное объявление улучшает читаемость.' },
]

const CATS = [
  { key:'all',label:'Все правила' },
  { key:'security',label:'Безопасность' },
  { key:'performance',label:'Производительность' },
  { key:'reliability',label:'Надёжность' },
  { key:'best_practices',label:'Best Practices' },
]
const SEV_CLS = { error:'err', warning:'warn', info:'info' }
const SEV_LBL = { error:'ERROR', warning:'WARN', info:'INFO' }

export default function DocsPage() {
  const [cat, setCat] = useState('all')
  const filtered = cat === 'all' ? RULES : RULES.filter(r => r.cat === cat)

  return (
    <div className="main wide">
      <div className="ph">
        <div className="ph-label">Справочник</div>
        <div className="ph-title">Документация</div>
        <div className="ph-sub">{RULES.length} правил · <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" style={{ color:'var(--accent-hi)' }}>Swagger API</a></div>
      </div>
      <div className="docs-grid">
        <nav className="docs-nav">
          <div className="docs-nav-section">Категории</div>
          {CATS.map(c => (
            <button key={c.key} className={`docs-nav-item ${cat === c.key ? 'active' : ''}`} onClick={() => setCat(c.key)}>
              {c.label} <span style={{ marginLeft:'.4rem', fontSize:10, color:'var(--text-3)' }}>({c.key==='all'?RULES.length:RULES.filter(r=>r.cat===c.key).length})</span>
            </button>
          ))}
          <div className="docs-nav-section" style={{ marginTop:'.5rem' }}>API</div>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="docs-nav-item">Swagger UI</a>
          <a href="http://localhost:8000/redoc" target="_blank" rel="noreferrer" className="docs-nav-item">ReDoc</a>
        </nav>
        <div className="fade">
          {filtered.map(rule => (
            <div key={rule.id} className="rule-card">
              <div className="rule-header">
                <span className="rule-id-badge">{rule.id}</span>
                <span className={`sev-badge ${SEV_CLS[rule.sev]}`} style={{ fontSize:9 }}>{SEV_LBL[rule.sev]}</span>
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
