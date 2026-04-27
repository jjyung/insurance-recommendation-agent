# FastAPI 後端設計藍圖

本文件定義 app 目錄的第一階段重構後架構，目標是在不破壞現有 API 契約的前提下，把 FastAPI 控制層、ADK 執行層、Session 狀態契約與應用流程切開。

## 設計目標

- 保持既有 API 邊界不變：
  - POST /api/agent/run
  - GET/POST/DELETE /api/agent/sessions
  - GET /healthz
  - GET /readyz
- 保持既有 SSE envelope 不變：meta、timeline、state、message、done、error。
- 保持既有 ADK state key 不變，尤其是 user:* 與 _ui_* 相關欄位。
- 將路由從流程編排中抽離，讓 route 只負責 transport。
- 將 runtime singleton 收斂到可管理的 container，而不是讓 route 直接散用全域 cache。

## 目前採用的分層

```text
app/
├── agent.py                     # ADK agent 組裝入口
├── app_runtime.py               # 相容層，轉接到 core/config.py
├── api/                         # FastAPI transport 層
│   ├── dependencies.py          # container 與 request-scoped 取得方式
│   ├── main.py                  # app entrypoint、middleware、health endpoints
│   ├── schemas.py               # HTTP request/response models
│   ├── session_service.py       # session repository-oriented helpers
│   ├── streaming.py             # SSE transport helpers
│   ├── presenters/
│   │   └── session_presenter.py # session -> UI view model projection
│   └── mappers/
│       └── adk_event_mapper.py  # ADK event -> envelope mapping
│   └── routes/
│       ├── run.py               # agent run controller
│       └── sessions.py          # session CRUD controller
├── application/                 # use case / orchestration 層
│   ├── agent_run_service.py     # 執行 agent 與串流 envelope
│   ├── health.py                # readiness probe orchestration
│   └── session_facade.py        # session CRUD 與 state 讀取
├── core/                        # runtime foundation
│   ├── config.py                # 環境設定解析
│   └── container.py             # config/agent/session/runner singleton 組裝
├── domain/                      # 穩定業務契約
│   └── session_state.py         # session state keys 與 UI/private key 規則
└── tools/                       # ADK tools 與 local helper
```

## 檔案責任清單

### 1. agent 組裝層

- app/agent.py
  - 只負責 prompt 載入與 ADK agent 建立。
  - 提供 create_agent(config) 給 container、CLI、測試共用。
  - 保留 root_agent 供 ADK 入口使用。

### 2. core 層

- app/core/config.py
  - 單一來源解析所有 runtime 設定。
  - 不包含業務流程。

- app/core/container.py
  - 建立 AppContainer。
  - 統一組裝 config、agent、session service、runner。
  - 讓 FastAPI 啟動時可把 runtime state 掛到 app.state。

### 3. domain 層

- app/domain/session_state.py
  - 管理 user:*、最後推薦商品與 _ui_* key 的契約。
  - 避免 session key 字串散落在多處。

### 4. application 層

- app/application/session_facade.py
  - 封裝 session list/create/delete/get_state。
  - 讓 route 不直接操作 ADK session service。
  - 回傳的列表資料由 presenter 決定顯示形狀。

- app/application/agent_run_service.py
  - 負責 agent run 的應用流程：
    - 使用 session
    - 執行 runner
    - 合併 state patch
    - 產生 done/error envelope

- app/application/health.py
  - 負責 readiness 檢查流程。
  - 將同步 requests 包在 async-friendly probe 內。

### 5. API transport 層

- app/api/main.py
  - 建立 FastAPI app。
  - 注入 container。
  - 註冊 router 與 health endpoints。

- app/api/routes/run.py
  - 驗證 request。
  - 呼叫 AgentRunService。
  - 回傳 StreamingResponse。

- app/api/routes/sessions.py
  - 驗證 request。
  - 呼叫 SessionFacade。
  - 回傳 JSON。

- app/api/presenters/session_presenter.py
  - 只處理 session state 公開化與 UI view model 投影。

- app/api/mappers/adk_event_mapper.py
  - 只處理 ADK event 到 API envelope 的映射。

- app/api/streaming.py
  - 維持目前前端相容的 SSE transport 行為。
  - 包含編碼與 runner 迭代，不再承擔主要事件映射責任。

## 請求流程

### Session CRUD

```text
FastAPI Route
-> SessionFacade
-> ADK SessionService
-> Session 投影為 UI 結構
```

### Agent Run SSE

```text
FastAPI Route
-> AgentRunService
-> Runner.run_async
-> ADK Event
-> envelope 映射
-> SSE stream
```

## 重構原則

- route 不寫業務流程。
- application service 不直接處理 HTTP response 類型。
- domain contract 不依賴 FastAPI。
- config 與 container 作為唯一 runtime 組裝入口。
- session state key 不重新命名。
- 先維持前端契約，再逐步優化內部實作。

## 下一階段建議

### Phase 2

- 把 app/api/session_service.py 與 app/api/streaming.py 再往下拆成純 presenter / mapper。
- 新增統一錯誤模型與 request id middleware。
- 將 user_id 從固定 config 改為可注入的 auth context。
- 補上 application/domain 層的單元測試，而不只驗 FastAPI route。

### Phase 3

- 將 Toolbox 健康檢查改為正式 adapter。
- 把 observability、structured logging、latency metrics 收進 core/infrastructure。
- 視需要補充 reference implementation 文件，說明 SQL 工具與查詢規則的對照關係。