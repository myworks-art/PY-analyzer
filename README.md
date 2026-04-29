# CI/CD Pipeline Analyzer

Инструмент статического анализа конфигурационных файлов GitLab CI (`.gitlab-ci.yml`).
Выявляет проблемы безопасности, производительности и нарушения best practices.

**Версия:** 0.3.0 · **Python:** 3.12+ · **Стек:** FastAPI · ruamel.yaml · React · SQLite

---

## Быстрый старт

### Docker

```bash
git clone https://github.com/myworks-art/PY-analyzer.git
cd PY-analyzer
mkdir -p data logs
docker-compose up
```

- Web UI: http://localhost:3000
- Swagger API: http://localhost:8000/docs

### Локально

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Backend
uvicorn api.main:app --reload --port 8000

# Frontend (в отдельном терминале)
cd frontend && npm install && npm run dev
```

### CLI

```bash
# Анализ с текстовым выводом
python -m analyzer check .gitlab-ci.yml

# JSON-отчёт
python -m analyzer check .gitlab-ci.yml --format json

# SARIF (совместим с GitLab CodeQuality / GitHub Security)
python -m analyzer check .gitlab-ci.yml --format sarif

# Только ошибки (без предупреждений и замечаний)
python -m analyzer check .gitlab-ci.yml --severity error
```

**Пример вывода:**

```
Анализ: .gitlab-ci.yml
────────────────────────────────────────────────────────────
ERROR    [SEC001] In ".gitlab-ci.yml" in row 5 — Возможный секрет в переменной 'DB_PASSWORD'
ERROR    [SEC006] [deploy] In ".gitlab-ci.yml" in row 18 — curl/wget piped to shell
WARNING  [SEC002] In ".gitlab-ci.yml" in row 1 — Образ использует тег latest
WARNING  [PERF001] [build] In ".gitlab-ci.yml" in row 12 — Установка pip без cache

────────────────────────────────────────────────────────────
Найдено 4 проблем: 2 ошибок, 2 предупреждений, 0 замечаний
```

---

## Правила анализа

21 правило в 4 категориях. Полный каталог: [docs/rules.md](docs/rules.md)

| Категория | Кол-во | Примеры |
|-----------|--------|---------|
| SEC — Безопасность | 6 | Секреты в переменных, latest-образы, privileged mode, curl\|bash |
| PERF — Производительность | 5 | Нет кэша зависимостей, артефакты без expire_in, дублирование before_script |
| REL — Надёжность | 5 | Нет стадии test, деплой без условий на ветку, зависимости без версий |
| BP — Best Practices | 5 | Смешанное именование, нет stages, дублирование конфигурации |

---

## REST API

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/health` | Статус + количество загруженных правил |
| POST | `/analyze/` | Анализ (JSON body: `{content, filename}`) |
| POST | `/analyze/upload` | Анализ (multipart: файл) |
| GET | `/history` | История анализов (пагинация: `?limit=20&offset=0`) |
| GET | `/result/{id}` | Детали анализа |
| DELETE | `/result/{id}` | Удалить запись |

Swagger UI: http://localhost:8000/docs

---

## Структура проекта

```
PY-analyzer/
├── analyzer/                  # Ядро анализатора (Python)
│   ├── main.py                # CLI точка входа
│   ├── logger.py              # Централизованное логирование
│   ├── parsers/
│   │   └── yaml_parser.py     # ruamel.yaml парсер с line:col
│   └── rules/
│       ├── base.py            # BaseRule, Issue, Severity, Category
│       ├── registry.py        # Реестр правил (@registry.register)
│       ├── security.py        # SEC001–SEC006
│       ├── performance.py     # PERF001–PERF005
│       ├── reliability.py     # REL001–REL005
│       └── best_practices.py  # BP001–BP005
├── api/                       # FastAPI backend
│   ├── main.py                # Приложение, CORS, lifespan
│   ├── database.py            # SQLAlchemy модели (Analysis, IssueRecord)
│   ├── routers/
│   │   ├── analyze.py         # POST /analyze, POST /analyze/upload
│   │   └── history.py         # GET /history, GET /result/{id}, DELETE
│   └── schemas/
│       └── models.py          # Pydantic схемы запросов и ответов
├── frontend/                  # React + Vite SPA
│   ├── debug/
│   │   ├── error_codes.md     # Каталог кодов ошибок
│   │   └── debug_log.md       # Журнал отладки
│   └── src/
├── tests/
│   ├── unit/                  # pytest: парсер, правила
│   ├── integration/           # pytest: API (httpx AsyncClient)
│   └── fixtures/              # Примеры .gitlab-ci.yml
├── docs/
│   ├── architecture.md        # Архитектурные диаграммы
│   ├── rules.md               # Полный каталог правил
│   └── dev-journal.md         # Журнал разработки
├── logs/                      # Автоматические логи (gitignored)
├── data/                      # SQLite БД (gitignored)
├── Dockerfile                 # Multi-stage, non-root user
├── docker-compose.yml
├── .pre-commit-config.yaml
├── pyproject.toml
└── requirements.txt
```

---

## Разработка

```bash
# Установка зависимостей и pre-commit
pip install -r requirements.txt
pip install pre-commit
pre-commit install

# Тесты с покрытием
python -m pytest tests/ -v --cov=analyzer --cov=api --cov-report=term-missing

# Только unit-тесты
python -m pytest tests/unit/ -v

# Линтинг
ruff check .
ruff format .
```

---

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|--------------|----------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./analyzer.db` | URL базы данных |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | CORS: список разрешённых origins |

---

## Известные ограничения

| ID | Описание | Версия |
|----|----------|--------|
| LIM-01 | `include:` с remote URL не резолвится | v0.2.0 |
| LIM-02 | `extends:` и `!reference` — частичная поддержка | v0.2.0 |
| LIM-03 | Нет миграций БД (Alembic) | v0.2.0 |
| LIM-04 | Нет аутентификации в API | v0.3.0 |

Полный список: [frontend/debug/error_codes.md](frontend/debug/error_codes.md)

---
