# Deployment

## Agent Starter Pack

enhance is using your current folder name as project name by default, and that name is over the 26-char limit.

```bash
# 預設會使用 project dir name => Error: Project name 'insurance-recommendation-agent' exceeds 26 characters. Please use a shorter name.
uvx agent-starter-pack enhance

# 指定 shorter name
uvx agent-starter-pack enhance --name ins-reco-agent
```

base template: adk
agent directory: app
deployment target: cloud_run
session types: cloud_sql
ci/cd runner: google_cloud_build
gcp region: global

## 環境變數集中設定（Local / Deploy）

### Local（`.env`）

- `ADK_SESSION_DB_URI=sqlite+aiosqlite:///./db/adk_sessions.db`
- `MODEL_NAME=<your-model-name>`
- `TOOLBOX_SERVER_URL=http://127.0.0.1:5000`
- 其他本機測試用設定（如 `FASTAPI_RELOAD` / CORS）

### Deploy（Cloud Run Runtime Env）

`make deploy` 會更新以下 runtime env：

- `ADK_APP_NAME=ins_reco_agent`
- `FASTAPI_HOST=0.0.0.0`
- `FASTAPI_PORT=8080`
- `ADK_MEMORY_MODE=in_memory`
- `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT`
- `MODEL_NAME=$(DEPLOY_MODEL_NAME)`（預設 `gemini-3.1-flash-lite-preview`）
- `GOOGLE_GENAI_USE_VERTEXAI=1`
- `GOOGLE_CLOUD_LOCATION=global`
- `GOOGLE_CLOUD_PROJECT=<current gcloud project>`
- `TOOLBOX_SERVER_URL=http://127.0.0.1:5000`

> 為避免 revision 依賴程式 fallback（例如 `app/config.py` 預設 model），部署時會顯式設定 `MODEL_NAME`。
> Cloud Run 內部改為單一 image 雙進程（app + toolbox），不再需要額外 toolbox service URL。

### Deploy（Terraform 注入，Cloud SQL 相關）

`deployment/terraform/dev/service.tf` 會注入：

- `INSTANCE_CONNECTION_NAME`
- `DB_USER`
- `DB_NAME`
- `DB_PASS`（由 Secret Manager 提供）

程式邏輯會優先使用：

1. 若有 `ADK_SESSION_DB_URI`：直接使用
2. 否則若 `INSTANCE_CONNECTION_NAME/DB_USER/DB_NAME/DB_PASS` 都存在：自動組出 `postgresql+asyncpg://...`（Cloud SQL Postgres）
3. 再否則 fallback 到 SQLite：`sqlite+aiosqlite:///./db/adk_sessions.db`

> 因此 deploy 後通常不需要手動設定 `ADK_SESSION_DB_URI`，Terraform 提供的 DB env 足夠讓系統自動切到 Cloud SQL Postgres。

## Cloud Run Public Access (Dev)

Public access for Cloud Run is controlled by IAM binding (`roles/run.invoker` for `allUsers`), not only by ingress.  
`INGRESS_TRAFFIC_ALL` allows traffic routing, but unauthenticated invocation still requires the IAM member.

```
# Allow unauthenticated public access to Cloud Run service.
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.dev_project_id
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"

  depends_on = [google_cloud_run_v2_service.app]
}
```

After Terraform apply, verify with:

```bash
gcloud run services get-iam-policy <service-name> \
  --region <region> \
  --project <project>
```

Expected binding includes:

```text
role: roles/run.invoker
members:
- allUsers
```

```bash
make setup-dev-env
make deploy
```

## Troubleshooting: `Uploading sources` 很慢

如果在 `gcloud run deploy --source .` 卡在 `Uploading sources`，通常是因為上傳的 source context 太大。

本專案已新增以下檔案以縮小上傳內容：

- `.gcloudignore`
- `.dockerignore`

這兩個檔案會排除常見非部署必要內容，例如：

- `.venv/`, `.git/`, `__pycache__/`
- `tests/`, `notebooks/`, `docs/`, `deployment/`
- `frontend` build artifacts 與 `node_modules/`

部署前可先檢查實際上傳檔案：

```bash
gcloud meta list-files-for-upload
```

建議部署流程：

```bash
# 1) 確認上傳清單
gcloud meta list-files-for-upload

# 2) 部署到 Cloud Run
gcloud run deploy ins-reco-agent \
  --source . \
  --project dassa-lab \
  --region asia-east1
```

若仍偏慢，優先檢查是否有未被 ignore 的大型目錄或檔案。

## FastAPI Entrypoint 對齊

為了避免 Cloud Run 出現「container failed to start and listen on PORT=8080」，
目前啟動入口已統一使用 `make run-fastapi` 相同路徑：`app.api.main:app`。

已做的調整：

- 移除多餘的 `app/fast_api_app.py`
- Dockerfile 改為使用 `supervisord` 啟動雙進程（toolbox + app）
- Dockerfile 改用 Cloud Run 的 `PORT` 環境變數（預設 `8080`）
- Docker base image 改為 `python:3.12-slim`（符合 `pyproject.toml` 的 `requires-python >=3.12`）

目前 Dockerfile 啟動命令（容器主進程）：

```bash
supervisord -c /etc/supervisor/conf.d/supervisord.conf
```

本機與部署建議：

```bash
# Local
make run-fastapi

# Deploy
make deploy
```

健康檢查建議使用：

```bash
curl -i https://<service-url>/healthz
curl -i https://<service-url>/readyz
```

## Toolbox (Cloud Run) 設定

Cloud Run 採單一 image 雙進程：

- `supervisord` 同時啟動 toolbox 與 FastAPI
- toolbox 綁定 `127.0.0.1:5000`
- app 透過 `TOOLBOX_SERVER_URL=http://127.0.0.1:5000` 呼叫 toolbox
- 不需再部署第二個 toolbox Cloud Run service

啟動流程：

- `toolbox`: `/usr/local/bin/toolbox --config /workspace/db/tools.yaml --address 127.0.0.1 --port 5000`
- `app`: `uv run uvicorn app.api.main:app --host ${FASTAPI_HOST:-0.0.0.0} --port ${PORT:-8080}`（啟動前會等待 toolbox 5000 可連線）

一行部署：

```bash
make deploy
```

部署後建議檢查：

```bash
curl -i https://<service-url>/readyz
```

Toolbox deploy 常見失敗點（非 Cloud Build）：

- supervisor 沒起來（容器 log 應同時看到 toolbox 與 uvicorn）
- toolbox 啟動失敗（`/workspace/db/tools.yaml` 或 `insurance.db` 遺失）
- `TOOLBOX_SERVER_URL` 被誤設為外部網址（應為 `127.0.0.1:5000`）

Cloud SQL 常見失敗點：

- Secret/連線字串錯誤：檢查 `DB_PASS` 與 `ADK_SESSION_DB_URI` 是否一致且可用
- 權限不足：Cloud SQL user 需有 schema `CREATE TABLE` 權限

## Cloud SQL Postgres Driver 注意事項

本專案的 session store 在 Cloud Run 環境會使用 Cloud SQL Postgres。  
若 `ADK_SESSION_DB_URI`/實際連線使用 `postgresql+asyncpg://...`，必須安裝 `asyncpg` driver。

`pyproject.toml` 已補上：

```toml
"asyncpg>=0.30.0",
```

若缺少 driver，常見錯誤會是：

```text
Database related module not found for URL '<db_url>'
```

部署前建議流程：

```bash
# 1) 更新 lock file（讓 Docker build 吃到新依賴）
uv lock

# 2) 重新部署（重建 image）
make deploy
```
