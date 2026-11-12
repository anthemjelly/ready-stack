SHELL := /bin/bash
PY ?= python3
VENV := .venv
BIN := $(VENV)/bin
COMPOSE ?= docker compose

.DEFAULT_GOAL := help
.PHONY: help venv install run test lint format typecheck migrate migration up down logs ps clean

help: ## 顯示可用指令
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

venv: ## 建立本地 .venv（如未存在）
	@test -d $(VENV) || $(PY) -m venv $(VENV)

install: venv ## 建立 .venv 並 editable 安裝本套件 + dev 依賴
	@$(BIN)/python -m pip install --upgrade pip --quiet
	@$(BIN)/python -m pip install --quiet -e ".[dev]"

run: ## 本機用 uvicorn 跑（需要本機可連的 PostgreSQL）
	@POSTGRES_HOST=$${POSTGRES_HOST:-localhost} $(BIN)/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## pytest（SQLite + aiosqlite，不需要 PostgreSQL）
	@$(BIN)/pytest -q

lint: ## ruff check + ruff format --check
	@$(BIN)/ruff check .
	@$(BIN)/ruff format --check .

format: ## ruff 自動修正與格式化
	@$(BIN)/ruff check --fix .
	@$(BIN)/ruff format .

typecheck: ## pyright（standard, py312）
	@$(BIN)/pyright

migrate: ## 套用 migration（alembic upgrade head）
	@$(BIN)/alembic upgrade head

migration: ## 新增 migration，例：make migration m="add users table"
	@$(BIN)/alembic revision --autogenerate -m "$(m)"

up: ## docker compose up -d --build
	@$(COMPOSE) up -d --build

down: ## docker compose down（連 volume 一起清）
	@$(COMPOSE) down -v --remove-orphans

logs: ## 跟隨 api 日誌
	@$(COMPOSE) logs -f api

ps: ## 顯示 compose 容器狀態
	@$(COMPOSE) ps

clean: ## 清掉 venv 與各種 cache
	@rm -rf $(VENV) .pytest_cache .ruff_cache .pyright htmlcov .coverage
