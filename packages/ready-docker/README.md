# ready-docker — 分層 Docker 工具箱

一套「三層積木」式 Docker 映像：**core（地基）→ lang/python（房屋框架）→ scenarios/discord（裝修好的房）**。
每一層都係獨立可建置、可 tag、可推上 registry 的映像；場景層只需要寫業務邏輯，時區、非 root 用戶、
healthcheck、entrypoint、venv 等重複設定由下層處理好。

> 建置次序**一定**係 `core → lang/python → scenarios/*`。搞錯次序就會出現 `FROM` 一個未存在映像的經典錯誤，
> 詳見 [第 4 節](#4-建置次序陷阱必讀)。

---

## 1. 三層概念

```
┌──────────────────────────────────────────────────────────────┐
│ Layer 3  scenarios/discord                                   │
│   FROM ${PYTHON_IMAGE}                                       │
│   discord.py + deep-translator + python-dotenv               │
│   CMD ["python", "-m", "app.main"]                           │
└───────────────────────────┬──────────────────────────────────┘
                            │  --build-arg PYTHON_IMAGE=ready-stack/python:dev
┌───────────────────────────▼──────────────────────────────────┐
│ Layer 2  lang/python                                         │
│   FROM python:3.12-slim-bookworm（腳本由 core 多階段複製）     │
│   /opt/venv + 分層 requirements + appuser(10001)             │
└───────────────────────────┬──────────────────────────────────┘
                            │  --build-arg CORE_IMAGE=ready-stack/core:dev
┌───────────────────────────▼──────────────────────────────────┐
│ Layer 1  core                                                │
│   FROM debian:bookworm-slim                                  │
│   curl / ca-certificates / git / tzdata                      │
│   appuser 10001、/app /logs /config                          │
│   entrypoint-base.sh、healthcheck.sh                         │
└──────────────────────────────────────────────────────────────┘
```

| 層 | 目錄 | 基礎映像 | 你得到什麼 |
|----|------|----------|------------|
| 1 | `core/` | `debian:bookworm-slim` | 系統工具、時區（預設 `Asia/Hong_Kong`）、`appuser`(10001)、共用 healthcheck/entrypoint、OCI labels |
| 2 | `lang/python/` | `python:3.12-slim-bookworm` | Python 3.12、`/opt/venv`、分層 requirements、UID 10001、繼承 core 的兩支腳本 |
| 3 | `scenarios/discord/` | `ready-stack/python:<tag>` | Discord 翻譯 bot 示範（`discord.py` + `deep-translator`） |

**為什麼 core 唔直接做 python 層的 base？**
`core` 係 Debian，而 conventions 規定 Python 層用官方 `python:3.12-slim-bookworm`（Debian 內建 Python 只有 3.11）。
所以 `lang/python/Dockerfile` 用多階段：`FROM ${CORE_IMAGE} AS core` 只為咗 `COPY --from=core` 兩支共用腳本，
第二階段才係真正 runtime。咁樣兩邊的腳本永遠一致，又唔需要自己編譯 Python。

---

## 2. 目錄結構

```
packages/ready-docker/
├── core/
│   ├── Dockerfile                 # Layer 1：debian:bookworm-slim
│   └── scripts/
│       ├── entrypoint-base.sh     # PID 1 轉發；/app/entrypoint.sh 存在就交畀佢
│       └── healthcheck.sh         # HEALTHCHECK 入口；/app/healthcheck 存在就交畀佢
├── lang/
│   └── python/
│       ├── Dockerfile             # Layer 2：python:3.12-slim-bookworm + /opt/venv
│       └── requirements/
│           └── base.txt           # 語言層共用依賴（pip / setuptools / wheel）
├── scenarios/
│   └── discord/
│       ├── Dockerfile             # Layer 3：discord 場景
│       ├── requirements.txt       # discord.py / deep-translator / python-dotenv
│       ├── .env.example
│       └── app/
│           ├── __init__.py
│           └── main.py            # !translate 指令；缺 token 時清楚報錯並正常結束
├── compose.yml                    # core + python（idle）＋ discord（profile: discord）
├── Makefile                       # build / smoke / hadolint / compose-config / verify
├── .dockerignore                  # build context = 本目錄
├── .env.example                   # DISCORD_BOT_TOKEN=
└── README.md
```

---

## 3. 快速開始

### 前置條件

- Docker Desktop 或 Docker Engine 24+，Compose v2
- 建置時需要網絡（apt 同 pip 要下載套件）

所有指令都假設 current directory 係 **本目錄** `packages/ready-docker`。
（build context 一律係本目錄，唔係 `core/`、`lang/python/` 或 `scenarios/discord/`。）

### 3.1 建置三層（依序）

```bash
docker build -t ready-stack/core:dev    -f core/Dockerfile .
docker build -t ready-stack/python:dev  --build-arg CORE_IMAGE=ready-stack/core:dev   -f lang/python/Dockerfile .
docker build -t ready-stack/discord:dev --build-arg PYTHON_IMAGE=ready-stack/python:dev -f scenarios/discord/Dockerfile .
```

或者用 Makefile（`build-python` 會自動先建 core，`build-discord` 會自動先建 python）：

```bash
make build          # 等於依序建三層
make build TAG=1.0.0
```

由 repo 根目錄一次過建全部套件（ready-docker 三層 + ready-python + webapi）：

```bash
bash scripts/build-all.sh
# Windows PowerShell
.\scripts\build-all.ps1
```

### 3.2 驗證

```bash
make smoke
# 等價於：
docker run --rm ready-stack/core:dev id -u                              # 10001
docker run --rm ready-stack/discord:dev /opt/venv/bin/python -c "import discord, deep_translator"
```

`make verify` 會跑齊 build + smoke + hadolint + compose config。

### 3.3 用 compose 起容器

```bash
cp .env.example .env          # 想跑 discord 才需要填 DISCORD_BOT_TOKEN

docker compose up -d core python      # 兩個 idle 容器，驗證映像同 healthcheck
docker compose --profile discord up -d  # 連 discord bot 一起起
docker compose ps
docker compose logs -f discord
docker compose --profile discord down
```

---

## 4. 建置次序陷阱（必讀）

### 現象

如果你先建 `lang/python` 或 `scenarios/discord`，會見到：

```
ERROR: failed to build: failed to solve: base name (${CORE_IMAGE}) should not be blank
```

或者（如果你硬編碼了 registry 名稱）`pull access denied` / `not found`。

### 原因

1. `lang/python/Dockerfile` 的第一個 `FROM` 係 `FROM ${CORE_IMAGE} AS core`，而 `CORE_IMAGE` 係**必填 build arg**
   （刻意冇 default，避免靜靜地 build 錯版本）。
2. `scenarios/discord/Dockerfile` 的 `FROM ${PYTHON_IMAGE}` 同理。
3. Docker 唔會自動幫你建上一層：`FROM ready-stack/python:dev` 只會去本地 image store 或 registry 搵，
   搵唔到就直接失敗。
4. Docker Compose 的 `build:` 亦唔會按 `FROM` 關係排次序，所以本套件**刻意唔用 compose build**，
   一律用 Makefile / 建置腳本控制次序。

### 本套件的做法

| 機制 | 位置 | 作用 |
|------|------|------|
| `ARG CORE_IMAGE` / `ARG PYTHON_IMAGE`（必填） | `lang/python/Dockerfile`、`scenarios/discord/Dockerfile` | 上層映像由建置命令傳入，唔寫死 registry |
| Makefile 依賴鏈 | `build-python: build-core`、`build-discord: build-python` | 單獨建一層都會自動先建上一層 |
| 有序建置腳本 | repo 根 `scripts/build-all.sh` / `build-all.ps1` | 由 core → python → discord → 其他套件逐個建 |
| CI | `.github/workflows/ci.yml` | 同樣按次序 build 三個 Dockerfile |

### 正確命令（記住 `--build-arg` 要跟 image 名一致）

```bash
# 1) core
docker build -t ready-stack/core:dev -f core/Dockerfile .
# 2) python ← CORE_IMAGE 要等於上一步的 -t
docker build -t ready-stack/python:dev --build-arg CORE_IMAGE=ready-stack/core:dev -f lang/python/Dockerfile .
# 3) discord ← PYTHON_IMAGE 要等於上一步的 -t
docker build -t ready-stack/discord:dev --build-arg PYTHON_IMAGE=ready-stack/python:dev -f scenarios/discord/Dockerfile .
```

> 建置輸出會有一個 BuildKit warning：`InvalidDefaultArgInFrom: Default value for ARG ${CORE_IMAGE} results in empty
> or invalid base image name`。呢個係因為 ARG 刻意冇 default（必填），屬預期警告，唔影響建置結果；
> 只要你有傳 `--build-arg` 就會成功。

---

## 5. 驗證清單（本機實測結果）

| # | 驗證 | 命令 | 結果 |
|---|------|------|------|
| 1 | core 建置 | `docker build -t ready-stack/core:dev -f core/Dockerfile .` | ✅ 成功 |
| 2 | python 建置 | `docker build -t ready-stack/python:dev --build-arg CORE_IMAGE=ready-stack/core:dev -f lang/python/Dockerfile .` | ✅ 成功（Python 3.12.16） |
| 3 | discord 建置 | `docker build -t ready-stack/discord:dev --build-arg PYTHON_IMAGE=ready-stack/python:dev -f scenarios/discord/Dockerfile .` | ✅ 成功（discord.py 2.7.1 / deep-translator 1.9.1） |
| 4 | 非 root UID | `docker run --rm ready-stack/core:dev id -u` | ✅ `10001` |
| 5 | 套件 import | `docker run --rm ready-stack/discord:dev /opt/venv/bin/python -c "import discord, deep_translator"` | ✅ exit 0 |
| 6 | hadolint | `hadolint --ignore DL3008 --ignore DL3013 --ignore DL3059 core/Dockerfile lang/python/Dockerfile scenarios/discord/Dockerfile` | ✅ 0 findings |
| 7 | compose 語法 | `docker compose -f compose.yml config -q` | ✅ exit 0 |
| 8 | healthcheck | `docker compose up -d core python` 後 `docker compose ps` | ✅ 兩個容器 `healthy` |
| 9 | 缺 token 行為 | `docker run --rm ready-stack/discord:dev`（無 `DISCORD_BOT_TOKEN`） | ✅ 印出 4 行清楚錯誤、`exit 0`、restart count 0（唔會 crash loop） |
| 10 | entrypoint 轉發 | `docker run --rm ready-stack/core:dev echo hello` | ✅ 印 `hello`（`exec "$@"` 生效） |

hadolint 完整命令（等同 Makefile 的 `make hadolint`）：

```bash
docker run --rm -v "$PWD:/mnt" -w /mnt hadolint/hadolint:latest-debian \
  hadolint --ignore DL3008 --ignore DL3013 --ignore DL3059 \
    core/Dockerfile lang/python/Dockerfile scenarios/discord/Dockerfile
```

---

## 6. 映像命名與 tag

| 層 | 本地 | CI / 推送 |
|----|------|-----------|
| core | `ready-stack/core:<tag>` | `ghcr.io/<owner>/ready-stack-core:<tag>` |
| python | `ready-stack/python:<tag>` | `ghcr.io/<owner>/ready-stack-python:<tag>` |
| discord | `ready-stack/discord:<tag>` | `ghcr.io/<owner>/ready-stack-discord:<tag>` |

- 開發用 `:dev`；發佈用 `:v0.x.y`（同時可打 `:latest`）。
- `Makefile` 用 `TAG` 變數：`make build TAG=1.2.3`。
- CI 用 `:ci` tag，避免同本地 `:dev` 混淆。

---

## 7. 各層規範

### 7.1 用戶、目錄、環境變數

| 項目 | 約定 |
|------|------|
| 運行用戶 | UID/GID **10001**，名稱 `appuser`；Dockerfile 用數字 `USER 10001:10001`（hadolint DL3066：host 冇呢個 user 都解析到） |
| HOME | `/home/appuser` |
| 目錄 | `/app`（工作目錄）、`/logs`、`/config`，全部 owner 係 `appuser` |
| Python | `PYTHONDONTWRITEBYTECODE=1`、`PYTHONUNBUFFERED=1`、`PIP_NO_CACHE_DIR=1` |
| venv | `/opt/venv`，`PATH=/opt/venv/bin:$PATH`，owner 係 `appuser`（場景層可以自己 `pip install`，唔需要 root） |
| 時區 | build arg `TZ`（預設 `Asia/Hong_Kong`），同時寫入 `/etc/localtime`、`/etc/timezone` |
| 容器內**唔用 root** 跑應用 | 全部 layer 最後都係 `USER 10001:10001` |

### 7.2 healthcheck 規範

- 每個映像都自帶 `HEALTHCHECK`，入口係 `/usr/local/bin/healthcheck.sh`：
  - `/app/healthcheck` **存在且可執行** → `exec` 佢（場景自訂檢查）；
  - 否則印一行提示並 `exit 0`（core 層冇應用級檢查，視為 healthy）。
- 自訂檢查語義同 Docker 一致：`exit 0` = healthy、非 0 = unhealthy。
- 場景要自訂檢查，只需喺場景層加 `/app/healthcheck`，唔需要改 Dockerfile 的 HEALTHCHECK。

```sh
# 場景自訂 healthcheck 範例（加入 scenarios/<場景>/app/healthcheck，COPY 時一齊放入 /app）
#!/bin/sh
set -eu
curl -fsS http://127.0.0.1:8080/healthz >/dev/null || exit 1
```

- compose 亦可以 override（例如加大 `start_period`）：

```yaml
healthcheck:
  test: ["CMD", "/usr/local/bin/healthcheck.sh"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 15s
```

### 7.3 entrypoint 規範

- 每個映像的 `ENTRYPOINT` 都係 `/usr/local/bin/entrypoint-base.sh`，`CMD` 係實際應用／預設 `sleep infinity`。
- `entrypoint-base.sh` 邏輯：
  1. `/app/entrypoint.sh` **存在且可執行** → `exec /app/entrypoint.sh "$@"`（場景初始化，例如 migration、等 DB）；
  2. 否則 `exec "$@"`（直接跑 CMD / `docker run` 參數）。
- 一定要用 `exec`：PID 1 先會收到 `SIGTERM`，`docker stop` 才會即刻而唔係等 timeout。
- **唔好用 shell form**（`CMD python -m app.main`）：會變成 `/bin/sh -c` 做 PID 1，訊號同 exit code 都會走樣；
  一律用 JSON array：`CMD ["python", "-m", "app.main"]`。
- 場景自訂 entrypoint 範本（最後一定要 `exec "$@"`，否則 CMD 唔會執行）：

```sh
#!/bin/sh
set -eu
# 例：等 DB / 跑 migration
# python -m app.migrate
exec "$@"
```

### 7.4 OCI labels

三個 Dockerfile 都有齊 conventions 要求的 labels：
`org.opencontainers.image.title` / `.description` / `.source` / `.licenses`（MIT）。

### 7.5 敏感資料（重要）

- **唔會**有任何密碼／token 檔入 image 或入 git。本套件冇 `db/`、冇 `password.txt`。
- 只提交 `.env.example`（空值／假值）；真 `.env` 由使用者自己複製，`.gitignore` 已忽略 `.env`、`.env.*`。
- 需要密碼檔的專案請用 `secrets:` + `.gitignore` 的 `*.secret`／`db/password*.txt` 規則，
  並且記住：**放過入 git 的密碼等於洩漏，要立刻更換**（舊 ready-docker repo 就發生過，見第 11 節）。
- `.dockerignore` 已排除 `.env*`，避免 local `.env` 被 COPY 入 build context。

---

## 8. 加一個語言層（例：Node.js）

1. 建 `lang/nodejs/Dockerfile`，第一個 stage 用 `ARG CORE_IMAGE` / `FROM ${CORE_IMAGE} AS core`，
   第二個 stage `FROM node:22-bookworm-slim`，用 `COPY --from=core` 拎 entrypoint／healthcheck 腳本，
   再跟第 7 節的用戶／目錄規範建 `appuser`。
2. 加 `lang/nodejs/requirements/` 或 `package.json` 等依賴描述。
3. 喺 repo 根 `scripts/build-all.sh` 加建置步驟（必需有 `--build-arg CORE_IMAGE=...`），並喺 `ci.yml` 加同樣步驟。
4. 喺本 README 第 1 節加一行「Layer 2（Node.js）」。
5. 建置次序：`core → lang/nodejs → scenarios/<場景>`。

## 9. 加一個場景層（例：webapi / CLI）

1. 複製 `scenarios/discord/` 做 `scenarios/<新場景>/`，改 Dockerfile 第一行 `ARG BASE_IMAGE`（或沿用 `PYTHON_IMAGE`）。
2. 場景 Dockerfile 模板：

```dockerfile
ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}

WORKDIR /app
COPY --chown=appuser:appuser scenarios/<新場景>/requirements.txt /opt/ready-docker/requirements.txt
USER 10001:10001
RUN /opt/venv/bin/pip install --no-cache-dir -r /opt/ready-docker/requirements.txt
COPY --chown=appuser:appuser scenarios/<新場景>/app /app/app

CMD ["python", "-m", "app.main"]
```

3. 依賴放 `requirements.txt`；程式放 `app/`；settings 用環境變數 + `.env.example`。
4. 如要對外端口，喺 compose 加 `ports:`；如要初始化流程，加 `/app/entrypoint.sh`（第 7.3 節）。
5. 喺 `scripts/build-all.sh` / `ci.yml` 加建置步驟，喺 `compose.yml` 加 service（長連線服務可加 `profiles:`）。

---

## 10. compose.yml 說明

| Service | Image | Profile | 用途 |
|---------|-------|---------|------|
| `core` | `ready-stack/core:dev` | 預設 | idle 容器（`sleep infinity`），驗證 Layer 1 |
| `python` | `ready-stack/python:dev` | 預設 | idle 容器，`docker compose exec python /opt/venv/bin/pip ...` |
| `discord` | `ready-stack/discord:dev` | `discord` | 翻譯 bot，需要 `DISCORD_BOT_TOKEN` |

- 專案名：`name: ready-stack-ready-docker`；network：`net-ready-docker`（bridge）。
- 資源限制：core/python 256 MB、discord 512 MB（`deploy.resources.limits`）。
- 日誌：`json-file`，`max-size: 10m`、`max-file: 3`。
- docker socket 唔會掛入容器；`no-new-privileges` 已開。
- discord 的 `restart: "on-failure:5"`：缺 token 時 app 以 `exit 0` 結束，容器保持停止（唔會無限 crash loop）；
  真崩潰（非 0 exit）最多重試 5 次。
- **compose 冇 `build:` 區段**，原因見第 4 節：compose 唔識排 `FROM` 的建置次序。

---

## 11. 與舊 ready-docker repo 的差異（已修正的 bug）

| 舊實作問題 | 後果 | 新實作 |
|------------|------|--------|
| `python.docker` / `discord.docker` 寫死 `FROM anthemjelly/ready-docker-core:latest`，冇 build args | 本地建置次序一錯就 `pull access denied`；必須先由 registry 拉舊映像，源碼根本 build 唔到 | 用 `ARG CORE_IMAGE` / `ARG PYTHON_IMAGE` 逐層傳入；Makefile 依賴鏈 + `scripts/build-all.*` 固定次序 |
| `core/scripts/entrypoint-base.sh` 係 **0 bytes**，Dockerfile 亦冇 `ENTRYPOINT` | `/app/entrypoint.sh` 永遠唔會執行；容器用 `tail -f` 做 PID 1，`docker stop` 要等 timeout | 腳本寫齊（`exec` 轉發 + `/app/entrypoint.sh` 契約）、COPY + chmod 0755、正式 `ENTRYPOINT` / `HEALTHCHECK`；已用 `docker run ... echo` 驗證 |
| `db/password.txt`、`db/password-dev.txt`、`lang/python/db/password.txt` 被 commit 入 git | 真密碼永久留在 git 歷史，任何 clone 都攞到 | 新套件完全冇密碼檔；只用 `.env` + `.env.example`，`.env` 由 `.gitignore` 忽略；舊密碼如仍在使用必須更換 |
| `.dockerignore` 放喺 `core/`、`lang/python/`、`scenarios/discord/` 子目錄 | build context 係 repo 根，子目錄 `.dockerignore` 完全唔生效 | 單一 `packages/ready-docker/.dockerignore` 對應唯一 build context |
| Python 環境用 apt 裝 `python3`（Debian 3.11）再自己開 venv | 版本同 conventions 的 3.12 唔一致，路徑散落 `/opt/python-deps` | Layer 2 直接用官方 `python:3.12-slim-bookworm`，venv 固定 `/opt/venv` |
| compose 有 external volume + DB + 密碼 secrets | 起唔到就係「volume 未 create」，同工具箱用途無關 | compose 只保留 core / python / discord 三個示範 service，冇 DB、冇 secrets file |

---

## 12. Troubleshooting

| 症狀 | 原因 | 解法 |
|------|------|------|
| `base name (${CORE_IMAGE}) should not be blank` | 漏 `--build-arg CORE_IMAGE=...` | 用 `make build`，或補 `--build-arg CORE_IMAGE=ready-stack/core:dev` |
| `pull access denied` / `image not found` | 建置次序錯，上一層未 build | 次序一定係 core → python → discord |
| 建置見到 `InvalidDefaultArgInFrom` warning | ARG 冇 default（預期設計） | 可忽略；確認你有傳 `--build-arg`，建置成功就得 |
| `exec /usr/local/bin/entrypoint-base.sh: no such file or directory` | `*.sh` 被 Windows editor 改成 CRLF | `.gitattributes` 已規定 `*.sh` 用 LF；`git add --renormalize .` 或 editor 設 LF |
| `docker compose config` 話 variable is not set | 冇 `.env` | `cp .env.example .env`（空值都可以） |
| discord 話缺 `DISCORD_BOT_TOKEN` | `.env` 未填／未傳入 | 填 `.env` 後 `docker compose --profile discord up -d`；或 `docker run --env-file .env` |
| discord 不停重啟 | 用咗 `restart: always` + token 無效 | 本套件已用 `on-failure:5`；app 對設定錯誤係 `exit 0`。檢查 `docker compose logs discord` |
| `!translate` 回「翻譯失敗」 | 容器冇出網／翻譯服務限流 | `docker run --rm ready-stack/discord:dev /opt/venv/bin/python -c "import urllib.request; urllib.request.urlopen('https://translate.google.com', timeout=10)"` 測試；稍後重試 |
| 寫 `/logs` permission denied | 宿主 bind mount 目錄唔係 UID 10001 | `sudo chown -R 10001:10001 ./logs` |
| hadolint 唔過 | 新版本加咗規則 | `make hadolint` 重現；DL3008/3013/3059 已在命令／CI ignore |
| `make` 喺 Windows 唔存在 | 冇安裝 make | 直接跑第 3.1 節三條 `docker build`，或用 `.\scripts\build-all.ps1` |

---

## 13. CI 與授權

- CI（`.github/workflows/ci.yml`）會：hadolint 檢查三個 Dockerfile → 按 core → python → discord 建置 →
  驗證 compose 檔。任何一層失敗都會即刻見到。
- 授權：[MIT](../../LICENSE)（同 ready-stack 其他套件一致）。
