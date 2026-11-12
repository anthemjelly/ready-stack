# ready-docker Layer 1/3：core（地基）
#   Debian bookworm-slim + 基礎工具 + appuser(10001) + 共用 healthcheck/entrypoint 腳本
#
# 建置（build context 必須是 packages/ready-docker，不是 core/）：
#   docker build -t ready-stack/core:dev -f core/Dockerfile .
FROM debian:bookworm-slim

ARG TZ=Asia/Hong_Kong
ARG APP_UID=10001
ARG APP_GID=10001

LABEL org.opencontainers.image.title="ready-stack/core" \
      org.opencontainers.image.description="Layer 1/3: Debian bookworm-slim base with curl, ca-certificates, tzdata, git, appuser(10001) and shared healthcheck/entrypoint scripts" \
      org.opencontainers.image.source="https://github.com/anthemjelly/ready-stack" \
      org.opencontainers.image.licenses="MIT"

ENV TZ=${TZ} \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    HOME=/home/appuser

# 時區與基礎工具。apt lists 即裝即刪，避免鏡像變大（DL3009）。
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        tzdata \
    && ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime \
    && echo "${TZ}" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 非 root 執行用戶；-l 避免 uid > 999 時 lastlog 產生巨大 sparse file（DL3046）。
RUN groupadd --gid "${APP_GID}" appuser \
    && useradd -l --uid "${APP_UID}" --gid "${APP_GID}" \
        --create-home --home-dir /home/appuser --shell /bin/bash appuser \
    && install -d -o appuser -g appuser -m 0755 /app /logs /config

# 共用腳本：entrypoint-base.sh（PID 1 轉發）與 healthcheck.sh（Docker HEALTHCHECK 入口）。
COPY core/scripts/*.sh /usr/local/bin/
RUN chmod 0755 /usr/local/bin/entrypoint-base.sh /usr/local/bin/healthcheck.sh

WORKDIR /app
# 用數字 UID 而唔係名：host 冇 appuser 時都一定解析到（hadolint DL3066）。
USER 10001:10001

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["/usr/local/bin/healthcheck.sh"]

ENTRYPOINT ["/usr/local/bin/entrypoint-base.sh"]
CMD ["sleep", "infinity"]
