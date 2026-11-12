# syntax=docker/dockerfile:1

# =============================================================================
# builder：安裝 build 工具鏈，將 package 裝入 /opt/venv
# =============================================================================
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv "$VIRTUAL_ENV"

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# =============================================================================
# runtime：只帶 venv 同 appuser，冇編譯器、冇 pip cache
# =============================================================================
FROM python:3.12-slim-bookworm AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

LABEL org.opencontainers.image.title="ready-python" \
      org.opencontainers.image.description="ready-stack 的 Python 專案起手模板 CLI" \
      org.opencontainers.image.source="https://github.com/anthemjelly/ready-stack" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    HOME=/home/appuser

COPY --from=builder /opt/venv /opt/venv

RUN groupadd --gid "${APP_GID}" appuser \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" \
        --create-home --home-dir /home/appuser --shell /usr/sbin/nologin appuser

USER ${APP_UID}:${APP_GID}
WORKDIR /home/appuser

# 用 shell form 先可以帶 `|| exit 1`；DL3025 本來只針對 CMD / ENTRYPOINT，對 HEALTHCHECK 係誤報。
# hadolint ignore=DL3025
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ready-python --version || exit 1

ENTRYPOINT ["ready-python"]
CMD ["--help"]
