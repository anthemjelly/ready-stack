# ready-python 本地開發指令（Linux / macOS / WSL）。
# Windows 用戶可以唔用 make，直接跑 README 入面嘅 PowerShell 指令。
SHELL := /bin/bash

PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
IMAGE ?= ready-stack/ready-python:dev
ARGS ?= --version

.DEFAULT_GOAL := help
.PHONY: help venv install lint format format-check typecheck test build run

help: ## 顯示可用指令
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

venv: ## 建立本地 .venv（如未存在）
	@test -d $(VENV) || $(PY) -m venv $(VENV)
	@$(BIN)/python -m pip install --upgrade pip --quiet

install: venv ## 以 editable 模式安裝 package + dev 依賴
	@$(BIN)/python -m pip install --quiet -e ".[dev]"

lint: ## ruff 靜態檢查
	@$(BIN)/ruff check .

format: ## ruff 自動格式化並修正
	@$(BIN)/ruff format .
	@$(BIN)/ruff check --fix .

format-check: ## ruff 格式檢查（CI 模式）
	@$(BIN)/ruff format --check .

typecheck: ## pyright 型別檢查（先將 venv 放上 PATH，令 pyright 用 venv 內嘅依賴）
	@PATH="$(CURDIR)/$(BIN):$$PATH" $(BIN)/pyright

test: ## pytest（唔依賴網絡）
	@$(BIN)/pytest -q

build: ## 建置 Docker 映像
	docker build -t $(IMAGE) .

run: ## 執行映像；可用 ARGS 覆寫（預設 --version）
	docker run --rm $(IMAGE) $(ARGS)
