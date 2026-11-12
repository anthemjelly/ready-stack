# ready-docker 分層工具箱 Makefile
# Windows 冇 make：直接用 docker build 指令（見 README），或由 repo 根跑 scripts\build-all.ps1。
SHELL := /bin/bash
TAG ?= dev

CORE_IMAGE := ready-stack/core:$(TAG)
PYTHON_IMAGE := ready-stack/python:$(TAG)
DISCORD_IMAGE := ready-stack/discord:$(TAG)

HADOLINT_FLAGS := --ignore DL3008 --ignore DL3013 --ignore DL3059
DOCKERFILES := core/Dockerfile lang/python/Dockerfile scenarios/discord/Dockerfile

.DEFAULT_GOAL := help
.PHONY: help build build-core build-python build-discord build-all smoke hadolint compose-config verify up up-discord down logs clean

help: ## 顯示可用指令
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# 建置次序就係依賴次序：core → python → discord。
# 單獨 make build-python 時會先確認 core 存在，避免「FROM 一個未存在嘅 image」呢個經典陷阱。
build-core: ## [1/3] 建置 core 層
	docker build -t $(CORE_IMAGE) -f core/Dockerfile .

build-python: build-core ## [2/3] 建置 lang/python 層（自動先建 core）
	docker build -t $(PYTHON_IMAGE) \
		--build-arg CORE_IMAGE=$(CORE_IMAGE) \
		-f lang/python/Dockerfile .

build-discord: build-python ## [3/3] 建置 scenarios/discord（自動先建 python）
	docker build -t $(DISCORD_IMAGE) \
		--build-arg PYTHON_IMAGE=$(PYTHON_IMAGE) \
		-f scenarios/discord/Dockerfile .

build: build-discord ## 依序建置三層：core → python → discord

build-all: ## 由 repo 根目錄腳本建置「所有套件」（ready-docker + ready-python + webapi）
	bash ../../scripts/build-all.sh

smoke: build ## 用短命令容器驗證 UID 與套件 import（唔會留低運行中容器）
	docker run --rm $(CORE_IMAGE) id -u
	docker run --rm $(PYTHON_IMAGE) /opt/venv/bin/python -c "import sys; print(sys.version.split()[0])"
	docker run --rm $(DISCORD_IMAGE) /opt/venv/bin/python -c "import discord, deep_translator; print('discord + deep_translator import ok')"

hadolint: ## hadolint 檢查三個 Dockerfile
	docker run --rm -v "$(CURDIR):/mnt" -w /mnt hadolint/hadolint:latest-debian \
		hadolint $(HADOLINT_FLAGS) $(DOCKERFILES)

compose-config: ## 驗證 compose.yml
	docker compose -f compose.yml config -q

verify: build smoke hadolint compose-config ## 一次過跑 build + smoke + hadolint + compose-config

up: ## 起 core + python（idle）
	docker compose up -d core python

up-discord: ## 起 core + python + discord（.env 內要有 DISCORD_BOT_TOKEN）
	docker compose --profile discord up -d

down: ## 停並移除 container / network（映像保留）
	docker compose --profile discord down

logs: ## 跟蹤 compose 日誌
	docker compose --profile discord logs -f

clean: ## 刪除本套件三個映像
	-docker image rm $(DISCORD_IMAGE) $(PYTHON_IMAGE) $(CORE_IMAGE)
