#!/usr/bin/env bash
# webapi 端到端驗證：建置 -> 起 api+db -> health/CRUD -> 清理
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="$ROOT/packages/ready-python-docker-webapi"
cd "$DIR"

if [ ! -f .env ]; then
  cp .env.example .env
fi

API_PORT="$(grep -E '^API_PORT=' .env | head -n1 | cut -d= -f2 | tr -d '[:space:]' || true)"
API_PORT="${API_PORT:-8000}"
BASE="http://localhost:${API_PORT}"

# 解析 JSON 用：Windows Git Bash 的 python3 可能是 Microsoft Store stub，要試跑確認
PY="${PY:-}"
if [ -z "$PY" ]; then
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

cleanup() {
  echo "==> 清理容器與 volume"
  docker compose down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> 建置並啟動 api + db"
docker compose up -d --build

echo "==> 等待 readyz"
for _ in $(seq 1 60); do
  if curl -fsS "${BASE}/readyz" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
if ! curl -fsS "${BASE}/readyz" >/dev/null 2>&1; then
  echo "readyz 超時，api 日誌："
  docker compose logs api || true
  exit 1
fi

echo "==> 檢查 healthz"
curl -fsS "${BASE}/healthz"

echo "==> 建立 item"
CREATE_JSON="$(curl -fsS -X POST "${BASE}/api/v1/items" \
  -H 'Content-Type: application/json' \
  -d '{"name":"e2e-item","description":"created by e2e","price":9.99}')"
ITEM_ID="$(printf '%s' "$CREATE_JSON" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
echo "item id = ${ITEM_ID}"

echo "==> 讀取列表"
curl -fsS "${BASE}/api/v1/items" | "$PY" -c '
import json, sys
data = json.load(sys.stdin)
assert data["total"] >= 1, data
assert any(i["id"] for i in data["items"]), data
print("list ok, total =", data["total"])
'

echo "==> 讀取單筆"
curl -fsS "${BASE}/api/v1/items/${ITEM_ID}" | "$PY" -c '
import json, sys
item = json.load(sys.stdin)
assert item["name"] == "e2e-item", item
print("get ok")
'

echo "==> 更新"
curl -fsS -X PATCH "${BASE}/api/v1/items/${ITEM_ID}" \
  -H 'Content-Type: application/json' \
  -d '{"price":12.5}' | "$PY" -c '
import json, sys
item = json.load(sys.stdin)
assert abs(item["price"] - 12.5) < 1e-6, item
print("patch ok")
'

echo "==> 刪除"
CODE="$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "${BASE}/api/v1/items/${ITEM_ID}")"
[ "$CODE" = "204" ] || { echo "DELETE 期望 204，實際 $CODE"; exit 1; }

echo "==> 確認已刪除"
CODE="$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/api/v1/items/${ITEM_ID}")"
[ "$CODE" = "404" ] || { echo "GET 已刪除 item 期望 404，實際 $CODE"; exit 1; }

echo "e2e 全部通過"
