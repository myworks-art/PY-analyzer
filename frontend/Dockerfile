FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY analyzer/ ./analyzer/
COPY api/      ./api/

RUN mkdir -p /app/data /app/logs && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
