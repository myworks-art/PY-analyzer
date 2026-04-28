"""
Интеграционные тесты API.

Используем httpx AsyncClient + тестовую in-memory SQLite БД.

Запуск:
    pytest tests/integration/test_api.py -v
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.database import Base, get_db
from api.main import app

# ---------------------------------------------------------------------------
# Фикстуры — тестовая БД в памяти
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_db_session():
    """Отдельная in-memory БД для каждого теста."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db_session: AsyncSession):
    """HTTP-клиент с подменённой зависимостью БД."""

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealth:

    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["rules_loaded"] > 0

    @pytest.mark.asyncio
    async def test_health_reports_rule_count(self, client: AsyncClient):
        response = await client.get("/health")
        # Мы написали 21 правило
        assert response.json()["rules_loaded"] >= 15


# ---------------------------------------------------------------------------
# POST /analyze
# ---------------------------------------------------------------------------

MINIMAL_YAML = """\
image: python:3.12-slim

build:
  stage: build
  script:
    - echo hello
"""

BAD_YAML = """\
image: python:latest

variables:
  DB_PASSWORD: "supersecret"

build:
  script:
    - pip install -r requirements.txt
"""


class TestAnalyzeText:

    @pytest.mark.asyncio
    async def test_analyze_returns_201(self, client: AsyncClient):
        response = await client.post("/analyze/", json={"content": MINIMAL_YAML})
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_analyze_response_has_required_fields(self, client: AsyncClient):
        response = await client.post("/analyze/", json={"content": MINIMAL_YAML})
        data = response.json()
        assert "id" in data
        assert "filename" in data
        assert "created_at" in data
        assert "summary" in data
        assert "issues" in data

    @pytest.mark.asyncio
    async def test_analyze_summary_counts(self, client: AsyncClient):
        response = await client.post("/analyze/", json={"content": BAD_YAML})
        data = response.json()
        summary = data["summary"]
        # BAD_YAML должен триггерить минимум SEC001 и SEC002
        assert summary["total"] >= 2
        assert summary["error"] >= 1   # SEC001
        assert summary["warning"] >= 1  # SEC002

    @pytest.mark.asyncio
    async def test_analyze_issue_has_rule_id(self, client: AsyncClient):
        response = await client.post("/analyze/", json={"content": BAD_YAML})
        issues = response.json()["issues"]
        rule_ids = [i["rule_id"] for i in issues]
        assert "SEC001" in rule_ids
        assert "SEC002" in rule_ids

    @pytest.mark.asyncio
    async def test_analyze_clean_yaml_returns_empty_issues(self, client: AsyncClient):
        clean = """\
image: python:3.12-slim
stages: [build, test, deploy]

build:
  stage: build
  script: echo build

run-tests:
  stage: test
  script: pytest

deploy-staging:
  stage: deploy
  script: ./deploy.sh
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
  environment:
    name: staging
"""
        response = await client.post("/analyze/", json={"content": clean})
        data = response.json()
        # Может быть несколько INFO, но не должно быть ERROR
        errors = [i for i in data["issues"] if i["severity"] == "error"]
        assert errors == []

    @pytest.mark.asyncio
    async def test_analyze_invalid_yaml_returns_422(self, client: AsyncClient):
        response = await client.post("/analyze/", json={"content": "{\ninvalid: yaml: :"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_empty_content_returns_422(self, client: AsyncClient):
        response = await client.post("/analyze/", json={"content": ""})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_custom_filename(self, client: AsyncClient):
        response = await client.post(
            "/analyze/",
            json={"content": MINIMAL_YAML, "filename": "my-pipeline.yml"},
        )
        assert response.json()["filename"] == "my-pipeline.yml"


# ---------------------------------------------------------------------------
# GET /history
# ---------------------------------------------------------------------------

class TestHistory:

    @pytest.mark.asyncio
    async def test_history_empty_initially(self, client: AsyncClient):
        response = await client.get("/history")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_history_contains_analysis_after_run(self, client: AsyncClient):
        await client.post("/analyze/", json={"content": MINIMAL_YAML})
        response = await client.get("/history")
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_history_ordered_newest_first(self, client: AsyncClient):
        await client.post("/analyze/", json={"content": MINIMAL_YAML, "filename": "first.yml"})
        await client.post("/analyze/", json={"content": MINIMAL_YAML, "filename": "second.yml"})
        history = (await client.get("/history")).json()
        assert history[0]["filename"] == "second.yml"

    @pytest.mark.asyncio
    async def test_history_pagination(self, client: AsyncClient):
        for i in range(5):
            await client.post("/analyze/", json={"content": MINIMAL_YAML})
        response = await client.get("/history?limit=3&offset=0")
        assert len(response.json()) == 3


# ---------------------------------------------------------------------------
# GET /result/{id}
# ---------------------------------------------------------------------------

class TestGetResult:

    @pytest.mark.asyncio
    async def test_get_result_returns_full_issues(self, client: AsyncClient):
        post = await client.post("/analyze/", json={"content": BAD_YAML})
        analysis_id = post.json()["id"]

        response = await client.get(f"/result/{analysis_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) > 0

    @pytest.mark.asyncio
    async def test_get_result_not_found(self, client: AsyncClient):
        response = await client.get("/result/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_result(self, client: AsyncClient):
        post = await client.post("/analyze/", json={"content": MINIMAL_YAML})
        analysis_id = post.json()["id"]

        delete_response = await client.delete(f"/result/{analysis_id}")
        assert delete_response.status_code == 204

        get_response = await client.get(f"/result/{analysis_id}")
        assert get_response.status_code == 404
