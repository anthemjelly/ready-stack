# ready-stack

[![CI](https://github.com/anthemjelly/ready-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/anthemjelly/ready-stack/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一套「開箱即用」的 Python × Docker 專案工具箱。把原本三個各自做到一半的專案整合成一個 monorepo，
共用同一套 Python / Docker / CI 規範，由「起手模板」到「真正可運行的 API 服務」一次過覆蓋。

## 三個套件

| 套件 | 定位 | 你會得到 |
|------|------|----------|
| [`packages/ready-python`](packages/ready-python/README.md) | Python 專案起手模板 | src layout、pyproject、ruff / pyright / pytest、pre-commit、devcontainer、多階段 Dockerfile、Makefile、CI |
| [`packages/ready-docker`](packages/ready-docker/README.md) | 分層 Docker 工具箱 | `core` → `lang/python` → `scenarios/discord` 三層鏡像、有序建置腳本、版本 tag、healthcheck / entrypoint 規範 |
| [`packages/ready-python-docker-webapi`](packages/ready-python-docker-webapi/README.md) | 實戰 FastAPI 服務模板 | async SQLAlchemy + Alembic + Pydantic v2、`/healthz` `/readyz`、Items CRUD、pytest、api + PostgreSQL compose |

```
                    ┌─────────────────────────────┐
                    │        ready-stack          │
                    │  共用 conventions / CI / docs│
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐        ┌────────▼─────────┐       ┌────────▼────────────────┐
│ ready-python   │        │ ready-docker     │       │ ready-python-docker-    │
│ 應用層模板      │        │ core/lang/scenario│       │ webapi（實際服務）       │
└────────────────┘        └──────────────────┘       └─────────────────────────┘
```

## 快速開始

前置條件：Docker Desktop（或 Docker Engine + Compose v2）、Python 3.12+、Git。

```bash
git clone https://github.com/anthemjelly/ready-stack.git
cd ready-stack

# 1) 本地品質檢查（ruff + pyright + pytest）
make install
make check

# 2) 建置三個套件的 Docker 映像
make docker-build

# 3) 起一套 FastAPI + PostgreSQL，驗證 CRUD
make e2e
```

Windows（PowerShell）：

```powershell
.\scripts\check.ps1 -Install
.\scripts\build-all.ps1
.\scripts\e2e-webapi.ps1
```

## 倉庫結構

```
ready-stack/
├── packages/
│   ├── ready-python/                  # Python 專案模板
│   ├── ready-docker/                  # 分層 Docker 工具箱
│   └── ready-python-docker-webapi/    # FastAPI + PostgreSQL 服務
├── docs/
│   ├── architecture.md                # 元件關係與設計取捨
│   ├── conventions.md                 # 必須遵守的共用規範
│   └── getting-started.md             # 由零開始的步驟
├── scripts/                           # 跨套件的建置 / 檢查 / e2e 腳本
├── .github/workflows/ci.yml           # CI：lint、typing、test、docker build
├── Makefile
└── README.md
```

## 常用指令

| 指令 | 作用 |
|------|------|
| `make install` | 建立 `.venv` 並以 editable 安裝兩個 Python 套件 |
| `make lint` / `make format` | ruff 檢查 / 格式化 |
| `make typecheck` | pyright 型別檢查 |
| `make test` | 兩個套件的 pytest |
| `make check` | lint + format-check + typecheck + test |
| `make docker-build` | 依序建置 core → python → discord → ready-python → webapi |
| `make compose-config` | 驗證 compose 檔 |
| `make e2e` | 起 webapi + PostgreSQL，跑 health / CRUD 驗證後清理 |

## 與舊 repo 的關係

`ready-docker` 與 `ready-python-docker-webapi` 兩個舊 repo 的內容已整理並整合進本 monorepo。
舊 repo 保留作歷史紀錄，並會在 README 標明「已遷移至 ready-stack」。新開發一律在本 repo 進行。

## 授權

[MIT](LICENSE)
