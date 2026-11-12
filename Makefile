SHELL := /bin/bash
PY ?= python3
ROOT := $(CURDIR)
VENV := .venv
BIN := $(VENV)/bin

.DEFAULT_GOAL := help
.PHONY: help venv install lint format format-check typecheck test check docker-build compose-config e2e clean

help: ## 顯示可用指令
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

venv: ## 建立本地 .venv（如未存在）
	@test -d $(VENV) || $(PY) -m venv $(VENV)
	@$(BIN)/python -m pip install --upgrade pip --quiet

install: venv ## 以 editable 模式安裝兩個 Python 套件 + dev 依賴
	@$(BIN)/python -m pip install --quiet -e "packages/ready-python[dev]" -e "packages/ready-python-docker-webapi[dev]"

lint: ## ruff 靜態檢查
	@$(BIN)/ruff check packages

format: ## ruff 自動格式化
	@$(BIN)/ruff format packages
	@$(BIN)/ruff check --fix packages

format-check: ## ruff 格式檢查（CI 模式）
	@$(BIN)/ruff format --check packages

typecheck: ## pyright 型別檢查
	@cd packages/ready-python && $(ROOT)/$(BIN)/pyright --pythonpath $(ROOT)/$(BIN)/python
	@cd packages/ready-python-docker-webapi && $(ROOT)/$(BIN)/pyright --pythonpath $(ROOT)/$(BIN)/python

test: ## 兩個套件的 pytest（逐個套件跑，才會載入各自的 pyproject 設定）
	@cd packages/ready-python && $(ROOT)/$(BIN)/pytest -q
	@cd packages/ready-python-docker-webapi && $(ROOT)/$(BIN)/pytest -q

check: lint format-check typecheck test ## 完整品質檢查

docker-build: ## 依序建置所有 Docker 映像
	@bash scripts/build-all.sh

compose-config: ## 驗證 compose 檔
	@bash scripts/compose-config.sh

e2e: ## 起 webapi + PostgreSQL，跑 health / CRUD 驗證後清理
	@bash scripts/e2e-webapi.sh

clean: ## 清掉本地快取與 venv
	@rm -rf $(VENV) .pytest_cache .ruff_cache
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
