# Коды ошибок — CI/CD Pipeline Analyzer v0.1.1
# Обновлено: 2024-04

---

## HTTP API

| Код | Тип | Описание |
|-----|-----|----------|
| 201 | Success | Анализ выполнен, результат сохранён |
| 204 | Success | Запись удалена |
| 404 | Client | Результат не найден |
| 413 | Client | Файл > 512 KB |
| 422 | Client | Некорректный YAML или пустое тело |
| 500 | Server | Внутренняя ошибка сервера |

---

## Rule IDs — все 21 правило

| ID | Severity | Статус |
|----|----------|--------|
| SEC001 | ERROR | Реализовано |
| SEC002 | WARNING | Реализовано |
| SEC003 | ERROR | Реализовано |
| SEC004 | WARNING | Реализовано |
| SEC005 | INFO | Реализовано v0.1.1 |
| SEC006 | ERROR | Реализовано |
| PERF001 | WARNING | Реализовано |
| PERF002 | INFO | Реализовано |
| PERF003 | INFO | Реализовано |
| PERF004 | INFO | Реализовано v0.1.1 |
| PERF005 | WARNING | Реализовано |
| REL001 | INFO | Реализовано |
| REL002 | WARNING | Реализовано v0.1.1 |
| REL003 | INFO | Реализовано |
| REL004 | WARNING | Реализовано |
| REL005 | WARNING | Реализовано |
| BP001 | INFO | Реализовано |
| BP002 | INFO | Реализовано |
| BP003 | INFO | Реализовано |
| BP004 | WARNING | Реализовано v0.1.1 |
| BP005 | WARNING | Реализовано |

---

## Коды парсера

| Код | Источник | Описание |
|-----|----------|----------|
| PARSE-001 | yaml_parser._parse() | Не YAML-маппинг на верхнем уровне |
| PARSE-002 | yaml_parser._parse() | Пустой файл |
| PARSE-003 | yaml_parser._get_pos() | Нет позиции ключа (lc.data отсутствует) |

---

## Баги — исправлены

| ID | Версия | Файл | Описание |
|----|--------|------|----------|
| BUG-01 | v0.1.1 | rules/registry.py | Issue под TYPE_CHECKING — недоступен в runtime |
| BUG-02 | v0.1.1 | rules/security.py SEC001 | False positive: "production" помечался как секрет |
| BUG-03 | v0.1.1 | rules/security.py SEC006 | lc.item() AttributeError на CommentedSeq без позиций |
| BUG-04 | v0.1.1 | api/database.py | DATABASE_URL захардкожен, нельзя переопределить |
| BUG-05 | v0.1.1 | rules/base.py | emoji() ломал вывод в не-Unicode терминалах |
| BUG-06 | v0.1.1 | docker-compose.yml | ./data volume, но URL указывал на ./analyzer.db |
| BUG-07 | v0.1.1 | api/main.py CORS | Только localhost:3000/5173, нельзя добавить origins |
| BUG-08 | v0.1.1 | analyzer/main.py SARIF | physicalLocation не по спецификации, нет job_name/fix_suggestion |
| BUG-09 | v0.1.1 | rules/ | SEC005, PERF004, REL002, BP004 отсутствовали в реализации |

---

## Известные ограничения (не баги)

| ID | Описание | Версия |
|----|----------|--------|
| LIM-01 | include: remote URL не резолвится | v0.2.0 |
| LIM-02 | extends: и !reference — частичная поддержка | v0.2.0 |
| LIM-03 | Нет Alembic миграций | v0.2.0 |
| LIM-04 | Нет аутентификации в API | v0.3.0 |
| LIM-05 | Нет rate limiting | v0.2.0 |
