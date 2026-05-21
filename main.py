from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.database import init_db
from api.routers import analyze, history
from api.schemas.models import HealthSchema
from analyzer.rules.registry import registry
#импорт всех модулей правил
#запускает @registry.register декораторы
import analyzer.rules.security       # noqa: F401
import analyzer.rules.performance    # noqa: F401
import analyzer.rules.reliability    # noqa: F401
import analyzer.rules.best_practices # noqa: F401

# Rate limiter — идентифицируем по IP
limiter = Limiter(key_func=get_remote_address)


import os

# CORS origins: ALLOWED_ORIGINS="https:/domain.com" (LATER)
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
_ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# 
# Lifespan
#

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    #можно добавить cleanup при остановке


# 
# Приложение
# 

app = FastAPI(
    title="CI/CD Pipeline Analyzer",
    description=(
        "Инструмент статического анализа конфигурационных файлов GitLab CI.\n\n"
        "Выявляет проблемы **безопасности**, **производительности**, "
        "**надёжности** и нарушения **best practices**."
    ),
    version="0.1.1",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting: не более 30 з/м
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow requests from React Dev Serv
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect routers
app.include_router(analyze.router)
app.include_router(history.router)


# 
# Health check
# 

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
