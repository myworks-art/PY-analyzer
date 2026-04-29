from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from analyzer.parsers.yaml_parser import ParsedPipeline


#
# Перечисления
#

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def __lt__(self, other: Severity) -> bool:
        order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
        return order[self] < order[other]


class Category(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    BEST_PRACTICES = "best_practices"

    def label(self) -> str:
        return {
            "security": "Безопасность",
            "performance": "Производительность",
            "reliability": "Надёжность",
            "best_practices": "Best Practices",
        }[self.value]


# 
# Issue
# 

@dataclass
class Issue:
    rule_id: str
    severity: Severity
    category: Category
    message: str
    line: int = 0
    col: int = 0
    job_name: str | None = None
    fix_suggestion: str | None = None
    filename: str = ".gitlab-ci.yml"

    def location_str(self) -> str:
        parts = [f'In "{self.filename}"']
        if self.line > 0:
            parts.append(f"in row {self.line}")
        return " ".join(parts)

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "location": self.location_str(),
            "line": self.line,
            "col": self.col,
            "filename": self.filename,
            "job_name": self.job_name,
            "fix_suggestion": self.fix_suggestion,
        }

    def __str__(self) -> str:
        job = f" [{self.job_name}]" if self.job_name else ""
        return (
            f"{self.severity.value.upper():<8} [{self.rule_id}]{job} "
            f"{self.location_str()} — {self.message}"
        )


# 
# BaseRule
# 

class BaseRule(ABC):
    rule_id: str = ""
    severity: Severity = Severity.INFO
    category: Category = Category.BEST_PRACTICES
    description: str = ""

    @abstractmethod
    def check(self, pipeline: ParsedPipeline) -> list[Issue]:

        ...

    def _make_issue(
        self,
        message: str,
        line: int = 0,
        col: int = 0,
        job_name: str | None = None,
        fix_suggestion: str | None = None,
    ) -> Issue:
       
        return Issue(
            rule_id=self.rule_id,
            severity=self.severity,
            category=self.category,
            message=message,
            line=line,
            col=col,
            job_name=job_name,
            fix_suggestion=fix_suggestion,
        )
