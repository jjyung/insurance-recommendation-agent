# 專案概述與總結 (Overview & Summary)

本專案是一個以 Google ADK、MCP Toolbox for Databases、SQLite、FastAPI 與 Next.js 組成的保險推薦代理原型。它的目標不是直接產生正式投保建議，而是建立一條可互動、可追溯、可測試、可擴充的推薦流程：由 Agent 負責對話與決策，由受控工具負責資料查詢，由 API 與前端提供展示與整合介面。

目前專案已經從單純的 Agent demo，收斂成一個具備前後端分層、session 管理、SSE 串流回傳、受控工具調用與 evaluation 驗證能力的教學型 PoC。

---

## 一、目前專案定位

這個 repository 目前最適合的定位是：

- 保險推薦代理 PoC
- Google ADK × MCP Toolbox 整合示範
- 受控工具導向的 Agent 設計範例
- 後續產品化、知識檢索與正式資料源接入的基礎版本

它已具備可執行、可測試、可展示與可擴充的條件，但仍不是正式上線產品。

---

## 二、目前實際架構

目前系統的實際執行鏈如下：

```text
使用者
-> Next.js Workbench / API Proxy
-> FastAPI Backend
-> Google ADK Runner / Agent
-> Local Session Tools + ToolboxToolset
-> MCP Toolbox
-> db/tools.yaml
-> SQLite
```

各層角色如下：

- Next.js：提供前端 workbench、session 列表、訊息視圖與事件檢視面板
- FastAPI：提供 HTTP API、session CRUD、agent run SSE 串流、health/readiness endpoints
- Google ADK Agent：負責追問、工具選擇、結果整合與最終回覆
- Local Session Tools：讀寫使用者 profile 與最近推薦狀態
- ToolboxToolset：讓 ADK 透過 MCP 協定使用外部工具
- MCP Toolbox：載入 db/tools.yaml 中定義的 sources、tools、toolsets 與 prompts
- SQLite：提供商品、推薦規則、示範資料與 FAQ 資料表

相較於舊版純 Agent + Toolbox 的描述，現在的專案已經明確加入後端 API 分層與前端原型，因此總結文件也應反映這條完整路徑。

---

## 三、目前目錄與責任分工

### 1. app/

後端核心程式集中在 app/：

- agent.py：建立 ADK Agent、載入主 prompt、組裝 session tools 與 ToolboxToolset
- config.py：讀取環境變數與 runtime 設定
- container.py：建立 AppContainer，集中組裝 agent、runner、session store 與 services
- session_state.py：集中定義 session / user state 契約
- api/：FastAPI 入口、Pydantic schema、routes 與依賴注入
- services/：封裝 agent run、session 管理、readiness 檢查等應用邏輯
- prompts/：管理 insurance_agent_prompt.txt
- tools/：提供 ADK 可直接呼叫的本地 session tools

這表示專案後端已從單檔 demo 演進為明確的 transport / service / runtime 分層。

### 2. db/

資料層與工具定義集中在 db/：

- schema.sql：建立商品、規則、FAQ、示範使用者等資料表
- seed.sql：示範資料初始化
- tools.yaml：定義 MCP Toolbox 的資料來源、保險查詢工具、工具群組與 prompt 模板

目前推薦流程仍以受控工具為主，不依賴模型自由產生 SQL。

### 3. frontend/

前端已存在一個可執行的 Next.js 原型介面：

- app/page.tsx：Workbench 入口頁
- components/adk-workbench.tsx：對話介面、session 切換、事件與 state 檢視
- app/api/...：代理前端到後端的 API routes
- lib/mock-data.ts：離線或示範模式使用的 mock 資料

因此目前更精確的描述不是「尚未有前端」，而是「已有 workbench 型原型前端，但尚未產品化」。

### 4. docs/

文件已拆成多份主題文件：

- 01_overview.md：專案摘要與總覽
- 02_architecture.md：後端模組切分與依賴方向
- 03_core_flows.md：核心互動與工具調用流程
- 04_agent_design.md：Prompt / Tool 分工與治理
- 05_demo_guide.md：展示與 demo 腳本

### 5. tests/

測試資產包含兩個面向：

- test_fastapi_api.py：驗證 health、session CRUD、SSE run stream 等 API 行為
- evals/：ADK eval 測試集，覆蓋 core、extended、safety 與 session-aware 場景

這使專案不只是靜態展示，而是具備基本驗證路徑。

---

## 四、目前完成的核心能力

### 1. 互動式需求蒐集

Agent 會先檢查是否具備年齡、預算與主要保障目標；若資訊不足，先追問而不是直接推薦。

### 2. 受控保險工具查詢

目前主要工具包括：

- search_medical_products
- search_accident_products
- search_family_protection_products
- search_income_protection_products
- get_product_by_name
- get_product_detail
- get_recommendation_rules

這些工具由 db/tools.yaml 定義，降低自由 SQL 帶來的不穩定性。

### 3. Session-aware 對話

本地 session tools 已可維護：

- 使用者基本 profile
- 最近推薦商品名稱與 ID
- 當前對話中的補充狀態

這讓系統能在同一 session 中沿用已知條件，減少重複提問。

### 4. 結構化回覆與可追溯事件

FastAPI run route 會將 Agent 執行結果轉為 SSE envelopes，將工具呼叫、工具結果、訊息串流與 state patch 一併送回前端。這讓 demo、除錯與驗證都更容易。

### 5. 文件化與測試化

目前專案已提供：

- README 與 Makefile 指令入口
- 架構、流程、代理治理、展示文件
- FastAPI API 測試
- ADK eval 測試案例

這些內容支撐了「可交付的 PoC」而不只是一次性的程式碼實驗。

---

## 五、技術組成與執行方式

### 後端

- Python 3.12
- FastAPI
- Google ADK
- ToolboxToolset / MCP Toolbox
- SQLite
- uv / setuptools

### 前端

- Next.js 15
- React 19
- TypeScript 5

### 執行與管理

- Makefile：統一安裝、資料庫初始化、後端啟動、前端啟動與 eval 指令
- Docker Compose：啟動 MCP Toolbox 容器

目前常見執行模式包括：

- make run-fastapi：啟動 FastAPI 後端
- make ui-dev：啟動 Next.js workbench
- make toolbox-up：啟動 MCP Toolbox
- make test-api：執行 FastAPI API 測試
- make eval-core / make eval-safety / make eval-session-aware：執行 ADK eval

---

## 六、目前已知邊界與限制

雖然專案已有前後端、工具層與測試骨架，但目前仍屬 PoC，主要限制包括：

- 商品與規則資料仍為示範資料
- 推薦結果仍屬初步篩選，不包含正式核保、理賠或報價流程
- session-aware 目前以單一 session 內的上下文延續為主
- FAQ 與條款知識尚未完成 semantic retrieval 整合
- 前端目前偏向 workbench / demo 介面，尚未是正式產品 UI
- 安全設定、權限控管、正式資料源與 CI 自動化仍待補強

換句話說，這個專案現在最大的價值，是把 Agent orchestration、受控工具查詢、API transport 與展示層串成一條清楚的原型路徑。

---

## 七、下一階段建議方向

若要往下一階段推進，建議優先順序如下：

### 第一階段

- 補強安全設定與部署邊界
- 補齊更多 API 與回歸測試
- 清理與統一文件內容，避免舊版敘述殘留

### 第二階段

- 把 FAQ / 條款知識納入 retrieval 流程
- 強化推薦排序與多商品比較邏輯
- 擴充跨 session 的使用者 profile 記憶策略

### 第三階段

- 接正式資料源
- 製作正式產品化前端體驗
- 加入認證、授權、審計與監控能力

---

## 八、一句話總結

本專案目前是一個以 Google ADK、FastAPI、Next.js、MCP Toolbox 與 SQLite 組成的保險推薦代理原型，已完成受控工具查詢、session-aware 對話、SSE 串流回應與 eval 驗證骨架，可作為後續產品化與知識檢索擴充的基礎。