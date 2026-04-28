"""
Правила производительности (PERF001–PERF005).
"""

from __future__ import annotations

import re

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from analyzer.parsers.yaml_parser import ParsedPipeline, _get_pos
from analyzer.rules.base import BaseRule, Category, Severity
from analyzer.rules.registry import registry

# Паттерны команд установки зависимостей
_INSTALL_PATTERNS = re.compile(
    r"\b(pip install|pip3 install|npm install|npm ci|yarn install|"
    r"mvn install|gradle build|composer install|bundle install|"
    r"apt-get install|apt install)\b",
    re.IGNORECASE,
)


@registry.register
class NoDependencyCacheRule(BaseRule):
    """PERF001 — Установка зависимостей без кэша."""

    rule_id = "PERF001"
    severity = Severity.WARNING
    category = Category.PERFORMANCE
    description = "Зависимости устанавливаются без настройки cache"

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []
        for job in pipeline.jobs:
            # Если у джоба нет cache — ищем установку зависимостей в скриптах
            has_cache = "cache" in job.data
            if has_cache:
                continue

            for script_key in ("script", "before_script"):
                script = job.data.get(script_key)
                if not isinstance(script, (list, CommentedSeq)):
                    continue
                for cmd in script:
                    if isinstance(cmd, str) and _INSTALL_PATTERNS.search(cmd):
                        pos = _get_pos(job.data, script_key)
                        issues.append(
                            self._make_issue(
                                message=(
                                    f"Джоб устанавливает зависимости ({cmd.strip()[:50]}…) "
                                    "без настройки 'cache'"
                                ),
                                line=pos.line if pos else 0,
                                job_name=job.name,
                                fix_suggestion=(
                                    "Добавьте секцию cache с путём к директории зависимостей. "
                                    "Пример для pip: cache: {key: pip, paths: [.pip-cache/]}"
                                ),
                            )
                        )
                        break  # достаточно одного совпадения на script_key

        return issues


@registry.register
class ArtifactsNoExpireRule(BaseRule):
    """PERF002 — Артефакты без срока жизни."""

    rule_id = "PERF002"
    severity = Severity.INFO
    category = Category.PERFORMANCE
    description = "Артефакты без expire_in хранятся вечно"

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []
        for job in pipeline.jobs:
            artifacts = job.data.get("artifacts")
            if not isinstance(artifacts, CommentedMap):
                continue
            if "expire_in" not in artifacts:
                pos = _get_pos(job.data, "artifacts")
                issues.append(
                    self._make_issue(
                        message="Артефакты не имеют срока жизни (expire_in не задан)",
                        line=pos.line if pos else 0,
                        job_name=job.name,
                        fix_suggestion=(
                            "Добавьте expire_in в секцию artifacts. "
                            "Пример: expire_in: 1 week"
                        ),
                    )
                )
        return issues


@registry.register
class ExcessiveTimeoutRule(BaseRule):
    """PERF003 — Избыточный таймаут джоба."""

    rule_id = "PERF003"
    severity = Severity.INFO
    category = Category.PERFORMANCE
    description = "Таймаут джоба превышает 2 часа"

    # Разбираем строки вида: "3h", "3h 30m", "200m", "7200"
    _TIMEOUT_PATTERN = re.compile(
        r"(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:in(?:utes?)?)?)?\s*(?:(\d+)\s*s(?:ec(?:onds?)?)?)?",
        re.IGNORECASE,
    )
    _MAX_MINUTES = 120

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []
        for job in pipeline.jobs:
            timeout_val = job.data.get("timeout")
            if timeout_val is None:
                continue
            minutes = self._parse_timeout_minutes(str(timeout_val))
            if minutes is not None and minutes > self._MAX_MINUTES:
                pos = _get_pos(job.data, "timeout")
                issues.append(
                    self._make_issue(
                        message=(
                            f"Таймаут джоба '{timeout_val}' ({minutes} мин) "
                            f"превышает {self._MAX_MINUTES} минут"
                        ),
                        line=pos.line if pos else 0,
                        job_name=job.name,
                        fix_suggestion=(
                            "Оптимизируйте джоб или разбейте на несколько. "
                            "Длинные таймауты блокируют runner при зависании."
                        ),
                    )
                )
        return issues

    def _parse_timeout_minutes(self, value: str) -> int | None:
        """Конвертировать строку таймаута в минуты."""
        value = value.strip()
        # Просто число — секунды
        if value.isdigit():
            return int(value) // 60
        m = self._TIMEOUT_PATTERN.match(value)
        if not m:
            return None
        hours = int(m.group(1) or 0)
        minutes = int(m.group(2) or 0)
        return hours * 60 + minutes


@registry.register
class DuplicateBeforeScriptRule(BaseRule):
    """PERF005 — Одинаковый before_script в нескольких джобах."""

    rule_id = "PERF005"
    severity = Severity.WARNING
    category = Category.PERFORMANCE
    description = "Дублирование before_script — вынесите в default:"

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []
        # Собираем before_script из всех джобов
        scripts: dict[str, list[str]] = {}  # job_name -> before_script строки

        for job in pipeline.jobs:
            bs = job.data.get("before_script")
            if isinstance(bs, (list, CommentedSeq)):
                key = "\n".join(str(s) for s in bs)
                if key not in scripts:
                    scripts[key] = []
                scripts[key].append(job.name)

        # Если одинаковый before_script у 2+ джобов
        for script_content, job_names in scripts.items():
            if len(job_names) >= 2:
                first_job = next(j for j in pipeline.jobs if j.name == job_names[0])
                pos = _get_pos(first_job.data, "before_script")
                issues.append(
                    self._make_issue(
                        message=(
                            f"Одинаковый before_script в джобах: {', '.join(job_names)}. "
                            "Вынесите в секцию default:"
                        ),
                        line=pos.line if pos else 0,
                        fix_suggestion=(
                            "Используйте 'default: before_script: [...]' "
                            "или YAML anchors (&anchor / *alias)"
                        ),
                    )
                )

        return issues


@registry.register
class NoParallelismRule(BaseRule):
    """PERF004 — Независимые джобы не используют needs для параллельного запуска."""

    rule_id = "PERF004"
    severity = Severity.INFO
    category = Category.PERFORMANCE
    description = "Несколько джобов в одной стадии не используют needs/parallel"

    _MIN_JOBS_PER_STAGE = 3  # проверяем только если джобов >= 3 в одной стадии

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []

        # Группируем джобы по стадии
        by_stage: dict[str, list] = {}
        for job in pipeline.jobs:
            stage = str(job.data.get("stage", "test"))
            by_stage.setdefault(stage, []).append(job)

        for stage, jobs in by_stage.items():
            if len(jobs) < self._MIN_JOBS_PER_STAGE:
                continue

            # Ни один из джобов не использует needs/parallel
            uses_parallel = any(
                "needs" in job.data or "parallel" in job.data
                for job in jobs
            )
            if not uses_parallel:
                issues.append(
                    self._make_issue(
                        message=(
                            f"Стадия '{stage}' содержит {len(jobs)} джоба(ов) "
                            "без needs/parallel — выполняются последовательно"
                        ),
                        fix_suggestion=(
                            "Используйте needs: [] для запуска джобов параллельно "
                            "без ожидания предыдущей стадии, "
                            "или parallel: N для матрица-сборок"
                        ),
                    )
                )

        return issues

