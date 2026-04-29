#
# best practices (BP001–BP005).
#

from __future__ import annotations

import re

from ruamel.yaml.comments import CommentedMap

from analyzer.parsers.yaml_parser import ParsedPipeline, _get_pos
from analyzer.rules.base import BaseRule, Category, Severity
from analyzer.rules.registry import registry


@registry.register
class NoJobDescriptionRule(BaseRule):

    rule_id = "BP001"
    severity = Severity.INFO
    category = Category.BEST_PRACTICES
    description = "У джоба отсутствует поле description"

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []
        for job in pipeline.jobs:
            if "description" not in job.data:
                issues.append(
                    self._make_issue(
                        message=f"Джоб '{job.name}' не имеет поля description",
                        line=job.pos.line,
                        job_name=job.name,
                        fix_suggestion=(
                            "Добавьте поле description: 'Что делает этот джоб' — "
                            "улучшает читаемость пайплайна"
                        ),
                    )
                )
        return issues


@registry.register
class NamingConventionRule(BaseRule):

    rule_id = "BP002"
    severity = Severity.INFO
    category = Category.BEST_PRACTICES
    description = "Имена джобов не следуют единому стилю (kebab-case / snake_case)"

    _KEBAB = re.compile(r"^[a-z][a-z0-9-]*$")
    _SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")

    def check(self, pipeline: ParsedPipeline) -> list:
        if len(pipeline.jobs) < 2:
            return []

        styles: dict[str, list[str]] = {"kebab": [], "snake": [], "other": []}
        for job in pipeline.jobs:
            name = job.name
            if self._KEBAB.match(name) and "-" in name:
                styles["kebab"].append(name)
            elif self._SNAKE.match(name) and "_" in name:
                styles["snake"].append(name)
            elif self._KEBAB.match(name) or self._SNAKE.match(name):
                pass
            else:
                styles["other"].append(name)

        active = [k for k, v in styles.items() if k != "other" and v]
        if len(active) >= 2:
            return [
                self._make_issue(
                    message=(
                        f"Смешанный стиль именования: kebab-case ({', '.join(styles['kebab'][:3])}) "
                        f"и snake_case ({', '.join(styles['snake'][:3])})"
                    ),
                    fix_suggestion="Выберите один стиль (рекомендуется kebab-case) и придерживайтесь его",
                )
            ]
        return []


@registry.register
class NoEnvironmentRule(BaseRule):

    rule_id = "BP003"
    severity = Severity.INFO
    category = Category.BEST_PRACTICES
    description = "Джоб деплоя не объявляет environment"

    _DEPLOY_KEYWORDS = ("deploy", "release", "publish")

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []
        for job in pipeline.jobs:
            is_deploy = any(kw in job.name.lower() for kw in self._DEPLOY_KEYWORDS)
            if not is_deploy:
                continue
            if "environment" not in job.data:
                issues.append(
                    self._make_issue(
                        message=f"Джоб '{job.name}' не использует секцию environment",
                        line=job.pos.line,
                        job_name=job.name,
                        fix_suggestion=(
                            "Добавьте environment: {name: staging, url: 'https://staging.example.com'} — "
                            "даёт трекинг деплоев и кнопку rollback в GitLab UI"
                        ),
                    )
                )
        return issues


@registry.register
class MissingStagesSectionRule(BaseRule):

    rule_id = "BP005"
    severity = Severity.WARNING
    category = Category.BEST_PRACTICES
    description = "Секция stages не объявлена в начале файла"

    def check(self, pipeline: ParsedPipeline) -> list:
        if not pipeline.stages and len(pipeline.jobs) >= 3:
            return [
                self._make_issue(
                    message="Секция stages не объявлена — порядок стадий неочевиден",
                    fix_suggestion=(
                        "Добавьте явное объявление stages: в начало .gitlab-ci.yml: "
                        "stages: [build, test, deploy]"
                    ),
                )
            ]
        return []


@registry.register
class ConfigDuplicationRule(BaseRule):

    rule_id = "BP004"
    severity = Severity.WARNING
    category = Category.BEST_PRACTICES
    description = "Несколько джобов содержат идентичные блоки конфигурации"

    _CHECK_KEYS = ("image", "services", "variables")
    _MIN_JOBS = 2

    def check(self, pipeline: ParsedPipeline) -> list:
        issues = []

        for key in self._CHECK_KEYS:
            values: dict[str, list[str]] = {}
            for job in pipeline.jobs:
                val = job.data.get(key)
                if val is None:
                    continue
                val_repr = repr(dict(val)) if hasattr(val, "items") else repr(val)
                values.setdefault(val_repr, []).append(job.name)

            for val_repr, job_names in values.items():
                if len(job_names) >= self._MIN_JOBS:
                    issues.append(
                        self._make_issue(
                            message=(
                                f"Блок '{key}' дублируется в джобах: "
                                f"{', '.join(job_names[:4])}"
                                f"{' и др.' if len(job_names) > 4 else ''}"
                            ),
                            fix_suggestion=(
                                f"Вынесите '{key}' в секцию default: "
                                "или используйте YAML anchors (&anchor / *alias) / extends:"
                            ),
                        )
                    )

        return issues
