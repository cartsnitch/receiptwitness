FROM python:3.12-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS prod

WORKDIR /app
RUN adduser --system --group --uid 1000 app
COPY --from=build /install /usr/local
COPY src/ ./src/
COPY alembic.ini ./
COPY alembic/ ./alembic/

USER 1000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "cartsnitch_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
