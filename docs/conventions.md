# 共用規範（Conventions）

本文件是三個套件都必須遵守的「合約」。如果你只想快速用某個套件，可以只看該套件自己的 README；
但只要你改動這個 repo 的程式碼，就要守這裡的規則。

## 1. Python

| 項目 | 規定 |
|------|------|
| 版本 | 3.12（`pyproject.toml` 的 `requires-python = ">=3.12"`） |
| 依賴管理 | `pip` + `pyproject.toml`（保持可移植，不強制 uv；dev 依賴放 `[project.optional-dependencies].dev`） |
| 佈局 | `src/` layout：`src/<package>/`，測試放 `tests/` |
| Lint / format | ruff：`line-length = 100`、`target-version = "py312"`，select `E,W,F,I,B,C4,UP` |
| 型別 | pyright：`typeCheckingMode = "standard"`、`pythonVersion = "3.12"` |
| 測試 | pytest，**不得依賴網絡**；需要 DB 的用 SQLite + `aiosqlite` 覆蓋掉真實 PostgreSQL |
| CLI | 用標準庫 `argparse`；除非有實際需要，不引入 typer / click |
| 日誌 | 標準庫 `logging`，格式由 app 設定；不要在 library 內 `print` |

`[project.optional-dependencies].dev` 最少要有：`pytest`、`pytest-cov`、`ruff`、`pyright`、`pre-commit`。
webapi 另外要有：`httpx`、`pytest-asyncio`、`aiosqlite`。

## 2. Docker

| 項目 | 規定 |
|------|------|
| 基礎映像 | `python:3.12-slim-bookworm`（語言／應用層）、`debian:bookworm-slim`（core 層） |
| 運行用戶 | UID/GID `10001`，名稱 `appuser`，`HOME=/home/appuser`，容器內**不得用 root 跑應用** |
| 環境變數 | `PYTHONDONTWRITEBYTECODE=1`、`PYTHONUNBUFFERED=1`、`PIP_NO_CACHE_DIR=1` |
| venv | `/opt/venv`，`PATH=/opt/venv/bin:$PATH` |
| 多階段 | builder 階段安裝依賴 → runtime 階段只複製 venv／產物，不帶編譯器 |
| Dockerfile 檔名 | 一律 `Dockerfile`（每個服務一個資料夾） |
| 映像命名 | 本地 `ready-stack/<component>:<tag>`；CI／推送 `ghcr.io/<owner>/ready-stack-<component>:<tag>` |
| Metadata | 加 `org.opencontainers.image.title/description/source/license` labels |
| 健康檢查 | 服務類用 `HEALTHCHECK` 打 `/healthz`（用 `python -c urllib` 或 `curl`，需在 runtime 階段確認有工具） |
| Entrypoint | 需要初始化（migration、等 DB）的服務用 `docker/entrypoint.sh`，最後 `exec "$@"` |
| Lint | hadolint 必須通過（apt 版本 pin 規則 DL3008 在 CI 忽略） |

## 3. Docker Compose

| 項目 | 規定 |
|------|------|
| 檔名 | `compose.yml`（預設）；開發覆蓋用 `compose.dev.yml` |
| 專案名 | `name: ready-stack-<component>` |
| restart | API `unless-stopped`、DB `always` |
| 健康檢查 | DB：`pg_isready`；API：`/healthz` |
| 啟動依賴 | `depends_on: db: condition: service_healthy` |
| 資源限制 | `deploy.resources.limits`（`cpus`、`memory`）＋ reservations |
| 日誌 | `logging: driver: json-file, max-size: 10m, max-file: 3` |
| 端口 | `8000`（webapi，宿主可用 `${API_PORT:-8000}`）、`5432`（可選，`${DB_PORT:-5432}`） |
| 網路 | 每個 compose 用自己的 bridge network（`net-<component>`） |

## 4. 密碼與敏感資料（重要）

- **絕對不要**把真密碼 / token / `.env` commit 入 git。
- 只提交 `.env.example`（全是假值）。
- 需要密碼檔的 compose 用 `secrets:` + `db/password.txt`，而 `db/password.txt` 必須在 `.gitignore`；
  提供 `db/password.txt.example` 由使用者複製。
- 舊 repo 的 git 歷史曾經出現過真實 DB 密碼；如那些密碼仍在使用，**必須更換**。

## 5. Git

- Conventional Commits：`feat:`、`fix:`、`docs:`、`chore:`、`test:`、`ci:`、`refactor:`。
- 主分支 `main`；不要 force-push 已公開的 `main`。
- 版本 tag：`v0.x.y`。

## 5a. Windows / PowerShell 腳本

- `.ps1` 一律存成 **UTF-8 with BOM**：Windows PowerShell 5.1 讀無 BOM 的 UTF-8 會用 ANSI
  （繁中系統即 CP950）解碼，中文有機會吞掉引號令 script 解析失敗。
- 腳本要同時兼容 **Windows PowerShell 5.1 與 PowerShell 7**。
- PS 5.1 會把 native command（docker / pip 等）的 stderr 當成終止錯誤；呼叫外部程式時
  要暫時把 `$ErrorActionPreference` 設回 `Continue`，再自行檢查 `$LASTEXITCODE`。
- 新增或修改 `.ps1` 後，最起碼用下面方式驗證語法：

```powershell
$tokens = $null; $errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path .\scripts\x.ps1), [ref]$tokens, [ref]$errors)
if ($errors.Count) { $errors | ForEach-Object Message }
```

## 6. 每個套件的最低要求

```
packages/<name>/
├── README.md          # 用途、快速開始、結構、指令
├── pyproject.toml     # Python 套件（如適用）
├── Makefile           # install / lint / test / build
├── tests/             # pytest
├── Dockerfile         # 如適用
├── .env.example       # 如需環境變數
└── .dockerignore
```
