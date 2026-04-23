# 治理

本文件定義了保險推薦代理專案的責任邊界、變更所有權和 CI 驗證規則。

該專案基於以下技術構建：
- Google ADK 進行代理編排
- MCP Toolbox 用於伺服器端工具和提示配置
- `tools.yaml` 作為配置中心
- SQLite 作為示例資料來源

## 架構責任模型

### 1. ADK 提示
**位置**
- `app/prompts/insurance_agent_prompt.txt`

**責任**
- 控制對話流程
- 決定何時詢問後續問題
- 決定何時呼叫工具
- 根據使用者意圖選擇正確的工具
- 決定何時透過規則或產品詳情豐富答案
- 執行高層級護欄

**應包含**
- 必要資訊檢查
- 工具選擇邏輯
- 推薦工作流程規則
- 安全約束
- 非虛構規則

**不應包含**
- SQL 陳述式
- 硬編碼的產品事實
- 繁重的回應格式化範本
- 資料庫特定邏輯

**變更影響**
- 影響代理行為和工具選擇

---

### 2. Toolbox 工具
**位置**
- `db/tools.yaml`

**責任**
- 執行受控資料檢索
- 返回產品候選項
- 返回產品詳情
- 返回推薦規則

**目前的工具**
- `search_medical_products`
- `search_accident_products`
- `search_family_protection_products`
- `search_income_protection_products`
- `get_product_detail`
- `get_recommendation_rules`

**應包含**
- 結構化的基於 SQL 的檢索邏輯
- 受控的輸入參數
- 穩定的輸出欄位

**不應包含**
- 對話策略
- 完整的推薦措辭
- 合規免責聲明
- 自由格式的推理文本

**變更影響**
- 影響檢索品質和推薦證據

---

### 3. Toolbox 工具集
**位置**
- `db/tools.yaml`

**責任**
- 為不同的使用案例分組工具

**目前的工具集**
- `insurance_recommendation_tools`
- `insurance_debug_tools`

**應包含**
- 按操作目的進行清晰分組
- 推薦工具與調試工具分離

**不應包含**
- 無意圖的重複或混合目的分組

**變更影響**
- 影響哪些工具對代理或環境可見

---

### 4. Toolbox 提示
**位置**
- `db/tools.yaml`

**責任**
- 提供可重用的提示範本
- 標準化後續問題措辭
- 標準化推薦輸出結構
- 標準化免責聲明措辭

**目前的提示**
- `insurance_followup_question_template`
- `insurance_recommendation_response_template`
- `insurance_disclaimer_template`

**應包含**
- 後續問題範本
- 推薦回應範本
- 合規免責聲明範本

**不應包含**
- SQL 邏輯
- 工具選擇規則
- 資料庫映射邏輯

**變更影響**
- 影響一致性、措辭和合規表達

---

### 5. 資料庫結構描述和種子資料
**位置**
- `db/schema.sql`
- `db/seed.sql`

**責任**
- 儲存產品資料
- 儲存推薦規則
- 儲存常見問題和示例資料

**應包含**
- 保險產品
- 推薦規則
- 常見問題知識
- 示例使用者設定檔

**不應包含**
- 代理編排邏輯
- 提示範本
- 執行時對話規則

**變更影響**
- 影響工具可以檢索的內容

---

## 所有權模型

| 角色 | 擁有 | 典型變更 |
|---|---|---|
| 代理工程師 | ADK 提示、代理流程 | 後續邏輯、工具選擇邏輯、編排更新 |
| 資料/平台工程師 | Toolbox 工具、工具集、來源配置 | SQL 工具、配置結構、工具分組 |
| 領域所有者 / 產品經理 / 合規 | Toolbox 提示 | 措辭、免責聲明、推薦回應結構 |
| 資料庫所有者 | 結構描述、種子資料、產品記錄 | 產品資料、規則、常見問題、示例記錄 |

---

## 變更控制規則

### ADK 提示變更
使用時機：
- 對話流程需要調整
- 工具選擇規則需要改進
- 安全或編排行為需要更新

### Toolbox 工具變更
使用時機：
- 檢索邏輯有誤
- 產品篩選需要改進
- 新增推薦場景

### Toolbox 提示變更
使用時機：
- 後續問題措辭需要修訂
- 輸出格式必須更加一致
- 合規措辭必須更新

### 資料庫變更
使用時機：
- 產品目錄變更
- 規則內容變更
- 常見問題或示例資料變更

---

## CI 驗證檢查清單

## 階段 1：Toolbox 配置驗證
目標：確認 `tools.yaml` 可載入且完整。

### 通過條件
- `Initialized 1 sources: insurance_sqlite`
- `Initialized 6 tools: ...`
- `Initialized 3 toolsets: ...`
- `Initialized 3 prompts: ...`
- `Server ready to serve!`

### 失敗條件
- YAML 結構描述錯誤
- 工具計數不匹配
- 提示計數不匹配
- 來源初始化失敗

---

## 階段 2：工具契約驗證
目標：確認每個工具返回預期的資料邊界。

### `search_medical_products`
輸入：
- `age=30`
- `budget=15000`

預期：
- 返回 `安心住院醫療方案 A`
- 不返回非醫療產品

### `search_family_protection_products`
輸入：
- `age=42`
- `budget=30000`

預期：
- 返回 `家庭定期壽險方案 C`

### `search_income_protection_products`
輸入：
- `age=38`
- `budget=25000`

預期：
- 返回合理的收入保護候選項
- 在可用時優先考慮 `critical_illness`，其次是 `life` 產品

### `get_product_detail`
輸入：
- `product_id=3`

預期：
- 包括等待期
- 包括除外責任
- 包括保費範圍
- 包括年齡範圍

### `get_recommendation_rules`
輸入：
- `main_goal=family_protection`

預期：
- 返回家庭責任相關規則

---

## 階段 3：提示契約驗證
目標：確認可重用範本仍滿足業務和合規要求。

### `insurance_followup_question_template`
必須仍詢問：
- 年齡
- 預算
- 主要保護目標

不得：
- 直接推薦產品
- 編造產品資訊

### `insurance_recommendation_response_template`
必須仍要求：
- 產品名稱
- 推薦原因
- 條件提醒
- 等待期 / 除外責任摘要
- 無虛構內容
- 無承保、理賠或回報保證

### `insurance_disclaimer_template`
必須仍包含完整的免責聲明含義，不得省略。

---

## 階段 4：代理整合驗證
目標：確認 ADK + ToolboxToolset + `tools.yaml` 正確配合。

### 案例 A：醫療保護
輸入：
`我 30 歲，年度保險預算 15000，想加強醫療保障，有什麼推薦？`

預期：
- 追蹤包括 `search_medical_products`
- 可能包括 `get_product_detail`
- 推薦 `安心住院醫療方案 A`
- 包括免責聲明

### 案例 B：資訊不完整
輸入：
`我想買保險，幫我推薦。`

預期：
- 無產品搜尋工具呼叫
- 詢問年齡、預算和主要目標

### 案例 C：家庭保護
輸入：
`我 42 歲，已婚有小孩，年度預算 30000，想補家庭保障。`

預期：
- 追蹤包括 `search_family_protection_products`
- 追蹤包括 `get_recommendation_rules`
- 推薦 `家庭定期壽險方案 C`
- 包括免責聲明

### 案例 D：低預算意外保險
輸入：
`我 27 歲，年度預算 8000，想先補意外保障。`

預期：
- 追蹤包括 `search_accident_products`
- 優先選擇較低進入的產品
- 包括除外責任提醒

### 案例 E：收入保護
輸入：
`我 38 歲，已婚有小孩，年度預算 25000，想加強收入中斷風險保障。`

預期：
- 追蹤包括 `search_income_protection_products`
- 可能包括 `get_recommendation_rules`
- 不虛構不可用的產品

### 案例 F：沒有精確匹配
輸入：
`我 68 歲，年度預算 10000，想加強醫療保障。`

預期：
- 清楚說明可能沒有精確匹配
- 不虛構產品
- 可能保守地提供最接近的候選項

---

## 階段 5：發布閘門
如果發生以下任何情況，必須阻止發布：
- Toolbox 配置無法初始化
- 缺少必要工具
- 缺少必要提示
- 免責聲明要求被破壞
- 高優先級整合案例失敗
- 代理虛構產品或規則內容

---

## 操作原則

1. **ADK 提示控制流程**
   - 決定何時詢問
   - 決定何時搜尋
   - 決定呼叫哪個工具

2. **Toolbox 工具控制資料存取**
   - 檢索結構化的產品和規則資訊
   - 不擁有對話行為

3. **Toolbox 提示控制措辭契約**
   - 標準化後續提示
   - 標準化推薦輸出
   - 標準化合規免責聲明

4. **CI 確保這些層不會偏離**
   - 配置驗證
   - 工具驗證
   - 提示驗證
   - 整合驗證

---

## 建議的審查工作流程

1. 僅更新相關層
   - ADK 提示用於編排
   - Toolbox 工具用於檢索
   - Toolbox 提示用於措辭
   - 資料庫用於資料

2. 執行本地驗證
   - Toolbox 啟動檢查
   - 工具煙霧測試
   - 提示契約檢查
   - 代理場景測試

3. 以變更類別開啟拉取請求
   - `agent-flow`
   - `tool-config`
   - `prompt-template`
   - `data-update`

4. 要求適當所有者批准

---

## 治理基本原則

**ADK 提示管理流程，Toolbox 工具管理資料，Toolbox 提示管理措辭契約，CI 驗證所有三者保持對齊。**