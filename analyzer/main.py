#
#CLI for CI/CD Pipeline Analyzer.
#
#Usage:
#    python -m analyzer check .gitlab-ci.yml
#    python -m analyzer check .gitlab-ci.yml --format json
#    python -m analyzer check .gitlab-ci.yml --format sarif
#    python -m analyzer check .gitlab-ci.yml --severity error
#

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analyzer",
        description="CI/CD Pipeline Analyzer — статический анализ .gitlab-ci.yml",
    )
    sub = parser.add_subparsers(dest="command")

    # check
    check = sub.add_parser("check", help="Проанализировать файл")
    check.add_argument("file", help="Путь к .gitlab-ci.yml")
    check.add_argument(
        "--format",
        choices=["text", "json", "sarif"],
        default="text",
        help="Формат вывода (по умолчанию: text)",
    )
    check.add_argument(
        "--severity",
        choices=["error", "warning", "info"],
        default="info",
        help="Минимальный уровень severity для вывода (по умолчанию: info = всё)",
    )
    check.add_argument(
        "--no-color",
        action="store_true",
        help="Отключить цветной вывод",
    )

    return parser


def cmd_check(args: argparse.Namespace) -> int:
    from analyzer.parsers.yaml_parser import YamlParser
    from analyzer.rules import registry
    from analyzer.rules.base import Severity

    path = Path(args.file)
    if not path.exists():
        print(f"Ошибка: файл не найден: {path}", file=sys.stderr)
        return 2
    if not path.is_file():
        print(f"Ошибка: {path} не является файлом", file=sys.stderr)
        return 2

    try:
        parser = YamlParser()
        pipeline = parser.parse_file(path)
    except Exception as e:
        print(f"Ошибка парсинга YAML: {e}", file=sys.stderr)
        return 2

    issues = registry.run_all(pipeline)

    severity_levels = {
        "error": {Severity.ERROR},
        "warning": {Severity.ERROR, Severity.WARNING},
        "info": {Severity.ERROR, Severity.WARNING, Severity.INFO},
    }
    allowed = severity_levels[args.severity]
    issues = [i for i in issues if i.severity in allowed]

    if args.format == "json":
        _output_json(issues, pipeline.filename)
    elif args.format == "sarif":
        _output_sarif(issues, path)
    else:
        _output_text(issues, pipeline.filename)

    has_errors = any(i.severity.value == "error" for i in issues)
    return 1 if has_errors else 0


def _output_text(issues: list, filename: str) -> None:
    from analyzer.rules.base import Severity

    print(f"\nАнализ: {filename}")
    print("─" * 60)

    if not issues:
        print(" Проблем не найдено!")
        return

    for issue in issues:
        print(issue)
        if issue.fix_suggestion:
            print(f"  {issue.fix_suggestion}")
        print()

    print("─" * 60)
    errors = sum(1 for i in issues if i.severity == Severity.ERROR)
    warnings = sum(1 for i in issues if i.severity == Severity.WARNING)
    infos = sum(1 for i in issues if i.severity.value == "info")
    print(
        f"Найдено {len(issues)} проблем: "
        f"{errors} ошибок, {warnings} предупреждений, {infos} замечаний"
    )


def _output_json(issues: list, filename: str) -> None:
    from analyzer.rules.base import Severity

    result = {
        "filename": filename,
        "summary": {
            "total": len(issues),
            "error": sum(1 for i in issues if i.severity == Severity.ERROR),
            "warning": sum(1 for i in issues if i.severity == Severity.WARNING),
            "info": sum(1 for i in issues if i.severity.value == "info"),
        },
        "issues": [i.to_dict() for i in issues],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _output_sarif(issues: list, path: Path) -> None:   
    rules_seen: dict[str, dict] = {}
    results = []

    sev_map = {"error": "error", "warning": "warning", "info": "note"}

    for issue in issues:
        if issue.rule_id not in rules_seen:
            rules_seen[issue.rule_id] = {
                "id": issue.rule_id,
                "name": issue.rule_id,
                "shortDescription": {"text": issue.message},
                "helpUri": f"https://github.com/myworks-art/PY-analyzer/blob/main/docs/rules.md#{issue.rule_id.lower()}",
                "defaultConfiguration": {
                    "level": sev_map.get(issue.severity.value, "note")
                },
                "properties": {
                    "category": issue.category.value,
                },
            }

        result: dict = {
            "ruleId": issue.rule_id,
            "level": sev_map.get(issue.severity.value, "note"),
            "message": {"text": issue.message},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": str(path),
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {
                            "startLine": max(issue.line, 1),
                            "startColumn": max(issue.col, 1),
                        },
                    }
                }
            ],
            "properties": {},
        }

        if issue.job_name:
            result["properties"]["jobName"] = issue.job_name
        if issue.fix_suggestion:
            result["properties"]["fixSuggestion"] = issue.fix_suggestion

        results.append(result)

    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "cicd-analyzer",
                        "version": "0.1.1",
                        "informationUri": "https://github.com/myworks-art/PY-analyzer",
                        "rules": list(rules_seen.values()),
                    }
                },
                "results": results,
            }
        ],
    }
    print(json.dumps(sarif, ensure_ascii=False, indent=2))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "check":
        sys.exit(cmd_check(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
