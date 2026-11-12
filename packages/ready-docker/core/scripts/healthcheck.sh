#!/bin/sh
# ready-docker 共用健康檢查（Layer 1：core）
#
# 契約：
#   /app/healthcheck 存在且可執行 → 交場景自訂腳本判斷（exit 0 = healthy、非 0 = unhealthy）；
#   否則 core 層沒有應用級檢查，印一行提示並視為 healthy。
#
# Docker HEALTHCHECK 語義：exit 0 = 健康、exit 1 = 不健康。
set -eu

if [ -x "/app/healthcheck" ]; then
    exec /app/healthcheck
fi

echo "ready-docker: /app/healthcheck 未提供，core 層沒有應用級健康檢查（預設 healthy）" >&2
exit 0
