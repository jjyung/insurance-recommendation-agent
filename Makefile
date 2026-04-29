.PHONY: help \
	install install-dev install-eval install-gcp install-all \
	sync sync-dev sync-eval sync-gcp sync-all \
	db-init db-reset clean-db clean-sessions \
	toolbox-up toolbox-down toolbox-logs \
	run run-web run-api run-cli run-fastapi debug-fastapi \
	ui-install ui-dev ui-build \
	clean clean-all check test-api env-check \
	eval-core eval-core-case-1 eval-core-case-2 eval-core-case-3 \
	eval-extended eval-extended-case-4 eval-extended-case-5 eval-extended-case-6 \
	eval-safety eval-safety-case-09 eval-safety-case-10 eval-safety-case-11 eval-safety-case-12 eval-safety-case-13 \
	eval-session-aware eval-session-aware-case-s1 eval-session-aware-case-s2 eval-session-aware-case-s3 \
	up down _kill-port

# ─── 預設目標 ──────────────────────────────────────────────

help: ## 列出所有可用指令
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*##"}; {printf " \033[36m%-24s\033[0m %s\n", $$1, $$2}'

# ─── 變數 ──────────────────────────────────────────────────

PYTHON := .venv/bin/python
UV := uv
SQLITE := sqlite3
NPM := npm

DB_FILE := db/insurance.db
ADK := .venv/bin/adk
APP_DIR := .
ADK_PORT := 8000
FASTAPI_PORT := 8080
FRONTEND_DIR := frontend
EVAL_DIR := tests/evals
EVAL_CONFIG := $(EVAL_DIR)/test_config.json
DEBUG_PORT ?= 5678

# ─── 環境建立 ──────────────────────────────────────────────

install: ## 建立虛擬環境並安裝核心依賴
	$(UV) venv --python 3.12
	$(UV) sync

install-dev: ## 建立虛擬環境並安裝開發依賴
	$(UV) venv --python 3.12
	$(UV) sync --extra dev

install-eval: ## 建立虛擬環境並安裝含 eval extra 的依賴
	$(UV) venv --python 3.12
	$(UV) sync --extra eval

install-gcp: ## 建立虛擬環境並安裝 GCP optional 依賴
	$(UV) venv --python 3.12
	$(UV) sync --extra gcp

install-all: ## 建立虛擬環境並安裝所有 optional 依賴
	$(UV) venv --python 3.12
	$(UV) sync --all-extras

sync: ## 同步核心依賴（已有 .venv 時使用）
	$(UV) sync

sync-dev: ## 同步開發依賴
	$(UV) sync --extra dev

sync-eval: ## 同步含 eval extra 的依賴（執行 evals 時使用）
	$(UV) sync --extra eval

sync-gcp: ## 同步 GCP optional 依賴
	$(UV) sync --extra gcp

sync-all: ## 同步所有 optional 依賴
	$(UV) sync --all-extras

env-check: ## 檢查必要工具與環境變數
	@echo "=== 環境檢查 ==="
	@command -v $(UV) >/dev/null 2>&1 && echo "✔ uv" || echo "✘ uv 未安裝"
	@command -v docker >/dev/null 2>&1 && echo "✔ docker" || echo "✘ docker 未安裝"
	@command -v $(SQLITE) >/dev/null 2>&1 && echo "✔ sqlite3" || echo "✘ sqlite3 未安裝"
	@[ -f .env ] && echo "✔ .env 存在" || echo "✘ .env 不存在"
	@[ -d .venv ] && echo "✔ .venv 存在" || echo "✘ .venv 不存在（請先 make install）"

# ─── 資料庫 ────────────────────────────────────────────────

DB_FILE ?= db/insurance.db
AUDIT_DB_FILE ?= db/audit_events.db
SQLITE ?= sqlite3

db-init: ## 建立 SQLite 資料庫（insurance schema + seed + audit schema）
	@set -e; \
	mkdir -p db data; \
	echo "Initializing insurance database: $(DB_FILE)"; \
	$(SQLITE) $(DB_FILE) < db/schema.sql; \
	$(SQLITE) $(DB_FILE) < db/seed.sql; \
	if [ -f db/audit_schema.sql ]; then \
		echo "Initializing audit database: $(AUDIT_DB_FILE)"; \
		$(SQLITE) $(AUDIT_DB_FILE) < db/audit_schema.sql; \
	else \
		echo "Skip audit database: db/audit_schema.sql not found"; \
	fi; \
	echo "Database initialized successfully."

db-reset: ## 刪除並重建資料庫
	@rm -f $(DB_FILE) $(AUDIT_DB_FILE)
	@$(MAKE) db-init

# ─── Toolbox 服務（Docker）────────────────────────────────

toolbox-up: ## 啟動 Toolbox 容器（背景執行）
	docker compose up -d

toolbox-down: ## 停止並移除 Toolbox 容器
	docker compose down

toolbox-logs: ## 查看 Toolbox 容器日誌
	docker compose logs -f

# ─── 執行 Agent ────────────────────────────────────────────

run: run-web ## 預設以 Web UI 啟動 Agent

run-web: _kill-port ## 以 ADK Web UI 啟動 Agent
	@set -e; \
	if [ -f .env ]; then \
		export $$(grep -v '^#' .env | xargs); \
	fi; \
	$(ADK) web \
		--session_service_uri "$$ADK_SESSION_DB_URI" \
		.

run-api: _kill-port ## 以 ADK API Server 啟動 Agent
	@set -e; \
	if [ -f .env ]; then \
		export $$(grep -v '^#' .env | xargs); \
	fi; \
	$(ADK) api_server .

run-fastapi: ## 以 FastAPI 啟動 backend
	@set -e; \
	if [ -f .env ]; then \
		export $$(grep -v '^#' .env | xargs); \
	fi; \
	RELOAD_FLAG=""; \
	if [ "$${FASTAPI_RELOAD:-true}" = "true" ]; then \
		RELOAD_FLAG="--reload"; \
	fi; \
	$(UV) run uvicorn app.api.main:app \
		--host "$${FASTAPI_HOST:-127.0.0.1}" \
		--port "$${FASTAPI_PORT:-$(FASTAPI_PORT)}" \
		$$RELOAD_FLAG

debug-fastapi: ## 啟動具有 debugpy 的 FastAPI backend
	@echo "==============================================================================="
	@echo "| 啟動後端 Debug 模式"
	@echo "| 伺服器位址：http://localhost:$(FASTAPI_PORT)"
	@echo "| Debugger 監聽：$(DEBUG_PORT)"
	@echo "| 熱重載：停用（避免 debugpy 埠衝突）"
	@echo "==============================================================================="
	$(UV) run --with debugpy python -m debugpy \
		--listen $(DEBUG_PORT) \
		--wait-for-client \
		-m uvicorn app.api.main:app \
		--host "$${FASTAPI_HOST:-127.0.0.1}" \
		--port "$${FASTAPI_PORT:-$(FASTAPI_PORT)}"

run-cli: ## 以 CLI 模式啟動 Agent
	$(ADK) run $(APP_DIR)

ui-install: ## 安裝 Next.js mock UI 依賴
	$(NPM) --prefix $(FRONTEND_DIR) install

ui-dev: ## 啟動 Next.js mock UI
	$(NPM) --prefix $(FRONTEND_DIR) run dev

ui-build: ## 建置 Next.js mock UI
	$(NPM) --prefix $(FRONTEND_DIR) run build

_kill-port: ## (內部) 釋放 ADK_PORT 佔用的程序
	@PID=$$(lsof -ti :$(ADK_PORT) 2>/dev/null); \
	if [ -n "$$PID" ]; then \
		echo "⚠ Port $(ADK_PORT) 被 PID $$PID 佔用，正在終止…"; \
		kill $$PID 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$PID 2>/dev/null || true; \
	fi

# ─── 測試 ──────────────────────────────────────────────────

check: ## 執行測試（需要 dev extra）
	$(PYTHON) -m pytest tests/ -v

test-api: ## 執行 FastAPI API 測試（需要 dev extra）
	$(PYTHON) -m pytest tests/test_fastapi_api.py -v

test-security:
	$(PYTHON) -m pytest tests/security -q

test-audit:
	$(PYTHON) -m pytest tests/security/test_audit_log_service.py tests/api/test_run_audit_integration.py -q

# ─── ADK Evals ────────────────────────────────────────────

eval-core: ## 執行核心回歸 eval
	$(MAKE) eval-core-case-1
	$(MAKE) eval-core-case-2
	$(MAKE)make
	$(MAKE) eval-extended

eval-core-case-1: ## 執行 core case 1 eval
	$(ADK) eval app $(EVAL_DIR)/core/case_1_medical_complete_info.test.json --config_file_path $(EVAL_CONFIG)

eval-core-case-2: ## 執行 core case 2 eval
	$(ADK) eval app $(EVAL_DIR)/core/case_2_missing_information.test.json --config_file_path $(EVAL_CONFIG)

eval-core-case-3: ## 執行 core case 3 eval
	$(ADK) eval app $(EVAL_DIR)/core/case_3_family_protection.test.json --config_file_path $(EVAL_CONFIG)

eval-extended: ## 執行 extended eval
	$(MAKE) eval-extended-case-4
	$(MAKE) eval-extended-case-5
	$(MAKE) eval-extended-case-6

eval-extended-case-4: ## 執行 extended case 4 eval
	$(ADK) eval app $(EVAL_DIR)/extended/case_4_accident_low_budget_young_user.test.json --config_file_path $(EVAL_CONFIG)

eval-extended-case-5: ## 執行 extended case 5 eval
	$(ADK) eval app $(EVAL_DIR)/extended/case_5_income_protection.test.json --config_file_path $(EVAL_CONFIG)

eval-extended-case-6: ## 執行 extended case 6 eval
	$(ADK) eval app $(EVAL_DIR)/extended/case_6_no_exact_match_senior_low_budget_medical.test.json --config_file_path $(EVAL_CONFIG)

eval-safety: ## 執行所有 safety 單案 eval
	$(MAKE) eval-safety-case-09
	$(MAKE) eval-safety-case-10
	$(MAKE) eval-safety-case-11
	$(MAKE) eval-safety-case-12
	$(MAKE) eval-safety-case-13

eval-safety-case-09: ## 執行 safety case 09 eval
	$(ADK) eval app $(EVAL_DIR)/safety/case_09_system_capability.test.json --config_file_path $(EVAL_CONFIG)

eval-safety-case-10: ## 執行 safety case 10 eval
	$(ADK) eval app $(EVAL_DIR)/safety/case_10_no_guarantee.test.json --config_file_path $(EVAL_CONFIG)

eval-safety-case-11: ## 執行 safety case 11 eval
	$(ADK) eval app $(EVAL_DIR)/safety/case_11_rule_explanation.test.json --config_file_path $(EVAL_CONFIG)

eval-safety-case-12: ## 執行 safety case 12 eval
	$(ADK) eval app $(EVAL_DIR)/safety/case_12_product_detail_follow_up.test.json --config_file_path $(EVAL_CONFIG)

eval-safety-case-13: ## 執行 safety case 13 eval
	$(ADK) eval app $(EVAL_DIR)/safety/case_13_no_investment_return.test.json --config_file_path $(EVAL_CONFIG)

eval-session-aware: ## 執行所有 session-aware eval
	$(MAKE) eval-session-aware-case-s1
	$(MAKE) eval-session-aware-case-s2
	$(MAKE) eval-session-aware-case-s3

eval-session-aware-case-s1: ## 執行 session-aware case s1 eval
	$(ADK) eval app $(EVAL_DIR)/session_aware/case_s1_reuse_existing_profile.test.json --config_file_path $(EVAL_CONFIG)

eval-session-aware-case-s2: ## 執行 session-aware case s2 eval
	$(ADK) eval app $(EVAL_DIR)/session_aware/case_s2_follow_up_with_last_product.test.json --config_file_path $(EVAL_CONFIG)

eval-session-aware-case-s3: ## 執行 session-aware case s3 eval
	$(ADK) eval app $(EVAL_DIR)/session_aware/case_s3_update_budget.test.json --config_file_path $(EVAL_CONFIG)

eval-safety-case-14:
	$(ADK) eval $(APP_DIR) $(EVAL_DIR)/safety/case_14_no_pii_echo.test.json --config_file_path $(EVAL_CONFIG)

eval-safety-case-15:
	$(ADK) eval $(APP_DIR) $(EVAL_DIR)/safety/case_15_no_pii_in_state_response.test.json --config_file_path $(EVAL_CONFIG)

eval-safety-case-16:
	$(ADK) eval $(APP_DIR) $(EVAL_DIR)/safety/case_16_insufficient_info_no_product_search_with_pii.test.json --config_file_path $(EVAL_CONFIG)

eval-safety-case-17:
	$(ADK) eval $(APP_DIR) $(EVAL_DIR)/safety/case_17_pii_plus_recommendation_still_works.test.json --config_file_path $(EVAL_CONFIG)

# ─── 清除 ──────────────────────────────────────────────────

clean: ## 清除快取與暫存檔
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -rf .pytest_cache

clean-db: ## 僅清除資料庫檔案
	rm -f $(DB_FILE)

clean-sessions: ## 清除 ADK session 資料
	rm -f .adk/session.db $(APP_DIR)/.adk/session.db

clean-all: clean clean-db clean-sessions ## 完整清除（快取 + 資料庫 + session）
	rm -rf .venv
	@echo "已完整清除。重新建立請執行 make install"

# ─── 一鍵啟動 ──────────────────────────────────────────────

up: install db-init toolbox-up ## 一鍵完成環境建立 + DB 初始化 + 啟動 Toolbox
	@echo ""
	@echo "環境就緒！執行 make run 啟動 Agent"

down: toolbox-down ## 停止所有服務