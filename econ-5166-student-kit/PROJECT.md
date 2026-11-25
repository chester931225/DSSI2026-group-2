# Project Context

這份文件保存本組專案脈絡、教師設定的預設值與學生已確認的偏好。除明列的預設值外，未填項目不代表已確認；AI 應詢問當前任務需要的資訊。

## Repository Context

學生先自行建立小組 repo，再於 VS Code clone 並開啟，把完整工作包內容放在 repo 根目錄。正式學生產出前核對設定；AI 可唯讀檢查與提供說明，stage、commit、push、pull／sync 由學生親自操作。此空白範本不代表學生已經建好 repo；教師維護範本時不代填學生的 URL 或狀態。

| Field | Details |
| --- | --- |
| Remote repository | `origin`：https://github.com/chester931225/DSSI2026-group-2.git （2026-11-25 本機設定唯讀核對；不等於已核對遠端提交狀態）。 |
| Target branch | 本機目前為 `main`，追蹤 `origin/main`；本次不變更分支或同步。 |
| Setup status | Git 根目錄為 `DSSI2026-group-2/`；研究工作包根目錄為其下 `econ-5166-student-kit/`，含 `AGENTS.md` 與 `templates/`。依學生 Unit 0.3 指示維持現有結構；下列研究路徑均相對於工作包根目錄。 |
| Last push verification | 遠端推送狀態待核對；本機與快取的遠端追蹤紀錄不能證明即時推送狀態。本次僅核對本機 Git 設定，不執行 fetch、pull／sync 或其他 Git 寫入。 |

## Research Question

2026-11-25 研究方向移轉：依學生已審查通過的 Unit 0.1、0.2 及本次 Unit 0.3 指示記錄。前兩階段完成的是既有專案盤點、研究定義及記憶體中的唯讀可行性診斷，並非新研究的正式資料處理、GIS 整合或分析結果。

- 暫定中文題目：**都市空間異質性與交通事故型態之關聯：以臺北市行政里的分群分析為例**。
- 英文題目：**Urban Spatial Heterogeneity and Traffic Accident Patterns: A Clustering-Based Analysis of Taipei City**。
- **主要設計 D 原版**：建立各里的事故組成特徵，以分群辨識地區事故型態，再比較人口結構、都市計畫分區及其他可取得的都市環境，討論社會意義及政策意涵。
- **有條件延伸 D 改良版**：獨立建立 Accident Clustering 與 Urban Environment Clustering，再比較關聯；僅在 Dataset B 品質及特徵適切性通過評估，且群組具足夠穩定性及可解釋性後，才考慮典型／非典型社區。不預設兩套分群必有顯著關聯。

| Question | 研究問題與狀態 |
| --- | --- |
| RQ1 | 臺北市各行政里的交通事故組成具有哪些空間異質性？ |
| RQ2 | 能否透過非監督式學習辨識穩定且具有可解釋性的地區事故型態？ |
| RQ3 | 不同事故型態的地區在人口結構及都市環境特徵上有何差異？ |
| RQ4 | 事故型態是否具有跨年度穩定性？ |
| RQ5（有條件延伸） | 獨立建立的都市環境分群與事故分群是否具有系統性關聯？ |
| RQ6（選用） | 不同類型的都市環境特徵是否具有辨識事故型態的預測能力？ |

### Confirmed Research Settings

| Setting | 已確立的研究設定 |
| --- | --- |
| Period and unit | 2024–2025 年、全天、不限定夜間；空間單位為臺北市行政里，基礎資料結構為 village-year。 |
| Accident record selection | 2024 選取當事人序號 1；2025 保留現有第一當事人紀錄。此方案有檔內一致性證據，仍缺官方事故 ID；完整保留所有原始當事人紀錄。 |
| Candidate sample | 2024 候選事故紀錄 22,368 筆、2025 為 22,762 筆，合計 45,130 筆；尚未完成 GIS 歸里，**不是最終分析樣本數**。 |
| Population | 使用行政里層級「計」，不重複加總男、女；年度人口為 12 個月平均存量，年齡比例為各月該年齡組人口合計除以各月總人口合計。 |
| Interpretation | 設籍人口不是交通暴露人口；不假設當事人居住於事故發生地；都市計畫分區不等於實際土地使用。 |
| Scope exclusions | 排除付費電信信令人流；暫不執行 Causal Inference，Prediction 為選用延伸。 |
| Historical work | 舊夜間事故研究、資料與成果完整保留，不作為新行政里研究的正式結論；歷史設定見下方 Historical Research Context。 |

### Candidate Methods and Pending Decisions

- 以事故組成為主要分群依據，事故總數及負擔原則上分群後比較，亦可作替代特徵設定。
- K-means 為主要候選；Hierarchical Clustering（Ward）為替代及穩健性方法。PCA 視特徵相關性及研究需求決定，不強制使用。
- 候選主分析：合併兩年各項事故分子與有效分母後重算比例，不直接平均兩年比例；保留 village-year 基礎資料以支援分年比較。兩年合併規格的觀察單位是里，不將同里兩年當作獨立社區。
- 候選跨年驗證：所有前處理參數及分群中心僅以 2024 擬合，再指派 2025 群組；Ward 的跨年比較方式須另行規劃，不能假定與 K-means 相同。
- 群數、低樣本門檻、比例平滑、尺度與特徵權重、最終特徵及模型均待 EDA 後審查。零事故里不把所有組成比例設為 0；低樣本里不自行刪除。
- 若群組不穩定或難以解釋，據實呈現，不強行建立分群結論。RQ6 的預測目標、時點及防洩漏設計尚未決定。

### Feature Planning — Not Yet Constructed

Dataset A、B、C 均為規劃，尚未建立正式資料檔、完成空間配對或確認分析可用。下列為目前主要候選定義；正式資料處理時仍須核對官方代碼表，最終分群特徵須經 EDA 審查。

**Dataset A — Accident Composition Features**

| Variable | 候選操作定義 |
| --- | --- |
| `morning_peak_ratio` | 07:00 至未滿 09:00 的事故比例。 |
| `evening_peak_ratio` | 17:00 至未滿 19:00 的事故比例。 |
| `late_night_ratio` | 22:00 至次日未滿 06:00 的事故比例；與 Unit 0.2 尚未定案的其他夜間定義區分。 |
| `weekend_ratio` | 星期六及星期日事故比例，不等同所有國定假日。 |
| `intersection_ratio` | 事故位置代碼 1–4，表示路口及附近，含待轉／停等區。 |
| `rear_end_ratio` | 事故類型及型態代碼 13（追撞）。 |
| `side_collision_ratio` | 事故類型及型態代碼 16（側撞），不混同擦撞。 |
| `pedestrian_collision_ratio` | 事故類型及型態代碼 1–9（人與車）；不宣稱已辨識所有涉入行人的事故。 |
| `multi_injury_ratio` | 受傷人數至少 2 人的事故比例，不代表重傷程度。 |

每項比例以該變數可判定事故數為分母，保留分子、有效分母、缺失數與有效涵蓋率；缺失不是不符合，分母為零保留 NA。各比例可重疊，並非相加等於 100% 的單一分類。早晚尖峰只是操作定義，不是實測尖峰車流。

平日限定時段、天文夜間、嚴格路口內定義及移除多人受傷變數均為敏感度候選。第一當事人年齡、性別、車種及事故道路情境先列補充變數，不代表全部涉入者，也不直接全部納入主分群。舊研究排除照明及傷亡的規則保留其舊案適用範圍；是否另有教師共同要求仍須依明確規範核對，不把歷史設定自動套用於新案。

**Dataset B — Urban Environment Features**

| Block | 候選變數與限制 |
| --- | --- |
| B1 人口結構 | `population_density`、`elderly_population_ratio`、`child_population_ratio`；人口年度口徑依上表，年齡界線、正式 crosswalk 及里面積驗證仍待完成。 |
| B2 都市計畫分區 | `residential_zoning_ratio`、`commercial_zoning_ratio`、`industrial_zoning_ratio`、`educational_zoning_ratio`、`park_green_zoning_ratio`；須先驗證來源、CRS、幾何及正式分類表，再以避免重複計算的面積口徑建立比例。 |
| B3 其他環境（尚未取得或選用） | 道路密度、主要幹道比例、路口密度、人行道密度、號誌設施、捷運活動程度；不將候選項目記為已取得資料。 |

Dataset B 不含事故數、事故組成、傷亡結果，亦不以事故紀錄中的道路特徵取代全里道路環境。單一時間快照依實際版本描述，不宣稱已有兩年度獨立環境資料；分區未覆蓋、未分類或缺失不當作 0。

**Dataset C — External Profiling Variables**

`annual_accident_count`、`total_injuries`、`total_fatalities_24h`、`total_fatalities_2_30d`、`fatal_accident_ratio`、`injuries_per_crash`、`accidents_per_km2`、`low_count_flag`，用於事故負擔及群組比較。傷亡缺值不能以 0 補成完整總數；24 小時與 2–30 日死亡先分列。每平方公里事故數是事故空間密度，不是暴露校正後事故率。

同一變數在替代模型變更角色時須記錄；參與分群的變數差異不能當成獨立驗證。A 已含多人受傷比例時，C 的受傷負擔比較也不是完全獨立的驗證。

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
| Data sources / documentation | [事故官方來源](https://data.taipei/dataset/detail?id=2f238b4f-1b27-4085-93e9-d684ef0e2735)：[2024 CSV](data/raw/113年-臺北市死傷交通事故明細.csv)、[2025 CSV](data/raw/114年-臺北市死傷交通事故明細.csv)、[事故對照表](data/raw/事故對照表.pdf)；[人口 CSV](data/raw/112迄今各里人口數按年齡分.csv)及[官方說明](https://data.taipei/dataset/detail?id=a6394e3f-3514-4542-87bd-de4310a40db3)；[里界 SHP](data/raw/G97_A_CAVLGE_P.shp)及[官方來源（學生提供）](https://data.taipei/dataset/detail?id=6b17b31d-4e16-495e-95b1-9fd1f47c80d8)；[細計-面](data/raw/細計-面.shp)、[細計-文](data/raw/細計-文.shp)及[官方來源（學生提供）](https://data.taipei/dataset/detail?id=3bab0a01-7936-4218-8cb5-f74dfcb43dda)。四個官方來源網址均由學生於 Unit 0.4 提供／確認；本機檔案版本、下載日期及歷史適用性仍未認證，GIS 配套及版本問題見下表。Unit 0.5 已建立並執行[兩年事故及 PDF 說明](data/raw/taipei_2024_2025_crashes_raw_documentation.ipynb)、[人口說明](data/raw/taipei_population_age_raw_documentation.ipynb)、[里界說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb)及[都市計畫說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)；15 個來源實體檔（含 GIS 配套）逐檔列於 Data Artifacts。2026-11-25 已查閱四官方頁的機關、欄名及更新日期；網頁更新日與本機下載／版本證明分開記錄。 |
| Unit of observation | 基礎資料為行政里×年；由 2024 第一當事人 22,368 筆及 2025 現有第一當事人 22,762 筆候選事故建立。Unit 0.2 的檔內唯一性與一致性診斷支持此操作口徑，但無官方事故 ID；尚未完成 GIS 空間配對，不宣稱已有 45,130 筆可用分析樣本。 |
| Current task / target variables | Unit 0.1–0.4 已完成並經學生審查（依本次 Unit 0.5 指示）。Unit 0.5 已完成四份正式原始資料說明 Notebook，使用新 .venv 在四個乾淨 kernel 執行共 31 個 code cells、保存實際輸出及讀檔前後 SHA-256；目前待學生審查。D 原版仍為主案，A／B／C 及正式 crosswalk 尚未建立；下一階段為 Chapter 1 Data Validation，須另獲指示才開始。 |
| Assignment constraints | 按 Sequential Prompt Protocol 一次處理已授權單元；Unit 0.5 僅新增 raw 說明 Notebook、唯讀診斷與必要 PROJECT.md／資料索引更新，全部程式使用 Unit 0.4 .venv。不安裝套件、不重新下載或修改原始資料、不覆寫或重跑舊研究、不建立 processed／正式 crosswalk、不指定未知 CRS、不修復幾何、不作事故歸里、分區疊合、模型或正式統計推論。不改組員角色；僅依學生本次確認記錄三人共同完成 Unit 0.5。Git 提交與同步由學生自行操作。 |

### Known Data Issues and Verification Status

以下沿用 Unit 0.1、0.2 的實際檢查及學生審查結果；Unit 0.3 未重做資料診斷，未宣稱問題已解決。Unit 0.4 僅補充環境建置與原始資料可讀性驗證，未解除下列實質資料限制。Unit 0.5 已在 raw 說明 Notebook 重算必要唯讀診斷並補充個體幾何有效性；下列已觀測結果與正式驗證待辦分列，不宣稱 Chapter 1 完成。

| Area | 已知事實、限制及待驗證工作 |
| --- | --- |
| Accident Data | Unit 0.5 重算與 Unit 0.2 一致：2024 原始 51,810×49、第一當事人 22,368；2025 原始 22,762×47、全為第一當事人；合計 45,130 候選紀錄，3 筆缺座標。完整列及第一當事人候選鍵均無重複；2024 候選時地群組各恰一筆第一當事人、已檢查事故情境及傷亡欄群內一致，仍不是官方事故 ID 認證。共同欄 46；道路照明設備／光線為候選跨年映射，尚未認證等價。傷亡及分類缺失、速限 0／502、年齡 -1／0／逾 100 均保留，事故座標 CRS 與官方發布口徑待補；不得把當事人受傷程度取代事故傷亡總數。詳見[原始說明](data/raw/taipei_2024_2025_crashes_raw_documentation.ipynb)。 |
| Village Boundary | Unit 0.5 核對 12 區、456 個 Polygon，CPTVID 為唯一 10 碼、區里名稱無缺失或空白；CPG=UTF-8，PRJ 辨識 EPSG:3826（TWD97、中央經線 121°、公尺）。無缺失、空、無效或完全相同 WKB 幾何；這不認證重疊／縫隙或 2024–2025 邊界一致。官方頁收錄迄 2025-06-17、資源更新 2026-09-21，不能作本機版本與歷史適用證明；原 AREA 定義／單位／計算版本與幾何面積仍未驗證。詳見[原始說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb)。 |
| Population Data | Unit 0.5 核對本機 112 年 1 月至 115 年 10 月；研究 2024、2025 共 24 個月各 456 里、每月 456×3 性別列，兩年里代碼集合一致。全檔 64,722×107，101 個年齡組合計與總計、男＋女與計均一致；無缺失、負值、完整列或年×月×區碼×性別重複。行政區＋里名精確配對仍 455／456，人口「糖?里」／里界「糖蔀里」與歷史紀錄「糖廍里」待官方碼表及正式 crosswalk；人口 11 碼與 CPTVID 10 碼不可自行截碼／補零。年度人口口徑已確認，但月內統計基準日待補；設籍人口不是交通暴露人口。詳見[原始說明](data/raw/taipei_population_age_raw_documentation.ipynb)。 |
| Urban Planning Data | Unit 0.5 精確辨識細計-面 15,508 Polygon＋10 MultiPolygon（總 15,518），細計-文 3 Point；缺 PRJ／CPG、CP950 可讀、CRS=None。面層 143 筆無效幾何（67 自交、52 環自交、15 孔洞在殼外、9 巢狀外殼），未修復。5 組共 11 列原始 WKB 完全相同，部分重疊未檢查；使用分區空白的 4 筆為細部計畫範圍、規劃範圍兩筆及陽明山公園。官方頁描述更新至 114 年 1 月，未認證本機圖資版本；原包／CRS／分類規格仍缺。正式分類、重複／重疊及幾何處理前不計算面積比例，不把規劃分區當實際土地使用。詳見[原始說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)。 |
| Environment | 歷史狀態：Unit 0.1、0.2 所見 Python 3.12.2 預設環境缺 geopandas、shapely、pyproj、pyogrio、scikit-learn、seaborn。Unit 0.4 已以 Python 3.12.2 64-bit 建立 [.venv](.venv/pyvenv.cfg)，無 system-site-packages，不依賴舊 data/temp/python-deps；19 項指定套件及 pip check、GIS／分群／統計／繪圖與實際 Notebook 驗證均通過。[依賴清單](data/code/urban_crash_requirements.txt)及[驗證紀錄](data/code/urban_crash_environment_validation.json)已保存。原 Windows 受限權限曾阻擋 Notebook 連線檔 ACL；獲准提升該次執行權限後通過。VS Code 畫面的 interpreter／kernel 選擇仍需學生手動核對。 |
| Historical Artifacts | 原始資料說明 Notebook 當前缺失；舊衍生資料索引與部分程式有 LF／CRLF 所致 SHA-256 差異，舊嚴格綁定可能停止。歷史索引、已知 hash 與原成果保留，不默默重設綁定、不重跑舊研究；新輸入版本及正式文件另待驗證。 |

待補來源資訊包括里界下載版本與年度適用性、事故座標基準及 2025 第一當事人發布口徑、都市計畫原下載包／CRS／分類說明，以及糖廍里官方代碼列。已確認人口年度口徑不再列為待決；年齡界線、低樣本門檻等仍依上方候選方法處理。

### Project Roadmap and Sequential Handoff

PROJECT.md 是本次研究方向與單元狀態的承接文件，不另建 ROADMAP.md。Unit 0.1–0.4 的審查通過依據為學生本次 Unit 0.5 指示；Unit 0.5 文件化本地完成後停止，等待學生審查，不自動進入 Chapter 1。後續章節及 Unit 拆分依資料品質與學生審查決定，不將規劃記為已執行。

| Chapter / Unit | 狀態 | 研究範圍與條件 |
| --- | --- | --- |
| Chapter 0 / Unit 0.1 Existing Project Audit | 已完成；學生審查通過 | 唯讀盤點與歷史成果辨識，非新案正式分析。 |
| Chapter 0 / Unit 0.2 Research Definition & Feasibility Assessment | 已完成；學生審查通過 | 研究定義、可行性與必要唯讀診斷，尚無正式里層級資料。 |
| Chapter 0 / Unit 0.3 Project Documentation Update | 已完成；學生審查通過；待自行提交 | 依本次 Unit 0.4 指示確認審查通過；原階段僅更新 PROJECT.md，貢獻歸屬及 commit／push 仍待確認。 |
| Chapter 0 / Unit 0.4 Environment Setup | 已完成；學生審查通過；既有貢獻索引待核對 | 依本次 Unit 0.5 指示確認審查通過。獨立 .venv、19 項套件及專用 kernel 的實際測試完成；保留環境紀錄、VS Code 手動核對及受限權限說明。 |
| Chapter 0 / Unit 0.5 Raw Data Documentation | 四份 Notebook 執行及文件化完成；待學生審查及自行提交 | 15 個原始實體檔逐檔 hash／索引，31 個 code cells 在新 .venv 的乾淨 kernel 成功執行並保存輸出；基本診斷不等於正式資料驗證完成。 |
| Chapter 1 Data Validation | 待執行 | 跨年事故正式驗證；里界來源及幾何；人口及代碼對照；都市計畫來源、CRS、分類及幾何；其他資料按需要補充。 |
| Chapter 2 Data Processing | 待執行；依賴資料驗證 | 一致事故層級資料、事故歸里、Dataset A／B1／可用 B2 及其他環境／C，並驗證最終分析資料。 |
| Chapter 3 Exploratory Data Analysis | 待執行 | 事故時空分布、各里樣本數與有效涵蓋率、事故及環境特徵、缺失／極端值／相關性，審查分群特徵與前處理。 |
| Chapter 4 Accident Pattern Segmentation | 待執行 | 模型與群數比較、穩定性、Cluster Profiling、GIS 群組地圖及跨年驗證；不預設必有穩定分群。 |
| Chapter 5 Urban Environmental Analysis（D 原版） | 主要設計；待執行 | 人口與可用都市環境比較、統計分析、效果量、穩健性、社會意義及政策意涵；不作因果推論。 |
| Chapter 6 Urban Environment Segmentation | 有條件；尚未決定執行 | Dataset B 資料品質、特徵適切性及分群可解釋性評估通過後再決定。 |
| Chapter 7 Dual-Clustering Association | 有條件；尚未決定執行 | 兩套獨立且足夠穩定的分群可用後才比較，不預設顯著關聯。 |
| Chapter 8 Prediction | 選用；尚未決定執行 | 先確認目標、時點、樣本與驗證／防洩漏設計；不等同因果或個人風險分析。 |
| Chapter 9 Research Deliverables | 待執行 | 依實際完成研究及教師範本整理成果、報告與簡報，學生自行檢閱及提交。 |

### Unit 0.4 Environment Handoff — 2026-11-25

Unit 0.5 銜接註：本節原「待審查」敘述保留當時狀態；學生已於 Unit 0.5 指示確認 Unit 0.4 審查通過，仍不代表 Git 提交或 VS Code 介面選擇已核對。

- 新環境：工作包根目錄 `.venv/Scripts/python.exe`，Python 3.12.2 64-bit／Windows 11 AMD64，未使用 system-site-packages；全域套件、舊 kernel 及 175 個受保護既有檔案（排除本文件）經前後比較未變。
- [環境與重現指令](data/code/urban_crash_environment.md)、[127 項固定版本依賴清單](data/code/urban_crash_requirements.txt)、[可重跑驗證程式](data/code/validate_urban_crash_environment.py)、[實際測試結果 JSON](data/code/urban_crash_environment_validation.json)。未改寫舊 descriptive_requirements.txt；.venv 與 data/temp 使用原有 Git 忽略規則。
- 專案內 kernel `dssi-urban-crash`／**DSSI Urban Crash** 指向新環境；nbformat／nbclient 已實際執行三個測試 code cells 並核對 sys.executable。命令列不能確認 VS Code 介面目前選擇，學生依環境文件手動核對。
- 合成 CSV、圖表、執行後最小 Notebook、快取及安裝／測試紀錄僅置於 `data/temp/urban_crash_environment/`。合成測試數值不是新研究成果；未建立正式 processed、finding 或實際空間整合。
- 實際唯讀讀取：2024 事故 51,810×49、2025 事故 22,762×47（UTF-8-SIG）；人口 64,722×107（CP950）；里界 456 筆、PRJ 辨識 EPSG:3826；細計-面 15,518 筆／細計-文 3 筆（CP950、CRS=None）；事故對照表 PDF 4 頁。讀取成功不等於資料定義、幾何品質或分析適用性通過；未指派都市計畫未知 CRS。
- 未有未解依賴衝突或未安裝的指定套件；沙箱 Notebook 執行限制及 Windows 非阻斷提示詳見環境文件。既有 CRS／版本／資料口徑／代碼問題仍待驗證，正式 raw 文件化留待 Unit 0.5。
- 本階段成果待學生審查，貢獻歸屬待確認，學生自行 commit／push；環境已具備 Unit 0.5 所需工具，尚未開始下一單元。

### Unit 0.5 Raw Documentation Handoff — 2026-11-25

- 本次起始工作區乾淨；目前 HEAD `56920e4` 已含前階段 PROJECT.md 與四份環境檔案。本次未變更 HEAD，未回填先前的貢獻 reference；舊「待提交」文字保留其歷史狀態，貢獻及遠端推送仍須另行核對，不以本機 tracking ref 認證推送。
- 共同作者／貢獻者：詹明翰、謝子詮、曾翊涵；依學生本次回覆「三者共同完成」，不推定個別分工，不追溯改寫 Unit 0.3／0.4 歸屬。
- 四份正式資料文件位於 data/raw/，依教師 raw 範本保留 Data Description／Change for Your Own Data／Summary／Sample／Summary Stats；完整欄位表、前十列、摘要、已知問題及 A／B／C 來源關係均有實際輸出或明確規劃標記。
- 兩年事故＋PDF 共用事故說明；人口主檔另含里界名稱唯讀比對；兩份 GIS 說明逐一綁定全部現有配套。15 個來源實體檔各有 Data Artifacts 一列，未將正式說明本身當作 raw dataset。
- 四個官方頁的機關、更新日期與欄名於本次查閱；未重新下載原始資料，下載／收到日期、本機版本與歷史適用性仍未知。原 AREA、部分編碼欄及精確統計／發布定義未取得，文件明列未知而未由欄名編造。
- 四個乾淨 dssi-urban-crash kernel，31 個 code cells 全部完成；以 .venv/Scripts/python.exe、從 data/raw/ 工作目錄測試可攜定位，保存執行輸出與讀取前後 hash 檢查。無 processed、crosswalk、幾何修復、事故歸里、分區疊合或研究模型產出。
- 與 Unit 0.2 的事故／人口／里數／精確名稱配對／重複幾何數一致；本次補正面幾何類型細分並新增 143 筆無效面幾何及里界個體有效性診斷。歷史 Notebook、成果、原始檔與教師規範未改寫。
- Chapter 1 須處理：官方事故／座標及跨年欄位映射、傷亡／速限／年齡／缺失；里界版本、年度適用性、重疊／縫隙、AREA；人口正式代碼及糖廍里 crosswalk、統計基準；都市計畫原包、CRS、年代、圖層／分類、無效與重複／重疊幾何。
- Chapter 0 工具與文件已備妥供審查；Unit 0.5 與 Chapter 0 結束仍待學生審查確認，沒有開始 Chapter 1。貢獻 commit reference 由學生自行提交後再核對。

## Historical Research Context

以下保留原夜間事故研究問題與當時的工作焦點原文，**僅為歷史研究階段**；其中「目前」「下一步」「必要範圍」指原記錄時間，不是新案的工作指令。原 Team／AI Agent Context 中的「本次對話」亦指當時紀錄，不用來推定本次學生身分、模型或貢獻歸屬。

### Original Research Question

- 本組於 2026-10-19 確認將研究主軸改為夜間交通事故情境 segmentation：以事故為觀察單位，利用道路、時間與環境特徵進行 PCA，採階層式分群輔助選擇群數，並以 k-means 建立主要群組；照明狀況、死亡與受傷結果不納入分群輸入，而於分群後比較各群的照明異常、無照明、死亡比例及地理分布。研究目的是辨識可解釋的事故情境並建立優先現勘線索，不推論照明改善的因果效果，也不以只有事故案件的資料預測全市道路事故風險。下一步為完成類別轉碼、主要分群特徵確認及 $K=2$ 至 $K=6$ 的實際比較。

### Original Data and Focus Snapshot

| Field | Details |
| --- | --- |
| Data sources / documentation | [臺北市資料大平臺－臺北市死傷交通事故資料](https://data.taipei/dataset/detail?id=2f238b4f-1b27-4085-93e9-d684ef0e2735)，提供機關為臺北市政府警察局交通大隊；目前檔案為民國 114 年（2025 年）。代碼定義見 [事故對照表](data/raw/事故對照表.pdf)，完整檢查見 [原始資料說明](data/raw/taipei_2025_casualty_crashes_documentation.ipynb)。 |
| Unit of observation | 檔案每列皆為 `當事人序號 = 1`；2026-10-16 核對 22,762 列，完整列及「年月日時分＋肇事地點＋座標」候選鍵均無重複。敘述性統計暫以每列一事故；因無官方事故識別碼，觀察單位與路口彙整仍未獲官方確認。 |
| Current task / target variables | 目前六週研究主線為 PCA＋k-means 夜間事故情境 segmentation。2026-11-06 已完成[夜間事故 PCA 與分群比較](finding/夜間事故PCA與分群比較.ipynb)及[K=5群組profile與照明比較](finding/夜間事故五群profile與照明比較.ipynb)。主要K=5分成秋冬傍晚50型、夏季晚間50型、深夜凌晨型、春季晚間50型與低速限晚間型；一般與區塊加權規格ARI=0.843、最佳對齊一致率93.2%，但群組主要由季節、時段及速限區分，道路型態差異較弱。深夜凌晨型照明未開啟／故障與無照明合計10.12%，24小時內死亡事故15/1,186（1.26%），均為五群最高；照明與群組關聯強度很小（Cramér’s V=0.051），全樣本死亡事故僅26件，不作因果解讀。preliminary report可暫以K=5呈現，並以K=2、K=6及後續地理／速限0檢查作敏感度。 |
| Assignment constraints | 六週內以 PCA、階層式分群輔助選群及 k-means 主分析為必要範圍；GMM、prediction 與 counterfactual analysis 不列為必要主分析。分群不得使用照明或傷亡結果；最終群數須綜合 elbow、silhouette、穩定性與可解釋性決定。沒有車流量及非事故道路資料，因此不稱事故率、不預測全市道路事故風險，也不推論照明改善的因果效果。事故單位、類別轉碼、罕見類別處理及重傷辨識仍須於正式分析前確認。 |

### Research Evolution and Artifact Index

- Unit 0.2 已查閱 2026-10-10 提案歷史：當時曾規劃無照明與嚴重程度的 logistic regression，未找到足以認定已實際完成該迴歸的結果；不把構想列為完成分析。
- 保留[舊研究提案](report/taipei-nighttime-unlit-crash-proposal.md)、[敘述統計](finding/敘述性統計.ipynb)、上列含月份分群與 profile，以及[不含月份期中 Notebook](finding/nighttime_no_month_midterm.ipynb)與[期中報告](report/taipei-nighttime-crash-midterm.md)。2026-11-09 的不含月份 K=5 是舊案探索展示，不是新案的群數設定。
- 保留 [Beamer 原始檔](deliverable/slides/taipei-nighttime-crash-3min.tex)、[講稿](deliverable/slides/taipei-nighttime-crash-3min-script.md)、[提案簡報 PDF](<deliverable/slides/資料科學與社會研究 proposal report.pdf>)及 finding/assets 下全部結果。本次未改寫、重跑或更新任何成果。
- 早晨尖峰事故位置與推測通勤方向的探索依學生提供的歷史背景記錄；Unit 0.2 未找到足以核對的專用程式與結果，不作正式結論。

## Data Artifacts

以下保留原有七欄格式與夜間研究的衍生資料紀錄／SHA-256。Unit 0.5 已更新同一份 2025 raw 的正式文件連結與本次核對，並補入其餘原始實體檔；原 2025 raw 歷史敘述與缺失文件路徑仍保留。analysis 是舊案用途，不代表已成為新行政里研究輸入；Dataset A／B／C 均未建立。

**已知缺件／版本限制（Unit 0.1、0.2 診斷，非本次重新驗證）：**下表連結的 `data/raw/taipei_2025_casualty_crashes_documentation.ipynb` 當前缺失，保留歷史路徑與已知身分，狀態為 missing／pending。歷史 hash 不靜默覆寫；Unit 0.1 所見全年衍生檔為 `09c8...`，分群三檔為 `d409...`、`179d...`、`ba81...`，與下表部分紀錄因 LF／CRLF 不同；期中 Notebook 已列接受版本，部分舊綁定仍會停止。這不等於本次重現或所有下游成果已更新。Unit 0.5 新事故說明提供兩年 raw 現況，但未重建該缺失的歷史文件，也未改寫任何舊 finding 的綁定或索引 hash。

2026-11-05 同儕建議評估：依使用者委託判斷是否修訂 proposal，保留既定 PCA／階層式分群／k-means 主線，於 proposal 補充類別編碼、尺度與權重、主成分數敏感性及未降維比較的適用性檢查。唯讀核對既有衍生資料的 6,795 列夜間樣本，四個主要類別變數合計 46 個非缺失代碼，連同速限與時間週期欄位約 51 欄；這是欄位檢查，尚未執行 PCA 或分群。FAMD 僅為替代方法建議，尚非組內確認決定；類別合併及權重規則仍待正式分析前確認。

資料建立或核對後，由 AI 依 [資料銜接規則](FINDING-RULES.md#資料銜接與檔案驗證) 填入實際紀錄，一個資料檔一列。尚無資料時保持空表，不把範例當成已完成結果。

| Dataset | Role | Data file | Documentation | Processing notebook | Verification | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| 臺北市 114 年死傷交通事故明細 | raw | [CSV](data/raw/114年-臺北市死傷交通事故明細.csv) | [2024–2025 新研究原始說明](data/raw/taipei_2024_2025_crashes_raw_documentation.ipynb)；[歷史文件（缺失／pending）](data/raw/taipei_2025_casualty_crashes_documentation.ipynb)；[事故對照表](data/raw/事故對照表.pdf) | not applicable (source) | 2026-11-25：重新計算本機 SHA-256，UTF-8-SIG、22,762×47、全為第一當事人，候選鍵與完整列無重複、2 筆候選紀錄缺座標；已執行新 raw 文件，CRS／官方事件及跨年映射待驗證。歷史驗證紀錄保留：2026-09-29：已核對 UTF-8 with BOM、22,762 列、47 欄、民國 114 年 1–12 月、0 筆完整列重複、欄位缺失、候選事故鍵及主要代碼分布；另已核對 4 頁事故對照表（SHA-256：`f40ded1ded1c816a38f421bc972cdc1320bbd280e647792207ec037d05fd3670`）。夜間規則後續已確認為臺北市當日日落後至隔日日出前，固定 18:00–06:00 作敏感度分析，但尚未實際計算與驗證；觀察單位、事故唯一鍵、重傷所需的其他資料來源或辨識方式、路口彙整仍 pending。 | `61f0bdb52a49176746ab8b66926224b294498c9e26b2dec6eefe44906fdffa0c` |
| 各里人口年齡原始統計 | raw | [112迄今各里人口數按年齡分.csv](data/raw/112迄今各里人口數按年齡分.csv) | [原始資料說明](data/raw/taipei_population_age_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：CP950、64,722×107、112年1月–115年10月；研究24個月各456里，101年齡組加總及男＋女一致，無缺失／負值／鍵重複；455／456精確名稱配對，正式碼表及月基準待驗證。未建立年度人口表。 | `a663a4f0329b18bb0514da7fd9f6845312d08fadef71e566faf1930c03541641` |
| 臺北市 113 年死傷交通事故原始明細 | raw | [113年-臺北市死傷交通事故明細.csv](data/raw/113年-臺北市死傷交通事故明細.csv) | [原始資料說明](data/raw/taipei_2024_2025_crashes_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：UTF-8-SIG、51,810×49；第一當事人 22,368，候選時地群各恰一筆；完整列與第一當事人候選鍵無重複，1 筆候選紀錄缺座標。傷亡／速限／年齡／CRS 等限制見已執行文件；非正式事故表。 | `b6ad23f05658531998f34ba4995a190d03872940ea48013115da89bb2a4e92c5` |
| 臺北市行政里界圖資配套 CPG | raw | [G97_A_CAVLGE_P.cpg](data/raw/G97_A_CAVLGE_P.cpg) | [原始資料說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：文字編碼宣告：UTF-8；本機里名糖蔀里仍保留，正式名稱／碼表待驗證。 五個配套檔均逐檔hash並綁定於已執行文件。 | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` |
| 臺北市行政里界圖資配套 DBF | raw | [G97_A_CAVLGE_P.dbf](data/raw/G97_A_CAVLGE_P.dbf) | [原始資料說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：屬性表：456×28；CPTVID唯一10碼、區里名完整；AREA及其他正式碼定義待補。 五個配套檔均逐檔hash並綁定於已執行文件。 | `2f43f92e84279a45b2512cf453e9b72f706d1ad1402665c946b1a354f75d8577` |
| 臺北市行政里界圖資配套 PRJ | raw | [G97_A_CAVLGE_P.prj](data/raw/G97_A_CAVLGE_P.prj) | [原始資料說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：座標定義：本機WKT辨識EPSG:3826（TWD97、TM中央經線121°、公尺）；不證明事故或都市計畫CRS。 五個配套檔均逐檔hash並綁定於已執行文件。 | `8dac7d82ea889063f9eaa7df408fcaeb7307d32831ea973b6534d0139a4523c5` |
| 臺北市行政里界圖資配套 SHP | raw | [G97_A_CAVLGE_P.shp](data/raw/G97_A_CAVLGE_P.shp) | [原始資料說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：幾何主檔：456 Polygon、12區；無缺失／空／無效／完全相同WKB幾何；年度適用性、重疊／縫隙未認證。 五個配套檔均逐檔hash並綁定於已執行文件。 | `f7fb4813a2283198ca564f5686823c454c5fd832d2f6981a2ee88a94719be3cc` |
| 臺北市行政里界圖資配套 SHX | raw | [G97_A_CAVLGE_P.shx](data/raw/G97_A_CAVLGE_P.shx) | [原始資料說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：幾何索引：與同名SHP／DBF可共同讀取；不以索引可讀認證拓樸。 五個配套檔均逐檔hash並綁定於已執行文件。 | `ab7bc5e63229f676d3580b68e98db59b91a2d327c74ca23b0000ca1c568d414e` |
| 事故代碼對照表參考文件 | raw | [事故對照表.pdf](data/raw/事故對照表.pdf) | [原始資料說明](data/raw/taipei_2024_2025_crashes_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：PyMuPDF 讀取4頁及文字，表單印有112.07.01後適用；主要代碼及逐欄定義附於事故文件。原始下載日期／本機與官方位元組版本未認證，CSV映射及完整職業等碼表仍待補。 | `f40ded1ded1c816a38f421bc972cdc1320bbd280e647792207ec037d05fd3670` |
| 都市計畫 細計-文 DBF | raw | [細計-文.dbf](data/raw/細計-文.dbf) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：3 Point，無無效／完全相同WKB幾何；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `eba92881fc11e574f24024380c946d73cf213e86040663c4070d15b1d552a7be` |
| 都市計畫 細計-文 SHP | raw | [細計-文.shp](data/raw/細計-文.shp) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：3 Point，無無效／完全相同WKB幾何；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `fa1767fc78c69b7683ec53e0fab8937bac6c33868bedee3c3dcc2ed38dcab731` |
| 都市計畫 細計-文 SHX | raw | [細計-文.shx](data/raw/細計-文.shx) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：3 Point，無無效／完全相同WKB幾何；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `32d642964d494f49d08830f9c12857f9f4995b56eebf09ef2be994034b864760` |
| 都市計畫 細計-面 DBF | raw | [細計-面.dbf](data/raw/細計-面.dbf) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：15,508 Polygon＋10 MultiPolygon，143無效；5組11列相同WKB；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `29b0484feef66c6c8417821ada8a28ed1edc0efcdffb492476fe7ada8739e1d4` |
| 都市計畫 細計-面 SHP | raw | [細計-面.shp](data/raw/細計-面.shp) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：15,508 Polygon＋10 MultiPolygon，143無效；5組11列相同WKB；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `67d2ecc469383459e43f2609cf384a4129e09b27c590cbbb82dfa750eba758ee` |
| 都市計畫 細計-面 SHX | raw | [細計-面.shx](data/raw/細計-面.shx) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb) | not applicable (source) | 2026-11-25：15,508 Polygon＋10 MultiPolygon，143無效；5組11列相同WKB；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `277e5f623c5c81865aa7288fac979a279b340899a4b3bc4335638f797fc5fd69` |
| 臺北市 114 年事故敘述性統計輸入 | analysis | [CSV](data/processed/taipei_2025_descriptive.csv) | [資料說明 Notebook](data/processed/taipei_2025_descriptive_documentation.ipynb)；[完整整合版](finding/敘述性統計.ipynb#data-description) | [處理 Notebook](data/code/prepare_descriptive_statistics.ipynb) | 2026-10-16：原始47欄及22,762列完整保留，衍生資料58欄。主要夜間6,795筆、未知2筆。2026-11-06 為建立分群輸入重新核對目前磁碟檔案，列數、欄數、`record_id` 唯一性與夜間樣本數符合既有紀錄，但實際位元組 SHA-256 為 `e98f...`，不同於既有資料說明與 finding 綁定的 `09c8...`；新分群處理明確綁定目前版本，舊敘述分析尚未重新執行或宣稱版本一致。官方事故識別碼、重傷與速限0定義仍待確認。 | `e98fb4c4d62bd08440d58bbe17af7f3c03b48b4bb91e02bf306e48dda8250465` |
| 臺北市 114 年夜間事故分群正式輸入 | analysis | [CSV](data/processed/taipei_2025_nighttime_clustering_input.csv) | [資料說明 Notebook](data/processed/taipei_2025_nighttime_clustering_documentation.ipynb) | [處理 Notebook](data/code/prepare_nighttime_clustering_data.ipynb) | 2026-11-06：由6,795筆主要夜間事故排除3筆關鍵類別欄位缺失及91筆速限為0紀錄，保留6,701筆、11欄；低頻類別未合併。重新讀檔後列數與欄序相符、`record_id` 唯一、無缺失，且不含照明、傷亡、行政區或座標。速限0官方意義仍待確認，後續應作敏感度分析。 | `02869cf20f9362a6bf3d54ca2ca8e4b75dca983069d220bc527d6dbe9122b0f1` |
| 臺北市 114 年夜間事故一般 one-hot 分群矩陣 | analysis | [CSV](data/processed/taipei_2025_nighttime_clustering_matrix_unweighted.csv) | [資料說明 Notebook](data/processed/taipei_2025_nighttime_clustering_documentation.ipynb) | [處理 Notebook](data/code/prepare_nighttime_clustering_data.ipynb) | 2026-11-06：6,701筆、50欄（`record_id`、5個標準化數值欄、44個 one-hot 欄）；重新讀檔、唯一鍵、無缺失、有限值、每個類別區塊列和為1及結果變數排除檢查均通過。 | `6a6d92299d333cce4dcc9b1f425faa28e0d8a20ba2b76dc7221ecc1d85328ab6` |
| 臺北市 114 年夜間事故區塊加權分群矩陣 | analysis | [CSV](data/processed/taipei_2025_nighttime_clustering_matrix_block_weighted.csv) | [資料說明 Notebook](data/processed/taipei_2025_nighttime_clustering_documentation.ipynb) | [處理 Notebook](data/code/prepare_nighttime_clustering_data.ipynb) | 2026-11-06：與一般矩陣使用相同6,701筆及欄序；每個類別區塊除以該區塊類別數平方根。重新讀檔、唯一鍵、無缺失、有限值、數值欄一致及區塊權重檢查均通過；第三階段須與一般矩陣比較，不預先視為較佳模型。 | `88173998c8c597af0ce653e1b6764b03ed2582cdb961c3975de12079ab304e37` |

路徑與連結相對於本專案根目錄。Role 記錄 raw／analysis／train／test 或已確認用途；Verification 說明實際執行的檢查、日期與限制，未完成時明列 pending／failed。SHA-256 由實際檔案計算。外部整理檔沒有產生程式可記 not available；原始來源可記 not applicable (source)。

2026-10-16 補充：raw CSV 與 PDF 雜湊均再次核對一致；原索引所列 `data/raw/taipei_2025_casualty_crashes_documentation.ipynb` 目前工作區不存在，保留歷史紀錄並標示文件缺失，不宣稱已檢閱該 Notebook。本次處理與分析的定義、檢查和結果記於新增三份 Notebook。上列 raw 舊紀錄中的「尚未計算夜間」為先前狀態，本次已在衍生資料中完成。

## Key Contributions

**課程原則：所有 contribution 都必須由學生在 VS Code 自行 commit 並 push。** 各成員隨成果更新下表，每項貢獻一列，記錄誰、做了什麼，以及實際包含該成果的 commit 連結或 SHA。AI 可整理待提交紀錄，在學生操作後唯讀核對再回填。程式、資料處理、文件、提案及專案紀錄的修改都適用；外部成果須有已 commit 的說明或連結紀錄可追溯。

尚未 commit 的工作標示「待提交」，已有 reference 但尚未核對者標示「待核對」；兩者均不視為完成貢獻紀錄。檔案連結不能取代 commit reference。不要以 commit 次數或程式行數替代成果評估。

已核對的本地 commit 不等於已 push；在 reference 後註明「推送待核對」或經證實的「待 push」，遠端目標分支包含該 commit 的證據核對完成後才記「已推送並核對」。學生自行回報但未核對時註明來源。貢獻表回填後，由學生在下一次 commit／push 納入；reference 指向先前的成果 commit，不要求填該表更新自身的未來 hash。

姓名與貢獻歸屬須由學生提供或確認；資訊缺少時先詢問，未回答前保留待填，不以 commit 作者直接認定實際負責人。commit 用來核對成果紀錄，不取代學生確認的分工。

| Name | Contribution | Commit reference |
| --- | --- | --- |
| 待確認 | 評估同儕對類別變數與 PCA 的建議，核對夜間樣本類別數並局部修訂 [Project Proposal](report/taipei-nighttime-unlit-crash-proposal.md) 的方法與限制；實際負責成員待確認。 | 待提交（貢獻紀錄未完成） |
| 謝子詮 | 提供 [臺北市 114 年死傷交通事故原始資料](data/raw/114年-臺北市死傷交通事故明細.csv)與[事故對照表](data/raw/事故對照表.pdf)，並建立及核對 [原始資料說明 Notebook](data/raw/taipei_2025_casualty_crashes_documentation.ipynb)。 | 待提交（貢獻紀錄未完成） |
| 詹明翰 | 在 Codex 協助下製作並執行 [樣本、光線及夜間照明敘述性統計](finding/敘述性統計.ipynb)、[資料整理程式](data/code/prepare_descriptive_statistics.ipynb)及[衍生資料說明](data/processed/taipei_2025_descriptive_documentation.ipynb)，核對 PDF 代碼與日出日落定義，保存六份表格 CSV，更新本次資料索引。後續補充四份工作 Notebook 的步驟說明與結果解讀，將資料說明的七個類別摘要分表呈現並重新執行驗證。 補充Astral方法定義，依確認改採全年最早日出／最晚日落固定時段並同步重跑三份Notebook及表格。 新增3×2照明與日夜交叉分析、不同分母比例及三份表格CSV，已重跑正式分析並核對原始代碼與缺值排除。 整合全部資料說明與七張類別摘要至正式finding，加入目錄、分章表格、簡報重點與CSV索引，已從乾淨kernel執行且既有九份表格及資料版本不變。 將文件重編為連續八節，移除重複表1/2與CSV及製作階段敘述，將交叉分析、夜間比較、敏感度及解讀融入各節，重跑後資料與保留八份CSV數值不變。 另依確認規則製作並執行[夜間事故分群資料整理](data/code/prepare_nighttime_clustering_data.ipynb)與[三份輸出資料說明](data/processed/taipei_2025_nighttime_clustering_documentation.ipynb)，建立正式輸入、一般 one-hot 及類別區塊加權矩陣並完成重新讀檔驗證。 完成並執行[夜間事故 PCA 與分群比較](finding/夜間事故PCA與分群比較.ipynb)，比較兩種矩陣的PCA、K=2至K=6 K-means、跨種子穩定性、Ward抽樣與跨矩陣一致度，產出候選群數及支援圖表。 完成並執行[K=5群組profile與照明比較](finding/夜間事故五群profile與照明比較.ipynb)，建立五群命名與profile，檢查區塊加權敏感度，並計算照明三分類、死亡比例、Wilson信賴區間及照明卡方關聯。 | 待提交（貢獻紀錄未完成） |
| 待確認 | 確認六週研究改採 PCA、階層式分群輔助選群及 k-means 的事故情境 segmentation，並修訂 [Project Proposal](report/taipei-nighttime-unlit-crash-proposal.md)及專案研究脈絡。實際負責成員待學生確認。 | 待提交（貢獻紀錄未完成） |
| 待確認 | 2026-11-25 Unit 0.3：依學生已審查的 Unit 0.1、0.2 及本次決策更新 [PROJECT.md](PROJECT.md)，記錄新行政里研究的題目、RQ、確立設定、候選特徵／方法、資料限制及單元規劃，保留舊夜間研究與索引；僅完成文件維護，無新正式資料處理或分析。本次實際負責成員待學生確認，不由舊對話或 Git 作者推定。 | 待提交（貢獻紀錄未完成） |
| 待確認 | 2026-11-25 Unit 0.4：建立獨立 Python 3.12 環境，安裝及驗證所需套件、GIS／分群／統計／繪圖、原始資料唯讀讀取及專用 kernel 的最小 Notebook；保存[環境文件](data/code/urban_crash_environment.md)、[依賴清單](data/code/urban_crash_requirements.txt)、[驗證程式](data/code/validate_urban_crash_environment.py)與[結果](data/code/urban_crash_environment_validation.json)，更新本文件；未執行正式研究分析。實際負責成員待學生確認，未自行改寫作者或分工。 | 待提交（貢獻紀錄未完成） |
| 詹明翰、謝子詮、曾翊涵 | 2026-11-25 Unit 0.5：依學生本次確認共同完成[事故與PDF說明](data/raw/taipei_2024_2025_crashes_raw_documentation.ipynb)、[人口說明](data/raw/taipei_population_age_raw_documentation.ipynb)、[里界說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb)及[都市計畫說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)，保存31個code cells的乾淨kernel實際輸出、15個原始檔hash與唯讀診斷，更新本文件／逐檔索引；未執行正式清理或研究分析。共同貢獻不推定個別分工，未追溯改寫先前單元歸屬。 | 待提交（貢獻紀錄未完成） |
