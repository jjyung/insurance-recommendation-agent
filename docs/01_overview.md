# 專案概述與總結 (Overview & Summary)

<!-- Content from summary.md -->
# 最終專案總結

本專案完成了一個以 **Google ADK**、**MCP Toolbox for Databases**、**ToolboxToolset**、**tools.yaml**、**SQLite** 與 **Vertex AI** 為核心的 **保險推薦代理原型**。

本專案的重點，不只是做出一個能回答問題的聊天代理，而是建立一套 **可互動、可追溯、可維護、可擴充** 的 Agent 工具架構，讓保險推薦流程不依賴模型自由產生 SQL，而是透過 **MCP Toolbox 中以 `tools.yaml` 定義的受控工具** 完成商品查詢與規則解釋。

---

## 一、專案最終架構

本專案最終採用以下架構：

```text
使用者
-> Google ADK Agent
-> ToolboxToolset
-> MCP Toolbox
-> tools.yaml
-> SQLite insurance.db
```

各層角色如下：

* **Google ADK Agent**：負責對話流程、追問、工具選擇與最終推薦輸出
* **ToolboxToolset**：負責讓 ADK Agent 透過 MCP 協定連接 MCP Toolbox
* **MCP Toolbox**：負責載入 `tools.yaml` 並提供工具
* **tools.yaml**：集中定義 `source`、`tool`、`toolset`、`prompt`
* **SQLite**：提供保險商品、推薦規則、FAQ 與示範資料

---

## 二、專案完成的核心能力

本專案目前已完成以下能力：

### 1. 互動式需求蒐集

當使用者資訊不足時，Agent 會先追問，而不是直接推薦商品。

例如：

* 年齡
* 預算
* 主要保障目標

---

### 2. 保險專用工具查詢

透過 `tools.yaml` 定義受控工具，而非使用自由 SQL。

目前已完成的工具包括：

* `search_medical_products`
* `search_accident_products`
* `search_family_protection_products`
* `search_income_protection_products`
* `get_product_detail`
* `get_recommendation_rules`

---

### 3. 規則驅動推薦

除了商品查詢外，Agent 還能透過 `get_recommendation_rules` 補充：

* 為什麼推薦這個商品
* 為什麼某些情境優先考慮特定商品類型
* 如何將商品推薦與家庭責任、收入中斷等保障需求連結

---

### 4. 結構化推薦輸出

最終推薦回覆已能穩定包含：

* 推薦商品名稱
* 推薦原因
* 條件限制
* 等待期
* 除外條款
* 規則依據
* 保守聲明

---

### 5. 可追溯工具呼叫流程

透過 ADK trace，可驗證 Agent 實際呼叫了哪些工具，例如：

* `search_medical_products`
* `search_family_protection_products`
* `get_recommendation_rules`

這讓整個推薦流程具備更高的可驗證性。

---

## 三、專案設計上的關鍵成果

本專案最重要的成果，不是單純做出推薦結果，而是完成了以下三個設計轉換：

### 1. 從自由 SQL 轉向受控工具

一開始雖然可透過 prebuilt SQLite 工具執行 `execute_sql`，但最終已收斂為：

* 不使用自由 SQL 作為主推薦機制
* 改以 `tools.yaml` 定義保險專用工具
* 由 Agent 選工具，而不是自己寫 SQL

---

### 2. 從本地 Python tools 轉向 MCP Toolbox YAML 配置

專案中曾先以本地 Python function 驗證推薦流程，之後再完整收斂到：

* `source`
* `tool`
* `toolset`
* `prompt`

都由 `tools.yaml` 統一管理。

這使得系統更接近正式 MCP Toolbox 的配置思維。

---

### 3. 從單一查詢工具轉向場景化工具設計

工具已從單一搜尋工具拆分成不同保障場景，例如：

* 醫療保障
* 意外保障
* 家庭保障
* 收入中斷保障

這讓 Agent 的工具選擇更清楚，也讓每個場景更容易測試與維護。

---

## 四、已完成的專案文件

本專案目前已整理出完整交付文件，包括：

* `README.md`
* `docs/architecture.md`
* `docs/prompt_tool_contract.md`
* `docs/demo_script.md`
* `docs/limitations.md`
* `tests/test_cases.md`

這使得專案不只可執行，也可用於：

* 技術展示
* 團隊分享
* 架構匯報
* 教學使用
* 作品集展示

---

## 五、目前專案的定位

本專案目前最適合的定位是：

* 保險推薦代理 PoC
* MCP Toolbox × ADK 整合示範
* `tools.yaml` 為核心的 Agent 工具架構教學專案
* 後續產品化與語意檢索擴充的基礎版本

它已經是：

* 可運行
* 可測試
* 可展示
* 可驗證
* 可擴充

但仍不是正式上線產品。

---

## 六、目前已知限制

目前專案仍有以下限制：

* 商品資料為示範資料
* 尚未實作正式核保流程
* 保費邏輯為簡化版本
* 規則涵蓋範圍有限
* 尚未加入 production 安全設定
* 尚未加入 embedding / semantic retrieval
* 尚未接正式資料源
* 尚未有正式前端介面

這些限制已在 `docs/limitations.md` 中整理清楚。

---

## 七、下一階段建議方向

若要繼續往下一階段發展，建議優先順序如下：

### 第一階段

* 補強安全設定
* 完善測試矩陣
* 整理最終展示文件

### 第二階段

* 加入 FAQ semantic retrieval
* 加入條款與除外責任語意檢索
* 將 embedding 納入 MCP Toolbox 教學模組

### 第三階段

* 切換正式資料源
* 加入正式前端 UI
* 補齊權限控管與上線架構

---

## 八、專案總結一句話版本

本專案完成了一個以 **`tools.yaml + ToolboxToolset + MCP Toolbox`** 為核心、可透過 **Google ADK** 進行對話與工具調度的 **保險推薦代理原型**，具備追問、商品篩選、規則解釋、保守聲明與可追溯工具呼叫能力，可作為後續產品化與知識檢索擴充的基礎。

---

## 九、專案總結完整版

這個專案的真正價值，不只是「讓模型推薦保險」，而是建立了一個 **清楚分工的 Agent 工具架構**：

* Agent 負責判斷怎麼問、怎麼選、怎麼說
* Toolbox 負責受控地查資料
* `tools.yaml` 負責定義工具能力
* 資料庫只作為資料來源，而不是讓模型自由操作的對象

這樣的設計比起讓模型直接自由查資料，更適合：

* 企業內部 Agent PoC
* 受控資料查詢場景
* 可解釋推薦流程
* 後續產品化擴充

因此，本專案已成功達成最初的核心目標：

> **透過 MCP Toolbox 與 Google ADK，完成一個以 `tools.yaml` 為核心的保險推薦代理完整專案設計。**


---

<!-- Content from project.md -->
# Insurance Recommendation Agent 專案文件

## 1. 專案概述

本專案以 **Google ADK** 作為代理框架，結合 **MCP Toolbox for Databases** 與 **SQLite**，實作一個可互動、可解釋、具基本 safety 邊界與 session-aware 能力的保險推薦代理。

專案目標不是直接做正式投保建議，而是建立一個：

* 能蒐集使用者需求
* 能依據結構化資料查詢候選商品
* 能提供保守、可解釋的初步推薦
* 能避免虛構商品與不當承諾
* 能在同一個 session 內記住已知條件，減少重複提問
* 能透過 ADK evaluations 做系統化驗證

本專案定位為 **教學型 prototype**，重點在於展示：

1. ADK Agent 設計
2. MCP Toolbox + `tools.yaml` 的整合方式
3. prompt 與工具路徑設計
4. session-aware 對話體驗
5. evaluation-driven 開發流程

---

## 2. 技術架構

### 2.1 架構總覽

```text
User
 -> ADK Agent
 -> Session State Tools / Prompt Policy
 -> ToolboxToolset
 -> MCP Toolbox Server
 -> tools.yaml
 -> SQLite (insurance.db)
```

### 2.2 核心元件

* **Google ADK**：負責 agent orchestration、工具呼叫、session/state 管理、evaluation
* **MCP Toolbox for Databases**：將 SQLite 查詢以工具形式提供給 agent
* **SQLite**：存放保險商品、推薦規則、FAQ、示範 profile 資料
* **Vertex AI / Gemini**：作為推理模型
* **ADK Eval**：驗證工具路徑、最終回答品質與 safety 邊界

---

## 3. 專案目錄結構

```text
insurance-recommendation-agent/
├─ .env
├─ README.md
├─ requirements.txt
├─ app/
│  ├─ __init__.py
│  ├─ agent.py
│  ├─ prompts/
│  │  └─ insurance_agent_prompt.txt
│  └─ tools/
│     └─ session_tools.py
├─ db/
│  ├─ insurance.db
│  ├─ schema.sql
│  ├─ seed.sql
│  └─ tools.yaml
├─ data/
└─ tests/
   ├─ test_cases.md
   └─ evals/
      ├─ test_config.json
      ├─ insurance_core.test.json
      ├─ insurance_extended.test.json
      ├─ insurance_case12_only.test.json
      ├─ safety/
      │  ├─ case_09_system_capability.test.json
      │  ├─ case_10_no_guarantee.test.json
      │  ├─ case_11_rule_explanation.test.json
      │  ├─ case_12_product_detail_follow_up.test.json
      │  └─ case_13_no_investment_return.test.json
      └─ session_aware/
         ├─ case_s1_reuse_existing_profile.test.json
         ├─ case_s2_follow_up_with_last_product.test.json
         └─ case_s3_update_budget.test.json
```

---

## 4. 資料庫設計

### 4.1 資料表

本專案使用以下主要資料表：

* `insurance_products`

  * 商品主檔
  * 包含商品名稱、類型、年齡區間、保費區間、保障焦點、等待期、除外條款

* `recommendation_rules`

  * 推薦規則資料
  * 用於解釋推薦邏輯，而不是取代商品查詢

* `user_profiles_demo`

  * 示範用使用者資料
  * 主要供開發與驗證場景使用

* `faq_knowledge`

  * FAQ 與知識補充
  * 可作為後續擴充知識型互動的基礎

### 4.2 商品類型與目標映射

代理的主要保障目標如下：

* `medical`
* `accident`
* `life`
* `family_protection`
* `income_protection`

對應商品類型映射：

* `medical -> medical`
* `accident -> accident`
* `life -> life`
* `family_protection -> life`
* `income_protection -> critical_illness`（必要時可延伸為壽險補充邏輯）

---

## 5. MCP Toolbox 與 tools.yaml 設計

### 5.1 設計原則

本專案一開始曾使用通用 SQL 工具進行推薦，但後續改為：

* **推薦任務優先使用語意明確的保險專用工具**
* 避免讓模型過度依賴通用 SQL 拼接
* 提升工具選擇穩定性
* 提高 eval 可預測性

### 5.2 已定義工具

目前主要工具包括：

* `search_medical_products`
* `search_accident_products`
* `search_family_protection_products`
* `search_income_protection_products`
* `get_product_by_name`
* `get_product_detail`
* `get_recommendation_rules`

### 5.3 tools.yaml 設計重點

`tools.yaml` 將：

* source 定義為 SQLite source
* tool 定義為具體 SQL 封裝
* toolset 分為推薦用途與除錯用途
* prompt 模板納入 Toolbox 層

### 5.4 Toolbox prompts

已在 `tools.yaml` 中加入 prompt 模板，例如：

* `insurance_recommendation_response_template`
* `insurance_followup_question_template`
* `insurance_disclaimer_template`

這些模板目前主要作為設計與未來擴充基礎；實際回答仍由 ADK agent prompt 與工具結果主導。

---

## 6. ADK Agent 設計

### 6.1 Agent 職責

agent 的核心責任是：

* 判斷目前資訊是否足夠
* 決定是否追問
* 選擇正確工具
* 整合工具結果為自然語言回覆
* 避免虛構與不當承諾

### 6.2 工具掛載策略

目前 agent 掛載兩類工具：

1. **Session state tools**

   * `get_user_profile_snapshot`
   * `save_user_profile`
   * `save_last_recommendation`
   * `clear_last_recommendation`

2. **ToolboxToolset**

   * 由 MCP Toolbox 提供保險查詢工具

### 6.3 Prompt 策略

prompt 設計包含：

* 核心必要資訊檢查
* 保障目標對應工具規則
* 推薦輸出格式要求
* safety 與保守聲明要求
* session-aware 對話規則

---

## 7. Session-aware 設計

### 7.1 目標

避免 agent 在同一個 session 內反覆詢問：

* 年齡
* 預算
* 主要保障目標
* 最近討論商品

以提升客戶體驗。

### 7.2 State Schema

#### User-level state

* `user:age`
* `user:budget`
* `user:main_goal`
* `user:marital_status`
* `user:has_children`
* `user:existing_coverage`
* `user:risk_preference`
* `user:last_recommended_product_name`
* `user:last_recommended_product_id`

#### Session-level state

* `current_goal_confirmed`
* `current_product_name`
* `current_product_id`
* `current_recommendation_reason`
* `needs_clarification`

### 7.3 Session tools

#### `get_user_profile_snapshot`

讀取目前 session / user state，整理出保險推薦相關欄位。

#### `save_user_profile`

把使用者新提供的條件寫回 state。

#### `save_last_recommendation`

將最近一次推薦商品保存，方便後續追問延續上下文。

#### `clear_last_recommendation`

清除最近商品指標。

### 7.4 互動策略

* 若已有核心必要資訊，先確認是否沿用
* 若使用者只做延伸追問，優先沿用既有商品上下文
* 若使用者只更新單一欄位，視為 state update，而非重新蒐集全部條件

---

## 8. 推薦流程設計

### 8.1 標準推薦流程

1. 檢查 session/user state
2. 確認是否已有必要資訊
3. 若不足，追問缺少欄位
4. 若足夠，依目標選擇對應 `search_*` 工具
5. 必要時用 `get_recommendation_rules` 補充規則依據
6. 必要時用 `get_product_detail` 補充細節
7. 輸出推薦商品與理由
8. 寫入 `save_last_recommendation`
9. 加上保守聲明

### 8.2 商品延伸追問流程

1. 讀取 `get_user_profile_snapshot`
2. 若有 `user:last_recommended_product_name` 或 `user:last_recommended_product_id`
3. 優先延續既有商品上下文
4. 用 `get_product_by_name` 或 `get_product_detail` 補查細節
5. 直接回答等待期 / 除外條款 / 商品摘要

---

## 9. Evaluation Strategy

本專案採用 **evaluation-driven** 方式逐步擴充功能。

### 9.1 共用評測設定

`tests/evals/test_config.json`

* `tool_trajectory_avg_score`
* `final_response_match_v2`

### 9.2 Core Set

`insurance_core.test.json`

驗證：

* 完整資訊推薦
* 資訊不足追問
* 家庭保障基本推薦

### 9.3 Extended Set

`insurance_extended.test.json`

驗證：

* 年輕低預算意外保障
* 收入中斷保障
* 無完全符合條件時的誠實回覆

### 9.4 Safety Set

已拆為單案檔案，主要驗證：

* 不可保證核保 / 理賠
* 不可虛構投資報酬
* 系統能力說明
* 推薦規則解釋
* 商品細節追問

### 9.5 Session-aware Set

已拆為 3 個單案：

* `case_s1_reuse_existing_profile.test.json`
* `case_s2_follow_up_with_last_product.test.json`
* `case_s3_update_budget.test.json`

驗證：

* 重用既有 profile
* 延續最近推薦商品上下文
* 單欄位更新而不重問全部條件

---

## 10. 目前驗證結果摘要

### 已通過

* Core set：通過
* Extended set：通過
* Case 12 only：通過
* Session-aware S1：通過
* Session-aware S2：通過
* Session-aware S3：通過

### 說明

這表示目前系統已可穩定做到：

* 正確工具選擇
* 保守且可解釋的推薦
* 邊界與 safety 控制
* 商品細節追問
* 同一 session 的上下文延續

---

## 11. 已知限制

### 11.1 MCP ToolboxToolset 在多案例 / 多輪 eval 中的 lifecycle 風險

在某些 ADK eval 多輪或批次情境下，`ToolboxToolset` 可能出現 session lifecycle 問題，例如：

* `Session is closed`

因此目前建議：

* 對於 safety 與 session-aware 場景，優先使用 **單案 eval files**
* 避免把高度依賴工具上下文的多輪案例直接綁成一個批次 gate

### 11.2 Session-aware 目前以同一 session 為主

目前完成的是 **session-aware 第一版**，主要解決：

* 同一 session 內記住條件
* 延續最近推薦商品

尚未正式實作：

* 跨 session 的長期記憶
* user-level memory service / profile DB

### 11.3 回答仍屬初步商品篩選

系統故意限制為：

* 不承諾核保
* 不承諾理賠
* 不承諾收益
* 不取代正式保險顧問與條款審閱

---

## 12. 後續 Roadmap

### 12.1 第 10 關：跨 session user profile / memory 設計

下一階段可擴充：

* 長期使用者偏好保存
* 跨 session 的 profile bootstrap
* user memory 與 session state 的分層策略

### 12.2 FAQ / Knowledge 型互動

可把 `faq_knowledge` 擴充為：

* FAQ 解釋工具
* 商品比較說明工具
* 條款摘要工具

### 12.3 更細緻的推薦策略

例如：

* 預算不足時的候選排序
* 多商品比較輸出
* 保障缺口說明
* 規則加權排序

### 12.4 更完整的 evaluation pipeline

可擴充：

* session memory 評測
* regression dashboard
* CI 驗證流程

---

## 13. 專案結論

本專案成功完成一個以 **Google ADK + MCP Toolbox + SQLite** 為核心的保險推薦代理 prototype，並透過結構化工具、prompt policy、session-aware state 與 evaluation-driven 開發方式，達成以下成果：

* 建立可查詢的保險商品推薦代理
* 將資料庫能力封裝為保險語意工具
* 以 ADK prompt 與工具策略控制推薦品質
* 建立 safety 與邊界控制
* 完成 session-aware 第一版互動體驗
* 建立可交付的測試與 eval 結構

這使本專案不只是單一 demo，而是一個具備後續擴充潛力的教學型代理系統基礎。


---

<!-- Content from limitations.md -->
# 已知限制（Known Limitations）

本文件整理目前這個保險推薦代理原型專案的已知限制，目的不是否定專案成果，而是讓系統邊界更清楚，方便後續：

- 驗收
- 風險溝通
- 專案規劃
- 下一階段擴充

本專案目前定位為 **PoC / Prototype**，而非正式上線產品。

---

## 一、資料層限制

### 1. 商品資料為示範資料
目前 `insurance_products` 中的商品、保費範圍、保障摘要、等待期與除外條款，皆為示範用途資料。

因此：

- 不代表真實保險商品
- 不可直接用於正式銷售
- 不可視為真實商品建議依據

---

### 2. 推薦規則為原型版本
目前 `recommendation_rules` 只涵蓋少量場景，例如：

- 年輕低預算
- 家庭責任
- 醫療保障
- 收入中斷保障

這些規則主要用於展示：

- Agent 如何調用規則工具
- Agent 如何補充推薦依據

但目前尚未涵蓋真實保險規劃所需的完整規則體系。

---

### 3. FAQ 知識庫尚未實際納入主流程
雖然資料庫中已有 `faq_knowledge` 資料表，但目前主推薦流程仍以商品與規則查詢為主。

目前尚未完成：

- FAQ 語意檢索
- 條款知識檢索
- 回答保險觀念問題的完整知識增強流程

---

## 二、推薦邏輯限制

### 4. 尚未實作正式核保邏輯
目前系統僅做 **初步商品篩選**，並未包含：

- 健康告知判斷
- 職業等級核保判斷
- 既往症核保限制
- 加費、除外承保、延期承保等邏輯

因此，系統不能判定使用者是否一定能投保。

---

### 5. 保費邏輯為簡化版本
目前工具中的預算條件主要是用來做初步候選商品篩選，例如：

- 年繳預算是否可達商品最低門檻
- 預算是否落在商品保費區間內

但真實保費通常還會受到更多因素影響，例如：

- 年齡
- 性別
- 職業
- 健康狀況
- 保額設計
- 附約搭配

因此，目前保費邏輯僅適合原型驗證，不適合真實報價。

---

### 6. 推薦排序仍為第一版
目前工具雖已根據場景拆分，例如：

- `search_medical_products`
- `search_family_protection_products`
- `search_income_protection_products`

但商品排序仍屬於第一版設計，主要根據：

- 商品類型
- 預算條件
- 最低保費排序
- 少量規則優先順序

未來若商品數量增加，仍需加入更細的排序策略。

---

## 三、Agent 層限制

### 7. 對話記憶仍有限
目前 Agent 主要針對單輪或短 session 的需求蒐集與推薦。

尚未完整實作：

- 長期使用者偏好記憶
- 客戶推薦歷史保存
- 多階段規劃流程記錄
- 顧問式長對話狀態管理

---

### 8. 追問策略仍為第一版
目前 Agent 已能在資訊不足時先追問：

- 年齡
- 預算
- 保障目標

但尚未做到更完整的訪談式邏輯，例如：

- 婚姻狀態引導
- 子女狀況引導
- 既有保單補問
- 風險偏好深入追問
- 動態調整追問順序

---

### 9. 回答格式仍偏原型導向
目前輸出已具備：

- 推薦原因
- 等待期
- 除外條款
- 規則依據
- 保守聲明

但在真實產品化時，仍可能需要更正式的格式，例如：

- 結構化推薦卡片
- 比較表
- 主推薦 / 備選推薦排序區分
- 更細的條款提示模板

---

## 四、Toolbox 與工具層限制

### 10. 工具仍屬第一版場景拆分
目前 `tools.yaml` 已成功拆成多個保險工具，但仍是第一版設計。

例如目前只拆到：

- 醫療保障
- 意外保障
- 家庭保障
- 收入中斷保障

未來仍可細化成更多工具，例如：

- 熟齡醫療補強
- 低預算基礎保障
- 家庭責任強化
- 醫療 + 重大疾病組合候選
- FAQ semantic retrieval tools

---

### 11. prompts 已配置，但尚未完整進入 Agent orchestration
目前 `tools.yaml` 中已成功加入：

- `insurance_recommendation_response_template`
- `insurance_followup_question_template`

Toolbox logs 也已成功顯示 prompts 被初始化。

但目前這些 prompts 主要仍屬於配置資產，尚未完整設計成：

- 由 ADK 顯式取得後再納入生成流程
- 形成完整 prompt orchestration 流程

因此，這部分仍屬可擴充能力，而非目前主流程的核心執行方式。

---

### 12. 尚未加入 embedding / semantic retrieval
目前系統主要是：

- 結構化商品查詢
- 結構化規則查詢

尚未加入：

- FAQ 語意檢索
- 條款語意檢索
- 商品描述相似度檢索
- 向量輔助推薦

因此，對於較開放式、概念型、條款型的問題，未來仍建議加入 embedding 模組。

---

## 五、安全與上線限制

### 13. 尚未完成 production 安全設定
目前 Toolbox logs 仍會出現：

- wildcard origins
- wildcard hosts

這表示目前配置仍偏向本機開發方便性，尚未加入正式安全限制，例如：

- `--allowed-origins`
- `--allowed-hosts`
- 更嚴格的網路邊界控制

---

### 14. 尚未加入正式授權與權限控管
目前專案仍為原型，尚未完整實作：

- 使用者身份驗證
- 角色權限管理
- 工具級存取控制
- 操作審計與更完整的行為記錄

因此不適合直接暴露給正式外部使用者。

---

### 15. 尚未接正式資料源
目前資料來源為 SQLite，適合原型與教學。

但正式環境通常還需考慮：

- 正式資料庫
- 多環境配置
- 權限分層
- 資料同步策略
- 監控與故障處理

---

## 六、產品化限制

### 16. 尚未提供正式前端體驗
目前使用者互動仍主要依賴：

- ADK Dev UI

這對開發與展示非常方便，但若要產品化，通常仍需要：

- 正式 Web UI
- 表單式輸入流程
- 比較型推薦介面
- 查詢結果卡片式展示

---

### 17. 尚未完成完整測試自動化
目前已有測試案例與工具驗證，但尚未完整建立：

- 自動化 regression tests
- 工具輸出驗證腳本
- 多場景對話測試流程
- CI/CD 測試整合

---

## 七、限制不代表失敗，而是邊界清楚

這些限制並不代表專案不足，反而表示目前這個 PoC 的邊界清楚：

- 它已能完成受控保險推薦原型
- 它已能展示 `tools.yaml + ToolboxToolset + MCP Toolbox` 的設計價值
- 它已能支撐下一階段擴充，例如：
  - embedding
  - FAQ retrieval
  - 正式資料源
  - 更完整安全控制
  - 更細的推薦工具

---

## 八、結論

本專案目前是一個 **可運行、可展示、可驗證、可擴充** 的保險推薦代理原型，但尚未達到正式上線條件。

其目前最適合的定位是：

- 教學專案
- 架構 PoC
- Agent + Toolbox 整合示範
- 後續產品化的基礎版本

若要進一步產品化，建議下一階段優先投入：

1. 安全設定
2. 正式資料源
3. FAQ / 條款 semantic retrieval
4. 更完整測試矩陣
5. 正式前端介面

---

