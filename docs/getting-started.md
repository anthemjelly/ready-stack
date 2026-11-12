# 由零開始（Getting Started）

## 前置條件

| 工具 | 版本 | 備註 |
|------|------|------|
| Docker Desktop / Engine | 24+，Compose v2 | Windows 用 Docker Desktop + WSL2 |
| Python | 3.12+ | 本地跑 lint / test 用；容器內已固定 3.12 |
| Git | 2.40+ | |
| make | 可選 | Windows 可以用 `scripts/*.ps1` 代替 |

## 1. 取得專案

```bash
git clone https://github.com/anthemjelly/ready-stack.git
cd ready-stack
```

## 2. 本地品質檢查

```bash
make install     # 建立 .venv，editable 安裝兩個 Python 套件 + dev 依賴
make check       # ruff check + ruff format --check + pyright + pytest
```

Windows PowerShell：

```powershell
.\scripts\check.ps1 -Install
```

## 3. 建置 Docker 映像（ready-docker 三層 + 兩個應用映像）

```bash
make docker-build
# 等價於
bash scripts/build-all.sh
```

建置完成後應該有：

```
ready-stack/core:dev
ready-stack/python:dev
ready-stack/discord:dev
ready-stack/ready-python:dev
ready-stack/webapi:dev
```

## 4. 起一套 FastAPI + PostgreSQL 並驗證

```bash
make e2e
```

腳本會：建置 webapi 映像 → `docker compose up -d` → 等 `/readyz` 通過 →
POST 一筆 item → GET 列表 → GET 單筆 → PATCH → DELETE → `docker compose down -v`。

手動版：

```bash
cd packages/ready-python-docker-webapi
cp .env.example .env          # 需要時改入面的 POSTGRES_PASSWORD
docker compose up -d --build
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl -X POST http://localhost:8000/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{"name":"demo","description":"hello","price":9.99}'
```

> 呢個套件用 `.env` 傳 DB 密碼（`POSTGRES_PASSWORD`），沒有 Docker secret 檔。
> Production 建議改用 Docker secrets 或外部 secret manager，見 `docs/conventions.md`。

## 5. 用 `ready-python` 開一個新專案

```bash
# 方法一：直接複製資料夾
cp -r packages/ready-python ../my-new-project
cd ../my-new-project
rm -rf .git
git init -b main

# 方法二（推薦）：先建立空 repo，再用 rsync 同步
gh repo create my-new-project --private --clone
rsync -a packages/ready-python/ ../my-new-project/
```

之後把 `pyproject.toml` 內的 `name`、`src/ready_python/`、tests 改成你的專案名。

## 6. 用 `ready-docker` 加一個新語言／新場景

加語言層（例：Node.js）：

1. 建立 `packages/ready-docker/lang/nodejs/Dockerfile`，`FROM ${CORE_IMAGE}`；
2. 在 `scripts/build-all.sh` 加入建置步驟；
3. 更新 `docs/conventions.md` 與該套件 README。

加場景：複製 `scenarios/discord/` 为 `scenarios/<你的場景>/`，改 Dockerfile 與 app。

## 常見問題

| 症狀 | 解法 |
|------|------|
| `docker compose up` 話 `db` unhealthy | 等 10–30 秒；`docker compose logs db` 看 PostgreSQL 初始化 |
| webapi 容器即刻退出 | `docker compose logs api`；多數是 migration 失敗或 DB 連不上 |
| 本機 5432 被佔用 | `DB_PORT=5433 docker compose up` |
| Windows 上 `make` 唔存在 | 用 `.\scripts\check.ps1`、`.\scripts\build-all.ps1`、`.\scripts\e2e-webapi.ps1` |
