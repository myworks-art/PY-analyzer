#
# GET /history, GET /result/{id}, DELETE /result/{id}
#

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.database import Analysis, get_db
from api.schemas.models import (
    AnalysisListItemSchema,
    AnalysisResultSchema,
    IssueSchema,
    SummarySchema,
)

router = APIRouter(tags=["history"])


#
# GET /history
#

@router.get(
    "/history",
    response_model=list[AnalysisListItemSchema],
    summary="История анализов",
    description="Список последних анализов, без деталей issues.",
)
async def get_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100, description="Кол-во записей"),
    offset: int = Query(default=0, ge=0, description="Смещение для пагинации"),
) -> list[AnalysisListItemSchema]:
    result = await db.execute(
        select(Analysis)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    analyses = result.scalars().all()

    return [
        AnalysisListItemSchema(
            id=a.id,
            filename=a.filename,
            created_at=a.created_at,
            summary=SummarySchema(
                total=a.total_issues,
                error=a.error_count,
                warning=a.warning_count,
                info=a.info_count,
            ),
        )
        for a in analyses
    ]


#
# GET /result/{id}
#

@router.get(
    "/result/{analysis_id}",
    response_model=AnalysisResultSchema,
    summary="Результат анализа по ID",
)
async def get_result(
    analysis_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalysisResultSchema:
    result = await db.execute(
        select(Analysis)
        .where(Analysis.id == analysis_id)
        .options(selectinload(Analysis.issues))
    )
    analysis = result.scalar_one_or_none()

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Анализ с id={analysis_id} не найден",
        )

    return AnalysisResultSchema(
        id=analysis.id,
        filename=analysis.filename,
        created_at=analysis.created_at,
        summary=SummarySchema(
            total=analysis.total_issues,
            error=analysis.error_count,
            warning=analysis.warning_count,
            info=analysis.info_count,
        ),
        issues=[
            IssueSchema(
                rule_id=i.rule_id,
                severity=i.severity,
                category=i.category,
                message=i.message,
                line=i.line,
                col=i.col,
                job_name=i.job_name,
                fix_suggestion=i.fix_suggestion,
            )
            for i in analysis.issues
        ],
    )


#
# DELETE /result/{id}
#

@router.delete(
    "/result/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить результат анализа",
)
async def delete_result(
    analysis_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
    analysis = result.scalar_one_or_none()

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Анализ с id={analysis_id} не найден",
        )

    await db.delete(analysis)
    await db.commit()
