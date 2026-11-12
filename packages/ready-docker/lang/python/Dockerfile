# ready-docker Layer 2/3：lang/python（房屋框架）
#   python:3.12-slim-bookworm + /opt/venv + 分層 requirements + appuser(10001)
#
# 建置前必須先建好 core 層（建置次序：core → python → discord）：
#   docker build -t ready-stack/python:dev \
#     --build-arg CORE_IMAGE=ready-stack/core:dev \
#     -f lang/python/Dockerfile .
ARG CORE_IMAGE
FROM ${CORE_IMAGE} AS core

FROM python:3.12-slim-bookworm

ARG TZ=Asia/Hong_Kong
ARG APP_UID=10001
ARG APP_GID=10001

LABEL org.opencontainers.image.title="ready-stack/python" \
      org.opencontainers.image.description="Layer 2/3: Python 3.12 runtime layering on ready-stack core with /opt/venv, appuser(10001) and layered requirements" \
      org.opencontainers.image.source="https://github.com/anthemjelly/ready-stack" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=${TZ} \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    HOME=/home/appuser \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:${PATH}

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        tzdata \
    && ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime \
    && echo "${TZ}" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 與 core 層相同的 UID/GID 約定，確保掛載 /logs /config 時權限一致。
RUN groupadd --gid "${APP_GID}" appuser \
    && useradd -l --uid "${APP_UID}" --gid "${APP_GID}" \
        --create-home --home-dir /home/appuser --shell /bin/bash appuser \
    && install -d -o appuser -g appuser -m 0755 /app /logs /config

# 這一層的 FROM 是 python slim（不是 core），所以由 core 鏡像借用兩支腳本。
COPY --from=core /usr/local/bin/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY --from=core /usr/local/bin/entrypoint-base.sh /usr/local/bin/entrypoint-base.sh
RUN chmod 0755 /usr/local/bin/healthcheck.sh /usr/local/bin/entrypoint-base.sh

# 先只複製 requirements，令新增場景依賴時不用重裝 venv。
COPY lang/python/requirements/ /tmp/requirements/

RUN python -m venv "${VIRTUAL_ENV}" \
    && "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir -r /tmp/requirements/base.txt \
    && rm -rf /tmp/requirements \
    && chown -R appuser:appuser "${VIRTUAL_ENV}"

WORKDIR /app
# 用數字 UID 而唔係名：host 冇 appuser 時都一定解析到（hadolint DL3066）。
USER 10001:10001

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["/usr/local/bin/healthcheck.sh"]

ENTRYPOINT ["/usr/local/bin/entrypoint-base.sh"]
CMD ["sleep", "infinity"]
