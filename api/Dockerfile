# Stage 1: Build dependencies
# Build context is the repo root.  Paths below are relative to the root.
FROM python:3.12-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY api/pyproject.toml ./
COPY api/src/ ./src/
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Production image
FROM python:3.12-slim AS prod

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN adduser --system --group --uid 1000 app
COPY --from=build /install /usr/local
COPY api/src/ ./src/
COPY api/alembic.ini ./
COPY api/alembic/ ./alembic/

USER 1000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn cartsnitch_api.main:app --host 0.0.0.0 --port 8000"]