#!/bin/sh
# ready-docker 共用 entrypoint（Layer 1：core）
#
# 契約：
#   1. /app/entrypoint.sh 存在且可執行 → 先交給場景初始化腳本（它要負責最後 exec "$@"）；
#   2. 否則直接 exec "$@"，即 Dockerfile 的 CMD / docker run 的參數。
#
# 保持 exec 形式可以讓應用程式成為 PID 1，正確收到 SIGTERM（docker stop 可以優雅結束）。
set -eu

if [ -x "/app/entrypoint.sh" ]; then
    exec /app/entrypoint.sh "$@"
fi

exec "$@"
