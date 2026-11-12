# syntax=docker/dockerfile:1
# 多階段建置：builder 建 /opt/venv 並安裝套件；runtime 只複製 venv 與應用程式碼。

# ---------- builder ----------
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# ---------- runtime ----------
FROM python:3.12-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="ready-python-docker-webapi" \
      org.opencontainers.image.description="FastAPI + async SQLAlchemy + PostgreSQL 示範服務（ready-stack）" \
      org.opencontainers.image.source="https://github.com/anthemjelly/ready-stack" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:${PATH}" \
    HOME=/home/appuser

# 非 root 執行用戶（與 docs/conventions.md 一致的 UID/GID 10001）。
ARG UID=10001
ARG GID=10001
RUN groupadd --gid "${GID}" appuser \
    && useradd --uid "${UID}" --gid "${GID}" \
        --create-home --home-dir /home/appuser --shell /bin/bash appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser docker/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod 0755 /usr/local/bin/entrypoint.sh

# 用數值 UID/GID 執行（比 `USER appuser` 更明確，亦避免 hadolint DL3066）。
USER 10001:10001

EXPOSE 8000

# 用標準庫 urllib 打 /healthz，runtime 唔需要 curl。
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
