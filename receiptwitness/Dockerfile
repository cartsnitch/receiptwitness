# Stage 1: Build dependencies
FROM python:3.12-slim AS build

WORKDIR /app

# build-essential and libpq-dev are needed to compile any C-extension wheels
# (e.g. psycopg2 fallback).  No git needed — common/ is copied from the repo root.
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Build context is the repo root.  These paths are relative to the root.
COPY receiptwitness/pyproject.toml ./
COPY receiptwitness/src/ ./src/
COPY common/ ./common/

# Install from the local common/ (cartsnitch-common>=0.1.0 in pyproject.toml
# will be satisfied by the local package) then install receiptwitness itself.
RUN pip install --no-cache-dir --prefix=/install ./common/ .

# Stage 2: Production image with Playwright + Chromium
FROM python:3.12-slim AS prod

WORKDIR /app

# Install Playwright system dependencies for Chromium
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
COPY receiptwitness/src/ ./src/

# Install Playwright Chromium browser (runs as root; /opt/playwright is world-readable)
RUN PLAYWRIGHT_BROWSERS_PATH=/opt/playwright playwright install chromium

ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

USER 1000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "receiptwitness.main:app", "--host", "0.0.0.0", "--port", "8000"]
