"""
Роутер анализа: POST /analyze
Принимает YAML как текст (JSON body) или как загружаемый файл (multipart/form-data).
"""
from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from analyzer.parsers.yaml_parser import YamlParser
from analyzer.rules import registry
from analyzer.rules.base import Severity
from analyzer.logger import get_logger
from api.database import Analysis, IssueRecord, get_db
from api.schemas.models import AnalysisResultSchema, AnalyzeRequest, SummarySchema, IssueSchema

log = get_logger("api.analyze")

router = APIRouter(prefix="/analyze", tags=["analyze"])

_parser = YamlParser()
MAX_YAML_SIZE = 512 * 1024  # 512 KB


# ---------------------------------------------------------------------------
# Хелперы
# ---------------------------------------------------------------------------

def _run_analysis(content: str, filename: str) -> tuple[list, dict]:
    """Парсим YAML и запускаем правила. Возвращает (issues, summary)."""
    try:
        pipeline = _parser.parse_string(content, filename=filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ошибка парсинга YAML: {e}",
        )

    issues = registry.run_all(pipeline)
    summary = {
        "total": len(issues),
        "error": sum(1 for i in issues if i.severity == Severity.ERROR),
        "warning": sum(1 for i in issues if i.severity == Severity.WARNING),
        "info": sum(1 for i in issues if i.severity.value == "info"),
    }
    return issues, summary


async def _save_to_db(
    db: AsyncSession,
    content: str,
    filename: str,
    issues: list,
    summary: dict,
) -> Analysis:
    """Сохранить результат анализа в БД."""
    yaml_hash = hashlib.sha256(content.encode()).hexdigest()

    record = Analysis(
        filename=filename,
        yaml_hash=yaml_hash,
        total_issues=summary["total"],
        error_count=summary["error"],
        warning_count=summary["warning"],
        info_count=summary["info"],
    )
    db.add(record)
    await db.flush()  # получаем record.id

    for issue in issues:
        db.add(IssueRecord(
            analysis_id=record.id,
            rule_id=issue.rule_id,
            category=issue.category.value,
            severity=issue.severity.value,
            message=issue.message,
            line=issue.line,
            col=issue.col,
            job_name=issue.job_name,
            fix_suggestion=issue.fix_suggestion,
        ))

    await db.commit()
    await db.refresh(record)
    return record


def _build_response(record: Analysis, issues: list) -> AnalysisResultSchema:
    return AnalysisResultSchema(
        id=record.id,
        filename=record.filename,
        created_at=record.created_at,
        summary=SummarySchema(
            total=record.total_issues,
            error=record.error_count,
            warning=record.warning_count,
            info=record.info_count,
        ),
        issues=[
            IssueSchema(
                rule_id=i.rule_id,
                severity=i.severity,          # type: ignore[arg-type]
                category=i.category,          # type: ignore[arg-type]
                message=i.message,
                location=i.location_str(),
                line=i.line,
                col=i.col,
                filename=i.filename,
                job_name=i.job_name,
                fix_suggestion=i.fix_suggestion,
            )
            for i in issues
        ],
    )


# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=AnalysisResultSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Анализ YAML (JSON body)",
    description="Принимает содержимое .gitlab-ci.yml как текст, возвращает структурированный отчёт.",
)
async def analyze_text(
    body: AnalyzeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalysisResultSchema:
    if len(body.content.encode()) > MAX_YAML_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл превышает максимальный размер {MAX_YAML_SIZE // 1024} KB",
        )

    issues, summary = _run_analysis(body.content, body.filename)
    record = await _save_to_db(db, body.content, body.filename, issues, summary)
    return _build_response(record, issues)


@router.post(
    "/upload",
    response_model=AnalysisResultSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Анализ YAML (загрузка файла)",
    description="Принимает .gitlab-ci.yml как multipart/form-data файл.",
)
async def analyze_upload(
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(..., description="Файл .gitlab-ci.yml"),
) -> AnalysisResultSchema:
    content_bytes = await file.read()

    if len(content_bytes) > MAX_YAML_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл превышает максимальный размер {MAX_YAML_SIZE // 1024} KB",
        )

    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Файл должен быть в кодировке UTF-8",
        )

    filename = file.filename or ".gitlab-ci.yml"
    issues, summary = _run_analysis(content, filename)
    record = await _save_to_db(db, content, filename, issues, summary)
    return _build_response(record, issues)
