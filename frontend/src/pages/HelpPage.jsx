export default function HelpPage() {
  return (
    <div className="main narrow">
      <div className="ph">
        <div className="ph-label">Поддержка</div>
        <div className="ph-title">Помощь</div>
        <div className="ph-sub">Коды ошибок, логирование, частые вопросы</div>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="card-label">Коды ошибок HTTP</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {[
            { code: '201', desc: 'Анализ выполнен успешно' },
            { code: '204', desc: 'Запись удалена' },
            { code: '404', desc: 'Результат анализа не найден' },
            { code: '413', desc: 'Файл превышает максимальный размер (512 KB)' },
            { code: '422', desc: 'Некорректный YAML — не удалось разобрать файл' },
          ].map(e => (
            <div key={e.code} style={{ display: 'grid', gridTemplateColumns: '48px 1fr', gap: '1rem', alignItems: 'center' }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--accent-hi)', fontWeight: 700 }}>
                {e.code}
              </span>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text-2)' }}>{e.desc}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="card-label">Логирование</div>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text-2)', lineHeight: 1.8 }}>
          <p style={{ marginBottom: '0.75rem' }}>Раздел в разработке. Здесь будет отображаться журнал событий анализатора.</p>
          <div style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 'var(--r)', padding: '1rem', color: 'var(--text-3)' }}>
            — журнал пуст —
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-label">Частые вопросы</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {[
            {
              q: 'Почему анализатор не проверяет include: из remote URL?',
              a: 'Резолвинг внешних include требует сетевых запросов и значительно усложняет парсер. MVP анализирует только локальный файл.',
            },
            {
              q: 'Как использовать анализатор в CI пайплайне?',
              a: 'Доступен CLI: python -m analyzer check .gitlab-ci.yml --format sarif. SARIF-вывод совместим с GitLab CodeQuality.',
            },
            {
              q: 'Что означает "Нет кэша зависимостей"?',
              a: 'Анализатор обнаружил команду установки пакетов (pip install, npm install и др.) без секции cache. Это замедляет каждый запуск пайплайна.',
            },
          ].map((faq, i) => (
            <div key={i}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: '0.3rem' }}>{faq.q}</div>
              <div style={{ fontSize: 12, color: 'var(--text-2)', fontFamily: 'var(--mono)', lineHeight: 1.6 }}>{faq.a}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
