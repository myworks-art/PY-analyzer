"""
FastAPI приложение — точка входа для backend.

Запуск:
    uvicorn api.main:app --reload --port 8000

Документация:
    http://localhost:8000/docs     (Swagger UI)
    http://localhost:8000/redoc    (ReDoc)
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import init_db
from api.routers import analyze, history
from api.schemas.models import HealthSchema
from analyzer.rules import registry


import os

# CORS origins: в prod задайте ALLOWED_ORIGINS="https://your-domain.com"
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
_ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# ---------------------------------------------------------------------------
# Lifespan — инициализация при старте
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    # здесь можно добавить cleanup при остановке


# ---------------------------------------------------------------------------
# Приложение
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CI/CD Pipeline Analyzer",
    description=(
        "Инструмент статического анализа конфигурационных файлов GitLab CI.\n\n"
        "Выявляет проблемы **безопасности**, **производительности**, "
        "**надёжности** и нарушения **best practices**."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — разрешаем запросы от React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(analyze.router)
app.include_router(history.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthSchema,
    tags=["system"],
    summary="Статус сервиса",
)
async def health() -> HealthSchema:
    return HealthSchema(
        status="ok",
        rules_loaded=len(registry),
    )
