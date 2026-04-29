from __future__ import annotations

import os
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./analyzer.db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


#
# Models
#

class Analysis(Base):
    __tablename__ = "analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    yaml_hash: Mapped[str] = mapped_column(String(64), nullable=False)  
    total_issues: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    info_count: Mapped[int] = mapped_column(Integer, default=0)

    issues: Mapped[list[IssueRecord]] = relationship(
        "IssueRecord", back_populates="analysis", cascade="all, delete-orphan"
    )


class IssueRecord(Base):
       __tablename__ = "issue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    line: Mapped[int] = mapped_column(Integer, default=0)
    col: Mapped[int] = mapped_column(Integer, default=0)
    job_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fix_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped[Analysis] = relationship("Analysis", back_populates="issues")


#
# Dependency for FastAPI
# 

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
