"""
Правила надёжности (REL001–REL005).
"""

from __future__ import annotations

import re

from ruamel.yaml.comments import CommentedMap

from analyzer.parsers.yaml_parser import ParsedPipeline, _get_pos
from analyzer.rules.base import BaseRule, Category, Severity
from analyzer.rules.registry import registry


@registry.register
class NoRetryRule(BaseRule):
    """REL001 — Джоб деплоя не настроен на повтор."""

    rule_id = "REL001"
    severity = Severity.INFO
    category = Category.RELIABILITY
    description = "Джоб деплоя не имеет retry при случайных сбоях"

    _DEPLOY_KEYWORDS = ("deploy", "release", "publish", "upload")

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []
        for job in pipeline.jobs:
            is_deploy = any(kw in job.name.lower() for kw in self._DEPLOY_KEYWORDS)
            if not is_deploy:
                continue
            if "retry" not in job.data:
                issues.append(
                    self._make_issue(
                        message=f"Джоб деплоя '{job.name}' не имеет настройки retry",
                        line=job.pos.line,
                        job_name=job.name,
                        fix_suggestion=(
                            "Добавьте retry: {max: 2, when: runner_system_failure} "
                            "для защиты от временных сбоев runner'а"
                        ),
                    )
                )
        return issues


@registry.register
class NoTestStageRule(BaseRule):
    """REL004 — В пайплайне нет стадии тестирования."""

    rule_id = "REL004"
    severity = Severity.WARNING
    category = Category.RELIABILITY
    description = "Пайплайн не содержит стадии тестирования"

    _TEST_STAGE_NAMES = ("test", "tests", "testing", "check", "verify", "lint")

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []

        all_stage_names = {s.lower() for s in pipeline.stages}

        # Также собираем stage из самих джобов (если stages не объявлены)
        for job in pipeline.jobs:
            stage = job.data.get("stage")
            if isinstance(stage, str):
                all_stage_names.add(stage.lower())

        has_test = any(name in self._TEST_STAGE_NAMES for name in all_stage_names)
        if not has_test and (pipeline.stages or pipeline.jobs):
            issues.append(
                self._make_issue(
                    message="Пайплайн не содержит стадии тестирования",
                    fix_suggestion=(
                        "Добавьте стадию 'test' и джобы с запуском тестов. "
                        "CI без тестов теряет свою основную ценность."
                    ),
                )
            )
        return issues


@registry.register
class DeployWithoutRulesRule(BaseRule):
    """REL005 — Джоб деплоя запускается без условий."""

    rule_id = "REL005"
    severity = Severity.WARNING
    category = Category.RELIABILITY
    description = "Джоб деплоя в прод запускается без ограничений на ветку"

    _PROD_KEYWORDS = ("prod", "production", "live")

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []
        for job in pipeline.jobs:
            is_prod_deploy = any(kw in job.name.lower() for kw in self._PROD_KEYWORDS)
            if not is_prod_deploy:
                continue

            has_restrictions = (
                "rules" in job.data
                or "only" in job.data
                or "except" in job.data
                or "when" in job.data
            )
            if not has_restrictions:
                issues.append(
                    self._make_issue(
                        message=(
                            f"Джоб '{job.name}' деплоит в прод без ограничений на ветку — "
                            "запустится при любом пуше"
                        ),
                        line=job.pos.line,
                        job_name=job.name,
                        fix_suggestion=(
                            "Добавьте: rules: [{if: '$CI_COMMIT_BRANCH == \"main\"'}] "
                            "чтобы деплой в прод запускался только из main"
                        ),
                    )
                )
        return issues


@registry.register
class NoStagesDeclaredRule(BaseRule):
    """REL003 — Секция stages не объявлена явно."""

    rule_id = "REL003"
    severity = Severity.INFO
    category = Category.RELIABILITY
    description = "Отсутствует явное объявление stages"

    def check(self, pipeline: ParsedPipeline) -> list:
        if not pipeline.stages and pipeline.jobs:
            return [
                self._make_issue(
                    message="Секция stages не объявлена — порядок выполнения неочевиден",
                    fix_suggestion=(
                        "Добавьте явное объявление stages в начало файла: "
                        "stages: [build, test, deploy]"
                    ),
                )
            ]
        return []


@registry.register
class UnpinnedDependenciesRule(BaseRule):
    """REL002 — Зависимости устанавливаются без фиксации версии."""

    rule_id = "REL002"
    severity = Severity.WARNING
    category = Category.RELIABILITY
    description = "Зависимости устанавливаются без фиксированных версий"

    # Команды без requirements-файла и без == в аргументах
    _UNPINNED_PATTERNS = re.compile(
        r"\b(pip3?\s+install|npm\s+install|yarn\s+add|gem\s+install|"
        r"composer\s+require|cargo\s+add)\s+(?!-r\s)(?!--requirement)"
        r"([a-zA-Z0-9_\-]+)(?!\s*[>=<!])",
        re.IGNORECASE,
    )

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []
        seen_jobs: set[str] = set()  # не дублируем одинаковые джобы

        for job in pipeline.jobs:
            if job.name in seen_jobs:
                continue

            for script_key in ("script", "before_script"):
                scripts = job.data.get(script_key)
                if not isinstance(scripts, list):
                    continue
                for cmd in scripts:
                    if not isinstance(cmd, str):
                        continue
                    m = self._UNPINNED_PATTERNS.search(cmd)
                    if m:
                        pkg = m.group(2)
                        pos = _get_pos(job.data, script_key)
                        issues.append(
                            self._make_issue(
                                message=(
                                    f"Пакет '{pkg}' устанавливается без фиксации версии"
                                ),
                                line=pos.line if pos else job.pos.line,
                                job_name=job.name,
                                fix_suggestion=(
                                    "Зафиксируйте версию: pip install requests==2.31.0 "
                                    "или используйте requirements.txt с pip install -r requirements.txt"
                                ),
                            )
                        )
                        seen_jobs.add(job.name)
                        break  # одно замечание на джоб
        return issues
