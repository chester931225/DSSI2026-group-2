# Project Context

這份文件保存本組專案脈絡、教師設定的預設值與學生已確認的偏好。除明列的預設值外，未填項目不代表已確認；AI 應詢問當前任務需要的資訊。

## Repository Context

學生先自行建立小組 repo，再於 VS Code clone 並開啟，把完整工作包內容放在 repo 根目錄。正式學生產出前核對設定；AI 可唯讀檢查與提供說明，stage、commit、push、pull／sync 由學生親自操作。此空白範本不代表學生已經建好 repo；教師維護範本時不代填學生的 URL 或狀態。

| Field | Details |
| --- | --- |
| Remote repository | 待學生提供或唯讀核對，不記錄帳密或 token |
| Target branch | 待學生確認或唯讀核對 |
| Setup status | 待確認學生的 repo、remote 與開啟的專案根目錄 |
| Last push verification | 待核對；記錄核對對象、分支、commit、依據及時間 |

## Research Question

- 本組已確認的研究方向：以夜間、無路燈情況下的死亡或重傷事故件數，篩選優先檢視地點；以嚴重事故占比作為輔助指標，並同時附上事故總數。由於沒有車流量資料，不將上述指標稱為事故率，也不據此推論照明改善的因果效果。

## Team

**每組預設 3–4 位學生（教師預設）**，以學生已確認的實際名單為準。AI 在學生開始使用時，主動確認全組成員姓名、各自已確認的實際工作，以及目前對話的學生是哪位。先沿用對話或本文件中已確認的資訊，只補問缺少的部分，不只是留下待填。尚未分配的工作由組員決定，未確認的欄位保留「待確認」。已確認的人數不同時依實際名單記錄，不為符合預設補造或刪除成員。

AI 只整理學生提供或明確確認的姓名與工作，不自行指派 PM／DE／DA，也不從 Git 作者、電腦帳號、檔名、範本示例或檔案提供者推定作者或責任；保留有依據的既有作者，不自動改成本次提供檔案的學生。等待回答時可先進行不依賴歸屬的檢查或討論。保留下列既有欄位，按已確認名單一人一列；尚無名單時保持空表，不先填入 3 或 4 位假成員。`Role` 記錄學生提供的角色與實際工作，確認姓名與工作不需額外要求學號或 GitHub 帳號。

目前對話的學生：謝子詮（依本次對話更新，不自動沿用上一次的對話者）。

| Name   | Student ID | GitHub Account | Role |
|--------|------------|----------------|------|
| 謝子詮 | B12303045  | chester931225  | DE  |
| 曾翊涵 | B12607049  | TBD|PJM
| 詹明翰 | B12302350  |hank94224-commits|DA

## Student Preferences

- Tool / artifact format: Python／Jupyter Notebook（謝子詮於 2026-09-29 本次對話確認）
- Report language: 繁體中文（台灣用語，zh-TW；教師預設，學生明確指定其他語言時優先沿用）
- Other explicit preferences: 尚未提供

## AI Agent Context

依 `AGENTS.md` 的 `Model and Agent Selection`，記錄每位已確認學生目前使用的 AI 工具、模型與選用入口。同組成員可以使用不同模型；不要將前一位學生或教師的設定當作全組預設。姓名確認後按學生一人一列，換工具或模型時更新該列；尚無學生資訊時保持空表。

`Model` 保留學生提供或目前執行環境可靠顯示的名稱；只知道工具或模型家族時註明「完整型號未確認」，不自行猜版本。`Source` 記錄「學生本次提供」或「目前執行環境」等實際依據。先確認選用入口即可，不為填滿模型版本而打斷工作。

| Student | AI tool / client | Model | Agent entrypoint | Source |
| --- | --- | --- | --- | --- |
| 謝子詮 | Codex | GPT-5 | `AGENTS.md` | 目前執行環境 |

## Data and Current Focus

| Field | Details |
| --- | --- |
| Data sources / documentation | [臺北市資料大平臺－臺北市死傷交通事故資料](https://data.taipei/dataset/detail?id=2f238b4f-1b27-4085-93e9-d684ef0e2735)，提供機關為臺北市政府警察局交通大隊；目前檔案為民國 114 年（2025 年）。代碼定義見 [事故對照表](data/raw/事故對照表.pdf)，完整檢查見 [原始資料說明](data/raw/taipei_2025_casualty_crashes_documentation.ipynb)。 |
| Unit of observation | 待確認。檔案每列皆為 `當事人序號 = 1`，同時包含事故層級死傷人數與第一當事者欄位；沒有事故唯一識別碼，尚不能確認每列是否等於一件事故，或可靠彙整到路口層級。 |
| Current task / target variables | 以夜間、無路燈情況下的死亡或重傷事故件數篩選優先檢視地點；嚴重事故占比作為輔助，並附上事故總數。死亡人數與道路照明設備欄位可用，但夜間規則仍待確認，且現有受傷程度代碼沒有重傷分類。 |
| Assignment constraints | 目前沒有車流量資料，因此不稱事故率；不據此推論照明改善的因果效果。事故觀察單位、去重／事故鍵、夜間定義、重傷所需的其他資料來源或辨識方式，以及路口彙整方法仍須確認。 |

## Data Artifacts

資料建立或核對後，由 AI 依 [資料銜接規則](FINDING-RULES.md#資料銜接與檔案驗證) 填入實際紀錄，一個資料檔一列。尚無資料時保持空表，不把範例當成已完成結果。

| Dataset | Role | Data file | Documentation | Processing notebook | Verification | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| 臺北市 114 年死傷交通事故明細 | raw | [CSV](data/raw/114年-臺北市死傷交通事故明細.csv) | [Jupyter Notebook](data/raw/taipei_2025_casualty_crashes_documentation.ipynb)；[事故對照表](data/raw/事故對照表.pdf) | not applicable (source) | 2026-09-29：已核對 UTF-8 with BOM、22,762 列、47 欄、民國 114 年 1–12 月、0 筆完整列重複、欄位缺失、候選事故鍵及主要代碼分布；另已核對 4 頁事故對照表（SHA-256：`f40ded1ded1c816a38f421bc972cdc1320bbd280e647792207ec037d05fd3670`）。觀察單位、事故唯一鍵、夜間定義、重傷所需的其他資料來源或辨識方式、路口彙整仍 pending。 | `61f0bdb52a49176746ab8b66926224b294498c9e26b2dec6eefe44906fdffa0c` |

路徑與連結相對於本專案根目錄。Role 記錄 raw／analysis／train／test 或已確認用途；Verification 說明實際執行的檢查、日期與限制，未完成時明列 pending／failed。SHA-256 由實際檔案計算。外部整理檔沒有產生程式可記 not available；原始來源可記 not applicable (source)。

## Key Contributions

**課程原則：所有 contribution 都必須由學生在 VS Code 自行 commit 並 push。** 各成員隨成果更新下表，每項貢獻一列，記錄誰、做了什麼，以及實際包含該成果的 commit 連結或 SHA。AI 可整理待提交紀錄，在學生操作後唯讀核對再回填。程式、資料處理、文件、提案及專案紀錄的修改都適用；外部成果須有已 commit 的說明或連結紀錄可追溯。

尚未 commit 的工作標示「待提交」，已有 reference 但尚未核對者標示「待核對」；兩者均不視為完成貢獻紀錄。檔案連結不能取代 commit reference。不要以 commit 次數或程式行數替代成果評估。

已核對的本地 commit 不等於已 push；在 reference 後註明「推送待核對」或經證實的「待 push」，遠端目標分支包含該 commit 的證據核對完成後才記「已推送並核對」。學生自行回報但未核對時註明來源。貢獻表回填後，由學生在下一次 commit／push 納入；reference 指向先前的成果 commit，不要求填該表更新自身的未來 hash。

姓名與貢獻歸屬須由學生提供或確認；資訊缺少時先詢問，未回答前保留待填，不以 commit 作者直接認定實際負責人。commit 用來核對成果紀錄，不取代學生確認的分工。

| Name | Contribution | Commit reference |
| --- | --- | --- |
| 謝子詮 | 提供 [臺北市 114 年死傷交通事故原始資料](data/raw/114年-臺北市死傷交通事故明細.csv)與[事故對照表](data/raw/事故對照表.pdf)，並建立及核對 [原始資料說明 Notebook](data/raw/taipei_2025_casualty_crashes_documentation.ipynb)。 | 待提交（貢獻紀錄未完成） |
