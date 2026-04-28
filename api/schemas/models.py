"""
Pydantic-схемы для запросов и ответов API.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SeverityEnum(str, Enum):
    error = "error"
    warning = "warning"
    info = "info"


class CategoryEnum(str, Enum):
    security = "security"
    performance = "performance"
    reliability = "reliability"
    best_practices = "best_practices"


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Тело запроса POST /analyze при передаче YAML как текста."""
    content: str = Field(..., description="Содержимое .gitlab-ci.yml", min_length=1)
    filename: str = Field(default=".gitlab-ci.yml", description="Имя файла для отчёта")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "image: python:latest\n\nbuild:\n  script:\n    - pip install -r requirements.txt\n",
                "filename": "my-pipeline.yml",
            }
        }
    }


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class IssueSchema(BaseModel):
    rule_id: str = Field(..., examples=["SEC001"])
    severity: SeverityEnum
    category: CategoryEnum
    message: str
    location: str = Field(default="", description='In "file.yml" in row N')
    line: int = Field(default=0)
    col: int = Field(default=0)
    filename: str = Field(default=".gitlab-ci.yml")
    job_name: str | None = None
    fix_suggestion: str | None = None


class SummarySchema(BaseModel):
    total: int
    error: int
    warning: int
    info: int


class AnalysisResultSchema(BaseModel):
    id: int
    filename: str
    created_at: datetime
    summary: SummarySchema
    issues: list[IssueSchema]

    model_config = {"from_attributes": True}


class AnalysisListItemSchema(BaseModel):
    """Краткая запись для GET /history."""
    id: int
    filename: str
    created_at: datetime
    summary: SummarySchema

    model_config = {"from_attributes": True}


class HealthSchema(BaseModel):
    status: str = "ok"
    rules_loaded: int
    version: str = "0.1.0"
