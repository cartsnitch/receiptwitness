# Stage 1: Build dependencies
FROM python:3.12-slim AS build

WORKDIR /app

# git is required to install cartsnitch-common from GitHub; build-essential and
# libpq-dev are needed to compile any C-extension wheels (e.g. psycopg2 fallback)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/

# cartsnitch-common is not on PyPI — install it directly from GitHub, then
# install the rest of the package dependencies in a single resolver pass so
# pip can satisfy the cartsnitch-common>=0.1.0 constraint declared in
# pyproject.toml without hitting PyPI for it.
RUN pip install --no-cache-dir --prefix=/install \
    "cartsnitch-common @ git+https://github.com/cartsnitch/common.git@76685ed0384103228cd670b477b967e7752ebe6b" \
    .

# Stage 2: Production image with Playwright + Chromium
FROM python:3.12-slim AS prod

WORKDIR /app

# Install Playwright system dependencies for Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Install Playwright Chromium browser (runs as root; /opt/playwright is world-readable)
RUN PLAYWRIGHT_BROWSERS_PATH=/opt/playwright playwright install chromium

ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

USER 1000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "receiptwitness.main:app", "--host", "0.0.0.0", "--port", "8000"]
