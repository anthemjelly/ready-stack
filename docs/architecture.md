# 架構（Architecture）

## 1. 為什麼是 monorepo

原本三個專案（`ready-docker`、`ready-python-docker-webapi`，加上一直未建立的 `ready-python`）各自
重複了同一堆東西：Python 版本、ruff/pyright 設定、Dockerfile 的多階段寫法、UID/GID、healthcheck、
compose 的 restart/logging 設定。三份 copy 一齊改，最後一定走樣。

改成 monorepo 之後：

- **一份 conventions**（`docs/conventions.md`）約束三個套件；
- **一套 CI** 同時驗證三個套件；
- 三個套件仍然是獨立可複製的資料夾，用完可以單獨拎出去做新專案。

## 2. 元件關係

```
┌──────────────────────────────────────────────────────────────┐
│ ready-python-docker-webapi（實際服務）                        │
│  FastAPI app → SQLAlchemy(async) → PostgreSQL                │
│  Dockerfile：python:3.12-slim-bookworm 多階段                 │
└───────────────────────────────┬──────────────────────────────┘
                                │ 沿用同一套規範（UID/GID、healthcheck、compose 模式）
┌───────────────────────────────▼──────────────────────────────┐
│ ready-docker（容器工具箱）                                    │
│  core（debian + 工具 + appuser）                              │
│    → lang/python（python:3.12-slim + venv + 依賴）            │
│      → scenarios/discord（示範場景）                          │
└───────────────────────────────┬──────────────────────────────┘
                                │ 建置／執行慣例
┌───────────────────────────────▼──────────────────────────────┐
│ ready-python（Python 專案模板）                               │
│  src layout + pyproject + ruff/pyright/pytest + Dockerfile    │
└──────────────────────────────────────────────────────────────┘
```

三者是「同層工具箱」而不是嚴格的編譯依賴：每個都可以單獨使用；放在同一個 repo 是因為共用規範與 CI。

## 3. ready-docker 的三層模型

| 層 | 內容 | 類比 |
|----|------|------|
| `core/` | Debian bookworm-slim、ca-certificates、curl、git、tzdata、`appuser`、healthcheck／entrypoint 腳本 | 地基 |
| `lang/python/` | 基於 core 的 Python 3.12 執行環境 + `/opt/venv` + 分層 requirements | 房屋框架 |
| `scenarios/discord/` | 基於 lang/python、安裝 `discord.py` + `deep-translator`、跑 `app/main.py` | 裝修好的房 |

建置次序很重要：`core` → `lang/python` → `scenarios/discord`。
`lang/python` 與 `scenarios/*` 的 Dockerfile 都接受 `ARG BASE_IMAGE`／`ARG CORE_IMAGE`，
由建置腳本逐層傳入，避免「FROM 一個未存在的 image」這個經典陷阱。

## 4. webapi 的請求流程

```
HTTP → uvicorn → FastAPI router (/api/v1/items)
                 → Pydantic schema 驗證
                 → deps.get_session（async session）
                 → SQLAlchemy model → PostgreSQL
                 → Pydantic response model → JSON
```

- `/healthz`：liveness，不碰 DB。
- `/readyz`：readiness，執行 `SELECT 1` 確認 DB 可用。
- `/api/v1/items`：POST / GET(list, pagination) / GET(id) / PATCH / DELETE。
- 啟動時用 Alembic 建表（`RUN_MIGRATIONS=true` 時由 entrypoint 執行）。

## 5. 資源與端口

| 服務 | 容器端口 | 宿主端口 | 備註 |
|------|----------|----------|------|
| webapi | 8000 | `${API_PORT:-8000}` | FastAPI / uvicorn |
| postgres | 5432 | `${DB_PORT:-5432}` | 只在需要本機連 DB 時映射 |
| Discord bot | — | — | 長連線，不需要端口 |

## 6. 與舊 repo 的關係

- `anthemjelly/ready-docker`：概念來源，內容已整理進 `packages/ready-docker`。
- `anthemjelly/ready-python-docker-webapi`：骨架來源，內容已由 `packages/ready-python-docker-webapi` 取代。
- 舊 repo 保留唯讀歷史；新功能一律在 `ready-stack` 開發。
