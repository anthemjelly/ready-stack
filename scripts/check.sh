#!/usr/bin/env bash
# 本地品質檢查（對應 Makefile 的 make check）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PY:-}"
if [ -z "$PY" ]; then
  # Windows Git Bash 的 python3 可能是 Microsoft Store stub，要實際試跑先算數
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys' >/dev/null 2>&1; then
      PY="$candidate"
      break
    fi
  done
fi
if [ -z "$PY" ]; then
  echo "找不到可用的 Python（python3 / python）" >&2
  exit 1
fi
VENV="$ROOT/.venv"

if [ ! -d "$VENV" ]; then
  echo "==> 建立 .venv"
  "$PY" -m venv "$VENV"
fi
# shellcheck disable=SC1091
. "$VENV/bin/activate"

python -m pip install --upgrade pip --quiet
python -m pip install --quiet -e "packages/ready-python[dev]" -e "packages/ready-python-docker-webapi[dev]"

echo "==> ruff check"
ruff check packages
echo "==> ruff format --check"
ruff format --check packages
echo "==> pyright"
(cd packages/ready-python && pyright --pythonpath "$VENV/bin/python")
(cd packages/ready-python-docker-webapi && pyright --pythonpath "$VENV/bin/python")
echo "==> pytest"
(cd packages/ready-python && pytest -q)
(cd packages/ready-python-docker-webapi && pytest -q)

echo "全部檢查通過"
