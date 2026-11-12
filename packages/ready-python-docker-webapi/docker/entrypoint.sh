#!/bin/sh
# 容器啟動入口：等 PostgreSQL 就緒 ->（可選）執行 Alembic migration -> 交棒給 CMD。
set -eu

echo "[entrypoint] 等待 PostgreSQL 就緒..."
python -m app.db.wait

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "[entrypoint] 執行 alembic upgrade head"
  alembic upgrade head
else
  echo "[entrypoint] RUN_MIGRATIONS=${RUN_MIGRATIONS:-false}，跳過 migration"
fi

exec "$@"
