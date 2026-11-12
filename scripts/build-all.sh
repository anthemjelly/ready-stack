#!/usr/bin/env bash
# 依序建置所有 Docker 映像：core -> python -> discord -> ready-python -> webapi
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${TAG:-dev}"
CORE_IMAGE="ready-stack/core:${TAG}"
PYTHON_IMAGE="ready-stack/python:${TAG}"
DISCORD_IMAGE="ready-stack/discord:${TAG}"

build() {
  local label="$1"; shift
  echo "==> 建置 ${label}"
  docker build "$@"
}

build "core" \
  -t "$CORE_IMAGE" \
  -f "$ROOT/packages/ready-docker/core/Dockerfile" \
  "$ROOT/packages/ready-docker"

build "lang/python" \
  -t "$PYTHON_IMAGE" \
  --build-arg CORE_IMAGE="$CORE_IMAGE" \
  -f "$ROOT/packages/ready-docker/lang/python/Dockerfile" \
  "$ROOT/packages/ready-docker"

build "scenarios/discord" \
  -t "$DISCORD_IMAGE" \
  --build-arg PYTHON_IMAGE="$PYTHON_IMAGE" \
  -f "$ROOT/packages/ready-docker/scenarios/discord/Dockerfile" \
  "$ROOT/packages/ready-docker"

build "ready-python" \
  -t "ready-stack/ready-python:${TAG}" \
  "$ROOT/packages/ready-python"

build "webapi" \
  -t "ready-stack/webapi:${TAG}" \
  "$ROOT/packages/ready-python-docker-webapi"

echo "全部映像建置完成（TAG=${TAG}）"
