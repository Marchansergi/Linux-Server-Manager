# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project && rm /usr/local/bin/uv
COPY backend/app ./app
COPY --from=frontend /build/dist ./frontend

RUN useradd --system --uid 10001 --no-create-home lsm \
    && mkdir /data && chown lsm:lsm /data
USER lsm

ENV LSM_DATABASE_URL=sqlite:////data/lsm.db \
    LSM_FRONTEND_DIST=/app/frontend

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)"]
CMD ["uvicorn", "--factory", "app.main:build_app", "--host", "0.0.0.0", "--port", "8000"]
