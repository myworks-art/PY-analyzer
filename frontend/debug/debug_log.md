# Debug Log — CI/CD Pipeline Analyzer
# Формат: [ДАТА] [УРОВЕНЬ] [КОМПОНЕНТ] Описание
# Этот файл ведётся вручную для сессий отладки.
# Автоматический лог приложения: logs/analyzer.log

---

## Сессия 2024-04 — первичный дебаг после сборки v0.1.0

### Метод: статический анализ кода + проверка поведения паттернов

[2024-04] [BUG] [rules/registry.py]
  `Issue` объявлен под `TYPE_CHECKING` — в runtime блок недоступен.
  В `run_all()` нет прямого использования `Issue` как типа,
  но в случае аннотации `list[Issue]` это вызовет NameError при включённых
  проверках типов или изменении кода. Риск: СРЕДНИЙ.
  → ИСПРАВЛЕНО: убран из TYPE_CHECKING.

[2024-04] [BUG] [rules/security.py · SEC001]
  Паттерн `_SECRET_VALUE_PATTERNS = r"^(?!\$)(?!\s*$).{6,}$"` срабатывает
  на любую строку длиннее 6 символов без $-prefix.
  Пример false positive: `DB_PASSWORD: "production"` → FLAGGED=True.
  Строка "production" не является секретом — это имя окружения.
  → ИСПРАВЛЕНО: добавлен фильтр _BENIGN_VALUES (production, staging, true,
    URL-подобные строки, hostname-подобные строки).
  Минимальная длина изменена с 6 на 8 символов.

[2024-04] [BUG] [rules/security.py · SEC006]
  `script.lc.item(i)` — метод может отсутствовать у CommentedSeq,
  созданных программно (например, в unit-тестах без полного round-trip через YAML).
  `except Exception` был слишком широким — скрывал другие ошибки.
  → ИСПРАВЛЕНО: `except (AttributeError, KeyError, TypeError)`.

[2024-04] [BUG] [api/database.py]
  DATABASE_URL захардкожен как строка прямо в модуле.
  В docker-compose используется volume для БД, но URL нельзя переопределить
  без правки кода.
  → ИСПРАВЛЕНО: `os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./analyzer.db")`.

[2024-04] [WARN] [rules/base.py · Severity.emoji()]
  Метод возвращает Unicode-emoji (❌ ⚠️ ℹ️). В ряде терминалов
  и CI-логах это ломает выравнивание и может вызвать проблемы с кодировкой.
  → ИСПРАВЛЕНО: метод emoji() удалён, __str__ использует текстовый формат.

[2024-04] [INFO] [rules/performance.py · PERF004]
  Правило "нет параллельности (needs/parallel)" задокументировано в docs/rules.md
  но не реализовано в performance.py. Класс отсутствует.
  → СТАТУС: отмечено в LIM-06, запланировано на v0.2.0.

[2024-04] [INFO] [api/database.py]
  Нет Alembic миграций. При добавлении поля `location` в IssueRecord
  существующая БД не обновится. Для MVP достаточно пересоздать таблицы,
  но в production нужен Alembic.
  → СТАТУС: отмечено в LIM-03.

---

## Сессия 2024-04 (раунд 2) — ревью после полного аудита

[2024-04] [BUG] [docker-compose.yml + api/database.py]
  volume монтирует ./data:/app/data, но DATABASE_URL=sqlite+aiosqlite:///./analyzer.db
  указывал на /app/analyzer.db — вне volume. БД терялась при перезапуске контейнера.
  → ИСПРАВЛЕНО: DATABASE_URL=sqlite+aiosqlite:////app/data/analyzer.db

[2024-04] [BUG] [api/main.py CORS]
  ALLOWED_ORIGINS захардкожен: только localhost:3000 и 5173.
  В production или на другом порту запросы падали с CORS-ошибкой.
  → ИСПРАВЛЕНО: читается из переменной окружения ALLOWED_ORIGINS (запятая-разделитель)

[2024-04] [BUG] [analyzer/main.py _output_sarif]
  physicalLocation.artifactLocation не содержал uriBaseId.
  job_name и fix_suggestion не передавались в SARIF results.
  → ИСПРАВЛЕНО: добавлен uriBaseId="%SRCROOT%", properties.jobName, properties.fixSuggestion

[2024-04] [BUG] [rules/ — 4 отсутствующих правила]
  В реестре 17 правил вместо 21 (видно в logs/analyzer.log).
  Отсутствовали: SEC005, PERF004, REL002, BP004.
  → ИСПРАВЛЕНО: все четыре правила реализованы и зарегистрированы.

[2024-04] [INFO] [Dockerfile]
  Образ запускался от root — нарушение security best practices.
  Нет HEALTHCHECK — docker-compose не мог дождаться готовности сервиса.
  → ИСПРАВЛЕНО: multi-stage build, пользователь appuser, HEALTHCHECK добавлен.

[2024-04] [INFO] [pre-commit]
  Отсутствовал .pre-commit-config.yaml — линтинг не запускался автоматически.
  → ДОБАВЛЕНО: ruff + ruff-format + mypy + pre-commit-hooks.

[2024-04] [DECISION] [extends: и include: local]
  Ревью рекомендовал добавить поддержку extends: и include: local.
  РЕШЕНИЕ: отложено до v0.2.0 — для MVP это over-engineering.
  Риск: при добавлении сломается парсер якорей (YAML anchors уже нетривиальны).
  Зафиксировано как LIM-02 в error_codes.md.

[2024-04] [DECISION] [GitHub Actions]
  Ревью рекомендовал добавить CI для проекта (lint + test + docker build).
  РЕШЕНИЕ: добавляем в Фазе 5 (финализация), сейчас фокус на функциональности.
---
