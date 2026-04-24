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
