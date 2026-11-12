# ready-python

ready-stack 入面嘅 **Python 專案起手模板**。複製呢個資料夾，你就有一個即刻行得嘅
Python CLI 專案骨架：`src/` layout、`pyproject.toml`、ruff、pyright、pytest、
pre-commit、devcontainer、多階段 Dockerfile 同 Makefile，全部跟
[共用規範](../../docs/conventions.md)。

呢個 package 亦係整套規範嘅「活文件」：入面嘅 `greet` CLI 只係示範用，重點係
**每個環節都真正跑得通、驗證得過**，你可以照住佢改。

| 你會得到 | 內容 |
| --- | --- |
| Python | 3.12+、`src/` layout、hatchling 打包 |
| 品質工具 | ruff（lint + format）、pyright（`standard`）、pytest（唔靠網絡）、pre-commit |
| CLI | 標準庫 `argparse`：`ready-python greet --name World`、`--version` |
| Docker | 多階段 builder / runtime、`/opt/venv`、非 root（UID/GID 10001）、OCI labels、HEALTHCHECK |
| 開發環境 | VS Code devcontainer、Makefile、統一 `pyproject.toml` 設定 |

---

## 快速開始

前置需求：

- **Python 3.12+**（本地開發用；容器內已固定 3.12）
- **Git**
- **Docker Desktop / Engine**（只有跑容器先需要；Compose 唔需要，呢個 package 冇 compose）

### 1. 本地開發（Windows PowerShell）

```powershell
cd packages\ready-python

# 建立虛擬環境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 以 editable 模式安裝 package 同 dev 依賴
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

如果 PowerShell 唔准你行 `Activate.ps1`（執行原則問題），可以唔 activate，
直接叫 venv 入面嘅執行檔：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\ready-python.exe --version
```

### 2. 本地開發（Linux / macOS / WSL）

```bash
cd packages/ready-python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 3. 驗證安裝

```console
$ ready-python --version
ready-python 0.1.0

$ ready-python greet --name World
Hello, World!

$ pytest
```

> `pip install -e ".[dev]"` 一定要喺 `pyproject.toml` 所在嘅資料夾（即係
> `packages/ready-python/`）執行，`.[dev]` 先會解析到呢個 package。

---

## CLI 行為

| 指令 | 輸出 | Exit code |
| --- | --- | --- |
| `ready-python` | 說明（help） | `0` |
| `ready-python --help` | 說明（help） | `0` |
| `ready-python --version` | `ready-python 0.1.0` | `0` |
| `ready-python greet --name World` | `Hello, World!` | `0` |
| `ready-python greet --name ""` | `error: name 不可以是空字串`（stderr） | `2` |
| `ready-python greet` | argparse 錯誤：缺少 `--name`（stderr） | `2` |

> Windows PowerShell 傳空字串做 native 程式嘅參數時有機會被丟棄（會變成「缺少 `--name`」）。
> 想即場試錯誤路徑，可以用 `ready-python greet --name=`，或者喺 Python 入面直接叫
> `main(["greet", "--name", ""])`。

`ready-python` 同 `python -m ready_python` 係同一個入口（`ready_python.cli:main`）。
`main()` 只會**回傳** exit code，唔會自己 `sys.exit`，所以測試可以直接
`assert main([...]) == 0`。

`greet()` 嘅規則：名字唔可以係空字串或者只有空白；名字本身**唔會**被 trim
（`greet("  Ann  ")` 會回 `Hello,   Ann  !`）。呢個「純函數」放喺
`src/ready_python/core.py`，可以原封不動搬去 FastAPI handler 或者 background job 用。

---

## 專案結構

```
packages/ready-python/
├── pyproject.toml              # metadata、依賴、ruff / pyright / pytest 設定
├── README.md                   # 你睇緊呢份
├── Makefile                    # install / lint / format / typecheck / test / build / run
├── Dockerfile                  # 多階段：builder → runtime
├── .dockerignore
├── .devcontainer/
│   └── devcontainer.json       # VS Code Dev Container（Python 3.12 bookworm）
├── src/
│   └── ready_python/
│       ├── __init__.py         # __version__（版本號唯一來源）
│       ├── __main__.py         # python -m ready_python
│       ├── cli.py              # argparse 入口：main(argv) -> int
│       ├── core.py             # greet() 業務邏輯（唔 print、唔讀環境變數）
│       └── py.typed            # 標記 package 自帶型別資訊
└── tests/
    ├── test_core.py            # greet() 正常路徑 + 錯誤路徑
    └── test_cli.py             # argparse、exit code、stdout/stderr、python -m
```

| 檔案 | 作用 |
| --- | --- |
| `pyproject.toml` | 套件 metadata、`[project.scripts]`、dev 依賴，以及全部工具設定 |
| `src/ready_python/core.py` | 真業務邏輯；刻意同 CLI 解耦，方便測試同重用 |
| `src/ready_python/cli.py` | 薄薄一層 argparse：解析參數 → 叫 core → 回傳 exit code |
| `src/ready_python/__main__.py` | 支援 `python -m ready_python`（同 console script 完全一致） |
| `tests/` | pytest；唔會連網、唔使 DB、唔使 Docker |
| `Dockerfile` | 多階段建置，runtime 冇編譯器、非 root 執行 |
| `Makefile` | Linux / macOS / WSL 用；Windows 用 README 嘅 PowerShell 指令 |

---

## 常用指令

### 直接叫工具

| 目的 | 指令 |
| --- | --- |
| Lint | `ruff check .` |
| Format（自動改） | `ruff format .` |
| Format 檢查（CI 模式） | `ruff format --check .` |
| 型別檢查 | `pyright`（venv 要 activate 咗先，見下面注意） |
| 測試 | `pytest` |
| 測試 + 覆蓋率 | `pytest --cov=ready_python --cov-report=term-missing` |
| 建置 Docker 映像 | `docker build -t ready-stack/ready-python:dev .` |
| 跑容器 | `docker run --rm ready-stack/ready-python:dev --version` |

### 用 Makefile（Linux / macOS / WSL）

```bash
make install        # 建 .venv + pip install -e ".[dev]"
make lint           # ruff check .
make format         # ruff format . + ruff check --fix .
make format-check   # ruff format --check .
make typecheck      # pyright
make test           # pytest -q
make build          # docker build -t ready-stack/ready-python:dev .
make run            # docker run --rm <image> --version
make run ARGS="greet --name Docker"
```

`make` 只係一層薄 wrapper；每個 target 都可以用上面「直接叫工具」嗰行指令代替。
Windows 冇 `make` 都唔影響任何功能。

> **pyright 嘅 Python 環境**：pyright 會由 `PATH` 揾 Python 直譯器去解析 site-packages，
> 所以跑之前要 activate venv。如果唔想 activate，可以明確指定：
> `pyright --pythonpath .venv/Scripts/python.exe`（Linux / macOS 係 `.venv/bin/python`）。
> `make typecheck` 已經自動幫你將 venv 放上 `PATH`。

---

## Docker

```bash
# 建置（context 係 packages/ready-python）
docker build -t ready-stack/ready-python:dev .

# 跑單次命令（--rm：容器即刻清理，唔會留低長期 process）
docker run --rm ready-stack/ready-python:dev --version
# ready-python 0.1.0

docker run --rm ready-stack/ready-python:dev greet --name Docker
# Hello, Docker!
```

映像設計：

| 項目 | 做法 |
| --- | --- |
| 多階段 | `builder` 裝 package 入 `/opt/venv`；`runtime` 只複製 venv，唔帶編譯器／pip cache |
| 基礎映像 | 兩個階段都用 `python:3.12-slim-bookworm`（跟 [conventions §2](../../docs/conventions.md)） |
| Venv | `/opt/venv`，`PATH=/opt/venv/bin:$PATH`；entrypoint 直接叫 `ready-python` |
| 非 root | `appuser`，UID/GID `10001`，`HOME=/home/appuser`（建置時可以用 `--build-arg APP_UID=...` 覆蓋） |
| 環境變數 | `PYTHONDONTWRITEBYTECODE=1`、`PYTHONUNBUFFERED=1`、`PIP_NO_CACHE_DIR=1` |
| Metadata | OCI labels：`title` / `description` / `source` / `licenses` |
| Healthcheck | `HEALTHCHECK ... CMD ready-python --version || exit 1` |
| Entrypoint / CMD | `ENTRYPOINT ["ready-python"]`、`CMD ["--help"]` |

注意：呢個係 **CLI 模板**，容器預設跑完一個命令就退出，所以 `docker run --rm ... --version`
睇唔到 health status（容器壽命太短）。當你將佢改造成長期服務（例如加個 web server）時，
個 `HEALTHCHECK` 先會持續生效；到時記得將檢查改成打 `/healthz`。

映像命名跟 conventions：本地 `ready-stack/<component>:<tag>`，CI／推送係
`ghcr.io/<owner>/ready-stack-<component>:<tag>`。

---

## 用呢個模板開新專案

### 1. 複製資料夾

Linux / macOS / WSL：

```bash
cp -r packages/ready-python ../my-new-project
cd ../my-new-project
rm -rf .git .venv .pytest_cache .ruff_cache
git init -b main
```

Windows PowerShell：

```powershell
Copy-Item -Recurse packages\ready-python ..\my-new-project
cd ..\my-new-project
Remove-Item -Recurse -Force .git, .venv, .pytest_cache, .ruff_cache -ErrorAction SilentlyContinue
git init -b main
```

### 2. 改名 checklist

`ready-python` 係 distribution 名（有連字號），`ready_python` 係 import 名（有底線）。
改名時兩個都要處理：

| 位置 | 原本 | 要改成 |
| --- | --- | --- |
| `pyproject.toml` → `[project].name` | `ready-python` | 你嘅 distribution 名（例：`my-new-project`） |
| `pyproject.toml` → `[project].description` / `keywords` / `classifiers` | 模板描述 | 你嘅描述 |
| `pyproject.toml` → `[project.scripts]` | `ready-python = "ready_python.cli:main"` | `<CLI 名> = "<新package>.cli:main"` |
| `pyproject.toml` → `[tool.hatch.build.targets.wheel].packages` | `["src/ready_python"]` | `["src/<新package>"]` |
| `src/ready_python/` 資料夾 | `ready_python` | `src/<新package>/`（import 名，建議只用底線） |
| 全部 `from ready_python...` import | — | 改成新 package 名（`src/`、`tests/`、`__main__.py`） |
| `src/<package>/__init__.py` | `__version__ = "0.1.0"` | 由 `0.1.0` 開始（版本號唯一來源） |
| `tests/test_cli.py` | `python -m ready_python` | `python -m <新package>` |
| `tests/test_cli.py` | `f"ready-python {__version__}"` | 對應新 CLI 名 |
| `Dockerfile` → `LABEL org.opencontainers.image.title/description` | `ready-python` | 新專案 |
| `Dockerfile` → `ENTRYPOINT` / `HEALTHCHECK` | `ready-python` | 新 CLI 名 |
| `Makefile` → `IMAGE` | `ready-stack/ready-python:dev` | `<你嘅映像名>:dev` |
| `.devcontainer/devcontainer.json` → `name` | `ready-python` | 新專案名 |
| `README.md` | 模板說明 | 你嘅專案 README |

改完之後，喺新資料夾再行一次完整驗證：

```bash
python -m venv .venv
# Windows: .venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv/bin/pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
pyright
docker build -t my-new-project:dev .
docker run --rm my-new-project:dev --version
```

> 小提示：`git init` 之後唔好忘記由 repo 根嘅 `.gitignore` 抄一份（或者自己加
> `.venv/`、`__pycache__/`、`.pytest_cache/`、`.ruff_cache/` 等），避免 commit 咗
> 本機環境。

---

## 設計取捨

- **src layout**：強迫你「安裝先行」——`pytest` 同 `import` 都係由已安裝嘅 package
  攞檔案，唔會唔小心 import 到工作目錄入面嘅同名資料夾，亦唔會將 `tests/` 或
  `pyproject.toml` 打包入 wheel。
- **薄 CLI、厚 core**：`core.py` 係純函數（唔 print、唔讀環境變數、唔掂 IO），
  CLI 只負責參數解析同 exit code。呢個切法令核心邏輯可以搬去 web handler、
  job queue 或者 notebook，而測試唔需要叫 subprocess。
- **用標準庫 `argparse`**：conventions 明確要求（除非真係有需要先引入 typer / click）。
  模板唔應該一開始就綁定第三方 CLI framework。
- **測試唔依賴網絡**：`tests/` 完全離線、唔使 DB、唔使 Docker；唯一嘅 subprocess
  測試係叫 `python -m ready_python --version`，目的係驗證模組入口，唔係連網。
- **版本號單一來源**：`pyproject.toml` 用 `dynamic = ["version"]`，由
  `src/ready_python/__init__.py` 嘅 `__version__` 讀取，避免兩處改漏。
- **ruff / pyright 設定放 `pyproject.toml`**：一個檔案搞掂，唔使 `.ruff.toml` /
  `pyrightconfig.json`；設定值跟 [conventions §1](../../docs/conventions.md)
  （`line-length = 100`、`target-version = "py312"`、`select = E,W,F,I,B,C4,UP`；
  pyright `standard` + `pythonVersion = "3.12"`）。
- **容器非 root + 多階段**：runtime 映像冇編譯器同 build 依賴，攻擊面細啲，映像亦細啲；
  UID/GID 10001 方便同其他服務對齊。
- **冇 `.env.example`**：CLI 模板唔需要任何環境變數；如果你改做服務，跟
  [conventions §4](../../docs/conventions.md) 只提交全假值嘅 `.env.example`，
  真密碼／token 一律唔入 git。

---

## 同 ready-stack 其他套件嘅關係

呢個 package 係三個套件入面最細嘅一個，定位係「起手模板」：

- [`ready-docker`](../ready-docker/README.md)：分層 Docker 工具箱（`core` → `lang/python`
  → `scenarios/*`），想做多層映像建置就睇佢；
- [`ready-python-docker-webapi`](../ready-python-docker-webapi/README.md)：實戰 FastAPI +
  PostgreSQL 服務模板，需要 API、DB、migration、compose 就睇佢；
- `ready-python`（本套件）：需要一個乾淨 Python 專案骨架就由呢度開始。

三者共用 [共用規範](../../docs/conventions.md) 同 [架構說明](../../docs/architecture.md)，
但彼此冇編譯依賴，每個資料夾都可以單獨複製出去用。

CI（[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)）會對呢個 package 跑：

1. `pip install -e ".[dev]"`
2. `ruff check .`
3. `ruff format --check .`
4. `pyright`
5. `pytest -q`
6. `docker build -t ready-stack/ready-python:ci packages/ready-python`
7. 對 `Dockerfile` 跑 hadolint（忽略 `DL3008` / `DL3013` / `DL3059`）

本機想一次過跑 CI 等價檢查（Windows）：

```powershell
.\scripts\check.ps1 -Install   # 由 repo 根目錄執行
```

---

## 疑難排解

| 症狀 | 原因／解法 |
| --- | --- |
| `ModuleNotFoundError: No module named 'ready_python'` | 未喺 `packages/ready-python` 內行 `pip install -e ".[dev]"`，或者用錯咗另一個 Python |
| `ruff: command not found` / `pyright: command not found` | dev 依賴未裝，或者 venv 未 activate；用 `.venv\Scripts\python -m ruff ...` 都可以 |
| `pytest` 搵唔到測試 | 喺 `packages/ready-python` 根目錄行；`testpaths = ["tests"]` 已設定好 |
| `pyright` 話 `Import "pytest" could not be resolved` | pyright 用咗系統 Python（venv 未 activate）；activate venv 再行，或者 `pyright --pythonpath .venv/Scripts/python.exe` |
| pyright 第一次行好慢／要下載 node | `pyright`（pip 版）首次執行可能要下載 node runtime；或者改用 `npx pyright` |
| `docker build` 好慢 | 第一次要拉 `python:3.12-slim-bookworm` 同喺 builder 內裝 package；之後有 layer cache |
| PowerShell 阻止 `Activate.ps1` | 用 `.\.venv\Scripts\python.exe -m ...` 直接叫執行檔，或者暫時 `Set-ExecutionPolicy -Scope Process Bypass` |
| Windows 冇 `make` | 直接用 README 上面嘅原始指令；或者用根目錄 `scripts\*.ps1` |

---

## 授權

[MIT](../../LICENSE) © ready-stack contributors
