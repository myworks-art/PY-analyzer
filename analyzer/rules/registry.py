#
#Использование:
#    from analyzer.rules.registry import registry
#
# Получить все правила
#    all_rules = registry.get_all()
#
# Запустить все правила на пайплайне
#   issues = registry.run_all(pipeline)
#

from __future__ import annotations

from typing import TYPE_CHECKING, Type

from analyzer.logger import get_logger

log = get_logger(__name__)

if TYPE_CHECKING:
    from analyzer.rules.base import BaseRule
    from analyzer.parsers.yaml_parser import ParsedPipeline


class RuleRegistry:

    def __init__(self) -> None:
        self._rules: list[Type[BaseRule]] = []

    def register(self, rule_class: Type[BaseRule]) -> Type[BaseRule]:
        self._rules.append(rule_class)
        log.debug("Зарегистрировано правило: %s", rule_class.rule_id)
        return rule_class

    def get_all(self) -> list[BaseRule]:
        return [cls() for cls in self._rules]

    def run_all(self, pipeline: ParsedPipeline) -> list:
        from analyzer.rules.base import Severity

        log.info(
            "Запуск анализа: %s (%d правил, %d джобов)",
            pipeline.filename, len(self._rules), len(pipeline.jobs),
        )

        all_issues: list[Issue] = []
        for rule in self.get_all():
            try:
                issues = rule.check(pipeline)
                for issue in issues:
                    issue.filename = pipeline.filename
                all_issues.extend(issues)
                if issues:
                    log.debug(
                        "  %s: найдено %d проблем",
                        rule.rule_id, len(issues),
                    )
            except Exception as e:
                log.error(
                    "Правило %s упало с ошибкой: %s",
                    rule.rule_id, e, exc_info=True,
                )

        severity_order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
        all_issues.sort(key=lambda i: severity_order.get(i.severity, 99))

        log.info(
            len(all_issues),
            sum(1 for i in all_issues if i.severity == Severity.ERROR),
            sum(1 for i in all_issues if i.severity == Severity.WARNING),
            sum(1 for i in all_issues if i.severity.value == "info"),
        )
        return all_issues

    def __len__(self) -> int:
        return len(self._rules)

    def __repr__(self) -> str:
        return f"RuleRegistry({[cls.__name__ for cls in self._rules]})"


registry = RuleRegistry()
