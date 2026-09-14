FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    BUI_RUNTIME_STATE=/app/data/runtime/state.json

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY config ./config
COPY knowledge ./knowledge
COPY scripts ./scripts
COPY data/README.md ./data/README.md

RUN pip install --upgrade pip && pip install ".[live,osm]" \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data/runtime /app/data/generated \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

CMD ["uvicorn", "berlin_urban_intelligence.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
