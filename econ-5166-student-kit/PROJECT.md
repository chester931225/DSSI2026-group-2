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

- 本組已確認的主要研究方向：檢驗臺北市夜間道路無照明是否與事故嚴重程度相關。主要分析比較夜間有照明與無照明事故，並以二元羅吉斯迴歸控制可觀察的道路及環境特徵；若關聯方向一致且相對穩健，再以嚴重事故件數、嚴重事故占比及事故總數建立優先現勘名單，作為向市府或相關單位提出分階段建議的依據。研究定位為關聯分析，不推論照明改善的因果效果。

## Team

**每組預設 3–4 位學生（教師預設）**，以學生已確認的實際名單為準。AI 在學生開始使用時，主動確認全組成員姓名、各自已確認的實際工作，以及目前對話的學生是哪位。先沿用對話或本文件中已確認的資訊，只補問缺少的部分，不只是留下待填。尚未分配的工作由組員決定，未確認的欄位保留「待確認」。已確認的人數不同時依實際名單記錄，不為符合預設補造或刪除成員。

AI 只整理學生提供或明確確認的姓名與工作，不自行指派 PM／DE／DA，也不從 Git 作者、電腦帳號、檔名、範本示例或檔案提供者推定作者或責任；保留有依據的既有作者，不自動改成本次提供檔案的學生。等待回答時可先進行不依賴歸屬的檢查或討論。保留下列既有欄位，按已確認名單一人一列；尚無名單時保持空表，不先填入 3 或 4 位假成員。`Role` 記錄學生提供的角色與實際工作，確認姓名與工作不需額外要求學號或 GitHub 帳號。

目前對話的學生：詹明翰（2026-10-16 本次對話確認；本次工作為資料整理與敘述性統計製作。角色自述為「除了 PM 跟 DA 的那個」，與下方既有 DA 紀錄不一致，正式角色代稱待釐清，未逕行修改既有分工）。

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
| 詹明翰 | Codex | GPT-6 家族（完整型號未確認） | `AGENTS.md` | 2026-10-16：本次對話確認姓名；工具與模型家族依目前執行環境 |

## Data and Current Focus

| Field | Details |
| --- | --- |
| Data sources / documentation | [臺北市資料大平臺－臺北市死傷交通事故資料](https://data.taipei/dataset/detail?id=2f238b4f-1b27-4085-93e9-d684ef0e2735)，提供機關為臺北市政府警察局交通大隊；目前檔案為民國 114 年（2025 年）。代碼定義見 [事故對照表](data/raw/事故對照表.pdf)，完整檢查見 [原始資料說明](data/raw/taipei_2025_casualty_crashes_documentation.ipynb)。 |
| Unit of observation | 檔案每列皆為 `當事人序號 = 1`；2026-10-16 核對 22,762 列，完整列及「年月日時分＋肇事地點＋座標」候選鍵均無重複。敘述性統計暫以每列一事故；因無官方事故識別碼，觀察單位與路口彙整仍未獲官方確認。 |
| Current task / target variables | 研究方向仍為夜間無照明與事故嚴重程度的關聯，後續羅吉斯迴歸及現勘名單尚未執行。2026-10-16 已完成 [敘述性統計](finding/敘述性統計.ipynb)：樣本概況、光線分布、夜間三種設備狀態比較（開啟／未開啟或故障／無設備）。依每筆座標以 Astral 3.2 計算當日日出日落，夜間 6,795 筆、缺座標無法判定 2 筆；另列使用者確認的全年保守固定18:49–05:02敏感度；界線依2025年365日及資料座標範圍四角計算，所有有座標的入選事故已逐筆核對屬於當日夜間。死亡指標沿用本次使用者「死亡人數 ≥ 1」，即 24 小時內死亡；2–30 日死亡人數另列。重傷資料與後續結果變數仍待確認。  照明設備狀態×日出日落夜間3×2交叉分析（finding第3節）；完整樣本22,750件，目標條件460件，占完整樣本2.02%、占照明已知夜間事故6.77%，缺值排除12件。  finding/敘述性統計.ipynb依資料定義、完整變數分布、照明與日夜交叉、夜間傷亡比較、時段敏感度、結論與驗證排列，作為簡報共同參考；重複的樣本概況及光線表與對應兩份CSV已刪除。 |
| Assignment constraints | 目前沒有車流量資料，因此不稱事故率；不據此推論照明改善的因果效果。事故觀察單位、去重／事故鍵、重傷所需的其他資料來源或辨識方式，以及路口彙整方法仍須確認；日出日落主要指標與新版保守固定時段已完成計算及驗證；界線適用本年度與本資料地理範圍。 |

## Data Artifacts

資料建立或核對後，由 AI 依 [資料銜接規則](FINDING-RULES.md#資料銜接與檔案驗證) 填入實際紀錄，一個資料檔一列。尚無資料時保持空表，不把範例當成已完成結果。

| Dataset | Role | Data file | Documentation | Processing notebook | Verification | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| 臺北市 114 年死傷交通事故明細 | raw | [CSV](data/raw/114年-臺北市死傷交通事故明細.csv) | [Jupyter Notebook](data/raw/taipei_2025_casualty_crashes_documentation.ipynb)；[事故對照表](data/raw/事故對照表.pdf) | not applicable (source) | 2026-09-29：已核對 UTF-8 with BOM、22,762 列、47 欄、民國 114 年 1–12 月、0 筆完整列重複、欄位缺失、候選事故鍵及主要代碼分布；另已核對 4 頁事故對照表（SHA-256：`f40ded1ded1c816a38f421bc972cdc1320bbd280e647792207ec037d05fd3670`）。夜間規則後續已確認為臺北市當日日落後至隔日日出前，固定 18:00–06:00 作敏感度分析，但尚未實際計算與驗證；觀察單位、事故唯一鍵、重傷所需的其他資料來源或辨識方式、路口彙整仍 pending。 | `61f0bdb52a49176746ab8b66926224b294498c9e26b2dec6eefe44906fdffa0c` |
| 臺北市 114 年事故敘述性統計輸入 | analysis | [CSV](data/processed/taipei_2025_descriptive.csv) | [資料說明 Notebook](data/processed/taipei_2025_descriptive_documentation.ipynb)；[完整整合版](finding/敘述性統計.ipynb#data-description) | [處理 Notebook](data/code/prepare_descriptive_statistics.ipynb) | 2026-10-16：原始47欄及22,762列完整保留，衍生資料58欄。主要夜間6,795筆、未知2筆。本次依使用者確認改定義 night_fixed：2025全年最早日出／最晚日落、資料座標範圍四角，保守取整為18:49（含）–05:02（不含），固定時段5,027筆；有座標的入選紀錄均逐筆驗證為當日夜間。處理、資料說明、分析三份Notebook已從乾淨kernel重跑；表格CSV同步更新。僅night_fixed欄數值改變；舊版SHA-256為`9c90b54cf073cbe1fb8b5ade587f37d7f1e316ee988a05236b454413cb8b5d97`。原始CSV雜湊不變。官方事故識別碼、重傷與速限0定義仍待確認。 | `09c8bae171a8307414aa787ce36f9d5d1f2f1c455dd619e250ac3fae41f15a60` |

路徑與連結相對於本專案根目錄。Role 記錄 raw／analysis／train／test 或已確認用途；Verification 說明實際執行的檢查、日期與限制，未完成時明列 pending／failed。SHA-256 由實際檔案計算。外部整理檔沒有產生程式可記 not available；原始來源可記 not applicable (source)。

2026-10-16 補充：raw CSV 與 PDF 雜湊均再次核對一致；原索引所列 `data/raw/taipei_2025_casualty_crashes_documentation.ipynb` 目前工作區不存在，保留歷史紀錄並標示文件缺失，不宣稱已檢閱該 Notebook。本次處理與分析的定義、檢查和結果記於新增三份 Notebook。上列 raw 舊紀錄中的「尚未計算夜間」為先前狀態，本次已在衍生資料中完成。

## Key Contributions

**課程原則：所有 contribution 都必須由學生在 VS Code 自行 commit 並 push。** 各成員隨成果更新下表，每項貢獻一列，記錄誰、做了什麼，以及實際包含該成果的 commit 連結或 SHA。AI 可整理待提交紀錄，在學生操作後唯讀核對再回填。程式、資料處理、文件、提案及專案紀錄的修改都適用；外部成果須有已 commit 的說明或連結紀錄可追溯。

尚未 commit 的工作標示「待提交」，已有 reference 但尚未核對者標示「待核對」；兩者均不視為完成貢獻紀錄。檔案連結不能取代 commit reference。不要以 commit 次數或程式行數替代成果評估。

已核對的本地 commit 不等於已 push；在 reference 後註明「推送待核對」或經證實的「待 push」，遠端目標分支包含該 commit 的證據核對完成後才記「已推送並核對」。學生自行回報但未核對時註明來源。貢獻表回填後，由學生在下一次 commit／push 納入；reference 指向先前的成果 commit，不要求填該表更新自身的未來 hash。

姓名與貢獻歸屬須由學生提供或確認；資訊缺少時先詢問，未回答前保留待填，不以 commit 作者直接認定實際負責人。commit 用來核對成果紀錄，不取代學生確認的分工。

| Name | Contribution | Commit reference |
| --- | --- | --- |
| 謝子詮 | 提供 [臺北市 114 年死傷交通事故原始資料](data/raw/114年-臺北市死傷交通事故明細.csv)與[事故對照表](data/raw/事故對照表.pdf)，並建立及核對 [原始資料說明 Notebook](data/raw/taipei_2025_casualty_crashes_documentation.ipynb)。 | 待提交（貢獻紀錄未完成） |
| 詹明翰 | 在 Codex 協助下製作並執行 [樣本、光線及夜間照明敘述性統計](finding/敘述性統計.ipynb)、[資料整理程式](data/code/prepare_descriptive_statistics.ipynb)及[衍生資料說明](data/processed/taipei_2025_descriptive_documentation.ipynb)，核對 PDF 代碼與日出日落定義，保存六份表格 CSV，更新本次資料索引。後續補充四份工作 Notebook 的步驟說明與結果解讀，將資料說明的七個類別摘要分表呈現並重新執行驗證。 補充Astral方法定義，依確認改採全年最早日出／最晚日落固定時段並同步重跑三份Notebook及表格。 新增3×2照明與日夜交叉分析、不同分母比例及三份表格CSV，已重跑正式分析並核對原始代碼與缺值排除。 整合全部資料說明與七張類別摘要至正式finding，加入目錄、分章表格、簡報重點與CSV索引，已從乾淨kernel執行且既有九份表格及資料版本不變。 將文件重編為連續八節，移除重複表1/2與CSV及製作階段敘述，將交叉分析、夜間比較、敏感度及解讀融入各節，重跑後資料與保留八份CSV數值不變。 | 待提交（貢獻紀錄未完成） |
