# ready-python-docker-webapi

ready-stack 的**實戰 FastAPI 服務範本**：不是空殼，而是一套可以直接 `docker compose up`
起機、有 PostgreSQL、有 migration、有測試、有 e2e 驗證的 API 服務。
三個套件共用同一份規範（見 repo 根 `docs/conventions.md`），呢個 package 可以單獨複製出去做新專案。

```
HTTP → uvicorn → FastAPI router (/api/v1/items)
                 → Pydantic v2 驗證
                 → get_session（async session）
                 → SQLAlchemy 2.0 model → PostgreSQL
                 → Pydantic response model → JSON
```

## 功能

- **Items CRUD**：POST / GET（分頁）/ GET by id / PATCH / DELETE
- **健康檢查**：`/healthz`（liveness，不碰 DB）、`/readyz`（readiness，執行 `SELECT 1`）
- **非同步資料層**：SQLAlchemy 2.0 async + asyncpg（生產）、aiosqlite（測試）
- **Migration**：Alembic（容器啟動時可自動 `upgrade head`）
- **設定**：pydantic-settings，`.env` + 環境變數
- **分頁合約**：`{"items": [...], "total": N, "limit": N, "offset": N}`
- **Docker**：多階段建置、非 root（UID/GID `10001`）、內建 HEALTHCHECK
- **品質**：ruff（line-length 100）、pyright（standard, py312）、pytest（30 個測試，無需網絡）

## 技術棧

| 層 | 選用 |
|----|------|
| Web | FastAPI 0.115+、uvicorn[standard] |
| 驗證 | Pydantic v2、pydantic-settings |
| DB | PostgreSQL 18、SQLAlchemy 2.0 async、asyncpg |
| Migration | Alembic |
| 測試 | pytest、pytest-asyncio、httpx、aiosqlite |
| Lint / 型別 | ruff、pyright |
| 容器 | python:3.12-slim-bookworm、docker compose |

## 快速開始（Docker Compose）

前置：Docker Desktop / Docker Engine + Compose v2。

```bash
cd packages/ready-python-docker-webapi
cp .env.example .env          # 只供開發用；真密碼不要 commit
docker compose up -d --build
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
```

預期輸出：

```json
{"status":"ok"}
{"status":"ready","database":"ok"}
```

建立一筆資料：

```bash
curl -X POST http://localhost:8000/api/v1/items \
  -H 'Content-Type: application/json' \
  -d '{"name":"demo","description":"hello","price":9.99}'
```

互動式 API 文件：<http://localhost:8000/docs>（Swagger UI）、<http://localhost:8000/redoc>。

收工：

```bash
docker compose down -v --remove-orphans   # -v 會一併刪 DB volume
```

如果本機 5432 已被佔用：`DB_PORT=5433 docker compose up -d`（只影響宿主機映射，容器內仍用 5432）。

## 本地開發（不用 Docker 跑 API）

前置：Python 3.12+，以及一個可連的 PostgreSQL（最簡單：`docker compose up -d db`）。

```bash
cd packages/ready-python-docker-webapi
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"

cp .env.example .env
# 本機直接跑 uvicorn 時，DB 在主機的 localhost（compose 只會覆寫容器內的設定）
export POSTGRES_HOST=localhost       # Windows PowerShell: $env:POSTGRES_HOST="localhost"

alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或者用 Makefile（POSIX shell）：

```bash
make install     # 建 .venv + pip install -e ".[dev]"
make migrate     # alembic upgrade head
make run         # uvicorn（POSTGRES_HOST 預設 localhost）
```

## API 一覽

| Method | Path | 說明 | 成功狀態碼 |
|--------|------|------|-----------|
| GET | `/healthz` | liveness，不碰 DB | 200 |
| GET | `/readyz` | readiness，執行 `SELECT 1`；DB 失敗回 503 | 200 / 503 |
| POST | `/api/v1/items` | 新增 item | 201 |
| GET | `/api/v1/items?limit=20&offset=0` | 列表（`limit` 1–100，`offset` ≥ 0） | 200 |
| GET | `/api/v1/items/{id}` | 讀取單筆；不存在回 404 | 200 |
| PATCH | `/api/v1/items/{id}` | 局部更新（所有欄位選填） | 200 |
| DELETE | `/api/v1/items/{id}` | 刪除；重複刪除回 404 | 204 |

範例：

```bash
# 列表：回應形狀固定為 {items,total,limit,offset}
curl 'http://localhost:8000/api/v1/items?limit=2&offset=0'

# 讀取
curl http://localhost:8000/api/v1/items/1

# 局部更新（只改價格）
curl -X PATCH http://localhost:8000/api/v1/items/1 \
  -H 'Content-Type: application/json' -d '{"price":12.5}'

# 刪除（204，無 body）
curl -i -X DELETE http://localhost:8000/api/v1/items/1

# 刪除後再讀 → 404
curl -i http://localhost:8000/api/v1/items/1
```

`price` 以 **JSON number** 輸出（例如 `9.99`），不是字串；資料庫存的是 `numeric(10,2)`。

## 資料模型：`items`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `id` | bigint identity PK | 自增 |
| `name` | varchar(100) not null | 有 index |
| `description` | varchar(500) null | 可為空 |
| `price` | numeric(10,2) not null | ≥ 0 |
| `created_at` | timestamptz not null | `server_default now()` |
| `updated_at` | timestamptz not null | `server_default now()`、UPDATE 時自動更新 |

## Migration（Alembic）

```bash
alembic upgrade head            # 套用到最新版
alembic downgrade -1            # 回滾一個版本
alembic history                 # 版本歷史
alembic current                 # 目前版本
alembic revision --autogenerate -m "add users"   # 改完 model 後產生新 migration
```

- DSN 由 `app.core.config` 讀取（`alembic/env.py`），`alembic.ini` 內**不存密碼**。
- 目前版本：`0001_create_items`。
- 容器內：`RUN_MIGRATIONS=true`（預設）時，entrypoint 會先 `alembic upgrade head` 再起 uvicorn。

## 測試與品質檢查

```bash
pytest -q                 # 30 個測試：health、readyz 503、items CRUD、404、422、分頁
ruff check .
ruff format --check .
pyright                   # standard / python 3.12
```

測試用 SQLite + aiosqlite，每個 test 一個暫存 DB 檔，**不需要 PostgreSQL、不需要網絡**。
本機 `pyright` 會自動用 `.venv`（`pyproject.toml` 已設 `venvPath`/`venv`）。

## 端到端驗證（e2e）

在 repo 根目錄：

```bash
bash scripts/e2e-webapi.sh          # Linux/macOS/WSL/Git Bash
pwsh -File scripts/e2e-webapi.ps1   # Windows PowerShell
```

腳本會：建置 webapi image → `docker compose up -d --build` → 等 `/readyz` →
healthz → POST → list → GET → PATCH（price 12.5）→ DELETE（204）→ GET（404）→ `down -v` 清理。

## 設定（環境變數）

| 變數 | 預設 | 說明 |
|------|------|------|
| `API_PORT` | `8000` | 宿主機映射到容器 8000 的端口（compose） |
| `DB_PORT` | `5432` | 宿主機映射到 PostgreSQL 的端口（compose） |
| `POSTGRES_USER` | `webapi` | DB 使用者 |
| `POSTGRES_PASSWORD` | `webapi` | DB 密碼（`.env.example` 為假值，正式環境務必更換） |
| `POSTGRES_DB` | `webapi` | DB 名稱 |
| `POSTGRES_HOST` | `localhost` | DB 主機；compose 內強制為 `db` |
| `POSTGRES_PORT` | `5432` | DB 端口（容器內） |
| `DATABASE_URL` | 空 | 完整 async DSN，設定後覆寫上述組合；接受 `postgresql://` / `postgresql+asyncpg://` |
| `ENVIRONMENT` | `development` | 環境名稱（只影響日誌） |
| `LOG_LEVEL` | `INFO` | 日誌等級 |
| `RUN_MIGRATIONS` | `true` | 容器啟動時是否自動 migration |
| `CORS_ORIGINS` | `http://localhost:8000,http://localhost:3000` | 逗號分隔的允許 origin |
| `DB_WAIT_MAX_ATTEMPTS` | `30` | entrypoint 等 DB 的最多重試次數 |
| `DB_WAIT_DELAY_SECONDS` | `2` | 每次重試間隔（秒） |

> 安全：`.env` 已在 `.gitignore`；只提交 `.env.example`。不要把真密碼寫入 repo 或 image。

## 專案結構

```
packages/ready-python-docker-webapi/
├── app/
│   ├── __init__.py            # __version__
│   ├── main.py                # create_app() + lifespan + CORS
│   ├── api/routes/
│   │   ├── health.py          # /healthz、/readyz
│   │   └── items.py           # /api/v1/items CRUD
│   ├── core/
│   │   ├── config.py          # pydantic-settings（Settings）
│   │   └── logging.py         # dictConfig
│   ├── db/
│   │   ├── base.py            # DeclarativeBase
│   │   ├── session.py         # async engine / sessionmaker / get_session
│   │   └── wait.py            # python -m app.db.wait（entrypoint 用）
│   ├── models/item.py         # items 表
│   └── schemas/item.py        # ItemCreate/Update/Read/List
├── alembic/                   # env.py + versions/0001_create_items.py
├── alembic.ini
├── docker/entrypoint.sh       # 等 DB → migration → exec CMD
├── tests/                     # conftest + test_health + test_items
├── compose.yml                # api + postgres:18-alpine + volume + network
├── Dockerfile                 # 多階段、非 root 10001、HEALTHCHECK
├── .devcontainer/devcontainer.json
├── .env.example
├── .dockerignore
├── Makefile
└── pyproject.toml
```

## 容器設計

- **多階段**：builder 建 `/opt/venv` 並 `pip install .`；runtime 只帶 venv + `app`/`alembic`，不含編譯器。
- **非 root**：`appuser` UID/GID `10001`，`HOME=/home/appuser`。
- **entrypoint 流程**：`python -m app.db.wait` →（`RUN_MIGRATIONS=true`）`alembic upgrade head` → `exec uvicorn ...`。
- **HEALTHCHECK**：用 venv 內的 `python -c` 打 `http://127.0.0.1:8000/healthz`，runtime 不需要 curl。
- **compose**：`api` (`restart: unless-stopped`) + `db` (`restart: always`)，DB healthcheck 用 `pg_isready`，
  `depends_on: condition: service_healthy`；資源限制與 json-file 日誌輪替都已設定。
- **PostgreSQL 18 volume**：官方 image 的 PGDATA 在 `/var/lib/postgresql/<major>/docker`，
  所以 volume 掛 `/var/lib/postgresql`（不是舊教學的 `/var/lib/postgresql/data`）。

## 常見問題

| 症狀 | 處理 |
|------|------|
| `readyz` 一直 503 | `docker compose logs db` 看 PostgreSQL 是否 healthy；`docker compose logs api` 看 migration 錯誤 |
| api 容器即刻退出 | 多數是 migration 失敗或 DSN 錯；檢查 `docker compose logs api` |
| 本機 5432 被佔用 | `DB_PORT=5433 docker compose up -d` |
| 本機跑 uvicorn 連不到 DB | `.env` 的 `POSTGRES_HOST` 要改 `localhost`（compose 內才是 `db`） |
| `make` 在 Windows 不可用 | 用 Git Bash / WSL，或直接跑 README 內的 PowerShell 指令 |
| pyright 找不到套件 | 確認在 package 目錄、`.venv` 已建立並 `pip install -e ".[dev]"` |

## 授權

MIT（見 repo 根 `LICENSE`）。與 repo 根 `docs/conventions.md` 的規範保持一致。
