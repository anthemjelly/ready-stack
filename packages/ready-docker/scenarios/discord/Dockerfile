# ready-docker Layer 3/3：scenarios/discord（裝修好的房）
#   繼承 lang/python 的 /opt/venv 與 appuser，加裝 discord.py / deep-translator / python-dotenv，
#   執行 app.main。bot 是長連線，不需要對外端口。
#
# 建置前必須先建好 python 層（建置次序：core → python → discord）：
#   docker build -t ready-stack/discord:dev \
#     --build-arg PYTHON_IMAGE=ready-stack/python:dev \
#     -f scenarios/discord/Dockerfile .
ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}

LABEL org.opencontainers.image.title="ready-stack/discord" \
      org.opencontainers.image.description="Layer 3/3: Discord translation bot scenario on ready-stack python layer (discord.py + deep-translator + python-dotenv)" \
      org.opencontainers.image.source="https://github.com/anthemjelly/ready-stack" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# 先裝場景依賴，再複製程式碼：改 app/ 不會令 pip 層 cache 失效。
COPY --chown=appuser:appuser scenarios/discord/requirements.txt /opt/ready-docker/requirements.txt

# 用數字 UID 而唔係名：host 冇 appuser 時都一定解析到（hadolint DL3066）。
USER 10001:10001

RUN /opt/venv/bin/pip install --no-cache-dir -r /opt/ready-docker/requirements.txt

COPY --chown=appuser:appuser scenarios/discord/app /app/app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["/usr/local/bin/healthcheck.sh"]

ENTRYPOINT ["/usr/local/bin/entrypoint-base.sh"]
CMD ["python", "-m", "app.main"]
