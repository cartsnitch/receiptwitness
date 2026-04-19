# Stage 1: Build dependencies
FROM python:3.12-slim AS build

WORKDIR /app

ARG APT_CACHE_BUST=1
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Build context is the receiptwitness repo root.
COPY pyproject.toml ./
COPY src/ ./src/

# Install receiptwitness (shared modules are inlined under src/receiptwitness/shared/).
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Production image with Playwright + Chromium
FROM python:3.12-slim AS prod

WORKDIR /app

# Install Playwright system dependencies for Chromium
ARG APT_CACHE_BUST=1
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --system --group --uid 1000 app

COPY --from=build /install /usr/local
COPY src/ ./src/
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Install Playwright Chromium browser (runs as root; /opt/playwright is world-readable)
RUN PLAYWRIGHT_BROWSERS_PATH=/opt/playwright playwright install chromium

ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

USER 1000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn receiptwitness.main:app --host 0.0.0.0 --port 8000"]
