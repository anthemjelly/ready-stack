#!/usr/bin/env bash
# 驗證所有 compose 檔（CI 與本地共用）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WEBAPI="packages/ready-python-docker-webapi"
READY_DOCKER="packages/ready-docker"

if [ -f "$WEBAPI/.env.example" ] && [ ! -f "$WEBAPI/.env" ]; then
  cp "$WEBAPI/.env.example" "$WEBAPI/.env"
fi

echo "==> 驗證 $WEBAPI/compose.yml"
docker compose -f "$WEBAPI/compose.yml" config -q

if [ -f "$READY_DOCKER/compose.yml" ]; then
  if [ -f "$READY_DOCKER/.env.example" ] && [ ! -f "$READY_DOCKER/.env" ]; then
    cp "$READY_DOCKER/.env.example" "$READY_DOCKER/.env"
  fi
  echo "==> 驗證 $READY_DOCKER/compose.yml"
  docker compose -f "$READY_DOCKER/compose.yml" config -q
fi

echo "compose 檔全部通過"
