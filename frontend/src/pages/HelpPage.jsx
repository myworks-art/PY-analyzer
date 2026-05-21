export default function HelpPage() {
  return (
    <div className="main narrow">
      <div className="ph">
        <div className="ph-label">Поддержка</div>
        <div className="ph-title">Помощь</div>
        <div className="ph-sub">Коды ошибок, частые вопросы</div>
      </div>
      <div className="card" style={{ marginBottom:'1rem' }}>
        <div className="card-label">Коды ошибок HTTP</div>
        <div style={{ display:'flex', flexDirection:'column', gap:'.5rem' }}>
          {[
            ['201','Анализ выполнен успешно'],
            ['204','Запись удалена'],
            ['404','Результат не найден'],
            ['413','Файл превышает 512 KB'],
            ['422','Некорректный YAML или пустое тело'],
            ['500','Внутренняя ошибка сервера'],
          ].map(([code, desc]) => (
            <div key={code} style={{ display:'grid', gridTemplateColumns:'48px 1fr', gap:'1rem', alignItems:'center' }}>
              <span style={{ fontFamily:'var(--mono)', fontSize:12, color:'var(--accent-hi)', fontWeight:700 }}>{code}</span>
              <span style={{ fontFamily:'var(--mono)', fontSize:12, color:'var(--text-2)' }}>{desc}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="card" style={{ marginBottom:'1rem' }}>
        <div className="card-label">Логирование</div>
        <div style={{ fontFamily:'var(--mono)', fontSize:12, color:'var(--text-2)', lineHeight:1.8 }}>
          <p style={{ marginBottom:'.75rem' }}>
            Журнал событий пишется в файл <span style={{ color:'var(--accent-hi)' }}>logs/analyzer.log</span> рядом с проектом.
          </p>
          <p>Уровни: DEBUG (в файл) · INFO (в консоль и файл) · WARNING · ERROR</p>
        </div>
      </div>
      <div className="card">
        <div className="card-label">Частые вопросы</div>
        <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
          {[
            ['Почему не анализируются include: из remote URL?', 'Резолвинг внешних include требует сетевых запросов. MVP анализирует только локальный файл. Зафиксировано как LIM-01.'],
            ['Как использовать CLI?', 'python -m analyzer check .gitlab-ci.yml --format sarif — SARIF совместим с GitLab CodeQuality.'],
            ['Где хранится история анализов?', 'В SQLite базе data/analyzer.db. В Docker монтируется как volume — данные сохраняются между перезапусками.'],
          ].map(([q, a], i) => (
            <div key={i}>
              <div style={{ fontSize:13, fontWeight:600, marginBottom:'.3rem' }}>{q}</div>
              <div style={{ fontSize:12, color:'var(--text-2)', fontFamily:'var(--mono)', lineHeight:1.6 }}>{a}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
 