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
| Population | 使用行政里層級「計」，不重複加總男、女；年度平均人口為12個月存量平均，高齡65歲以上、兒童0–14歲比例為同期間年齡人口和除以總人口和。合併規格用24個月平均與24個月分子／分母重算，不直接平均年度比例；缺月／缺值／零分母不補零。Unit 1.3僅記憶體試算，未輸出年度B1資料。 |
| Interpretation | 設籍人口不是交通暴露人口；不假設當事人居住於事故發生地；都市計畫分區不等於實際土地使用。 |
| Scope exclusions | 排除付費電信信令人流；暫不執行 Causal Inference，Prediction 為選用延伸。 |
| Population linkage policy — Unit 1.4 Revision | 學生接受糖廍里63000070015↔6300700015，456里同規則納主要人口／都市環境及後續整合，標準名稱糖廍里。原糖?／糖蔀名稱與provisional_match證據狀態保留，不再限制資格或僅因此設NA；不另作排除糖廍里敏感度、不再查碼。此決策取代所有先前相反設定；Unit 1.3不重跑，舊Notebook僅保留當時規則／試算。 |
| Fixed research geography and area | 依Unit 1.3明確審查決策，採現有456里作2024–2025固定研究地理單位，保留原geometry及歷史空間錯配限制，不宣稱兩年歷史幾何完全相同。密度以EPSG:3826原geometry.area／1e6為km²分母，AREA只供稽核；不修復、消除重疊或填洞。 |
| Urban planning working assumption — Unit 1.5 review | 學生已通過Unit 1.4：續用原細計面圖層，僅記憶體工作副本採EPSG:3826，證據維持B級strongly supported，非本機CRS正式認證；不補PRJ、不換主計、不處理細計-文或繼續查其CRS。固定都市計畫快照的生效及2024–2025歷史適用仍未知，不宣稱兩年事前環境。糖廍里沿用最新Revision，456里同規則。 |
| Adopted processing policies — Unit 1.6 | 學生通過Unit 1.5：原有效面不修復，無效143筆優先linework、保留來源／非面稽核，不合理或方法敏感者待確認；296複合鍵／13研究類與特專混合獨立保留，陽明山公園維持unclassified，IF／B指定用途／C文教作必要映射審查但不直接覆寫crosswalk。採方案B：排除三範圍、同類union、扣跨類及已分類對未知交集，不設類別優先或正規化100%，分母固定原里面積。這些政策已採用，個別修復／分類例外及品質門檻仍須實證診斷與審查。 |
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

Unit 1.1審查已確認後續比較前八個事故型態特徵與加入`multi_injury_ratio`的九特徵規格；多人受傷比例保留候選、照明暫不納入主要分群，均尚未實作。平日限定時段、天文夜間及嚴格路口內定義仍為敏感度候選。第一當事人年齡、性別、車種及事故道路情境先列補充變數，不代表全部涉入者，也不直接全部納入主分群。舊研究排除照明及傷亡的規則保留其舊案適用範圍；是否另有教師共同要求仍須依明確規範核對，不把歷史設定自動套用於新案。

**Dataset B — Urban Environment Features**

| Block | 候選變數與限制 |
| --- | --- |
| B1 人口結構 | `population_density`、`elderly_population_ratio`（65+）、`child_population_ratio`（0–14）三主要候選；年度12月、合併24月規則與固定幾何面積不變。456里[crosswalk](data/processed/village_crosswalk.csv)保留455 verified_exact_match＋1 provisional_match，但依Unit 1.4 Revision糖廍里已接受，與其他455里同規則納入，不能僅因provisional設NA或排除，不另作糖廍排除敏感度。舊Unit 1.3年度912列的910可用／2待審只是當時試算，未重跑或輸出正式B1；後續程式不得沿用舊資格限制。其他人口變數仍補充選項。 |
| B2 都市計畫分區 | 五候選`residential_zoning_ratio`、`commercial_zoning_ratio`、`industrial_zoning_ratio`、`educational_zoning_ratio`、`park_green_zoning_ratio`維持。Unit 1.6承接B級3826與方案B，已完成[逐里記憶體診斷](data/code/taipei_data_integration_readiness.ipynb)：全部456里仍有未覆蓋／未知或待審範圍，僅能報已辨識覆蓋及條件性保守下界L，不冒充完整比例；條件性上界min(1,L＋不確定聯集比例)須接受目前包絡假設，否則不可認證。品質門檻50／70／80／90／95／99%對應441／331／162／49／16／2里，未選正式門檻。未知不補零，特殊混合等已知非主類不當未知，不因B2不足排除事故或B1。正式B2為Partially ready，建議先D原版B1基礎版；觀測L／品質作補充與穩健性，未輸出正式B2。 |
| B3 其他環境（尚未取得或選用） | 道路密度、主要幹道比例、路口密度、人行道密度、號誌設施、捷運活動程度；不將候選項目記為已取得資料。 |

Dataset B 不含事故數、事故組成、傷亡結果，亦不以事故紀錄中的道路特徵取代全里道路環境。單一時間快照依實際版本描述，不宣稱已有兩年度獨立環境資料；分區未覆蓋、未分類或缺失不當作 0。

**Dataset C — External Profiling Variables**

`annual_accident_count`、`total_injuries`、`total_fatalities_24h`、`total_fatalities_2_30d`、`fatal_accident_ratio`、`injuries_per_crash`、`accidents_per_km2`、`low_count_flag`，用於事故負擔及群組比較。傷亡缺值不能以 0 補成完整總數；24 小時與 2–30 日死亡先分列。每平方公里事故數是事故空間密度，不是暴露校正後事故率。

同一變數在替代模型變更角色時須記錄；參與分群的變數差異不能當成獨立驗證。A 已含多人受傷比例時，C 的受傷負擔比較也不是完全獨立的驗證。

## Team

**每組預設 3–4 位學生（教師預設）**，以學生已確認的實際名單為準。AI 在學生開始使用時，主動確認全組成員姓名、各自已確認的實際工作，以及目前對話的學生是哪位。先沿用對話或本文件中已確認的資訊，只補問缺少的部分，不只是留下待填。尚未分配的工作由組員決定，未確認的欄位保留「待確認」。已確認的人數不同時依實際名單記錄，不為符合預設補造或刪除成員。

AI 只整理學生提供或明確確認的姓名與工作，不自行指派 PM／DE／DA，也不從 Git 作者、電腦帳號、檔名、範本示例或檔案提供者推定作者或責任；保留有依據的既有作者，不自動改成本次提供檔案的學生。等待回答時可先進行不依賴歸屬的檢查或討論。保留下列既有欄位，按已確認名單一人一列；尚無名單時保持空表，不先填入 3 或 4 位假成員。`Role` 記錄學生提供的角色與實際工作，確認姓名與工作不需額外要求學號或 GitHub 帳號。

目前對話者沿用既有詹明翰紀錄；2026-11-26學生正式確認下列PM／DE／DA分工，取代先前角色待釐清設定。歷史上曾自述「除了PM跟DA的那個」，該舊說法僅作歷史紀錄，不再作現行分工依據。

| Name   | Student ID | GitHub Account | Role |
|--------|------------|----------------|------|
| 謝子詮 | B12303045  | chester931225  | Data Engineer（DE）；負責data/資料蒐集、文件化、品質、跨年標準化、GIS、清理整合及特徵工程，交付可直接分析且文件完整的processed dataset。 |
| 曾翊涵 | B12607049  | TBD | Project Manager（PM）；統合研究意見、協調分工與進度、審查教師規範／Git及文件完整性、會議紀錄、四次口頭報告、異常回報及成果／貢獻協調；不單方面決定研究分工。 |
| 詹明翰 | B12302350  | hank94224-commits | Data Analyst（DA）；負責finding/研究背景與文獻、問題方法、變數需求、EDA、統計圖表、PCA／K-means／階層分群、穩健性、群間推論與解釋、Finding Notebook及期末海報。 |

### Permanent Team Responsibilities and Unit Ownership — 2026-11-26

以上為學生正式確認、持續適用於後續Chapters／Units的職務；預定職務、單元任務分配及實際完成貢獻分開記錄。共同作者不等於主要負責人，不回溯改寫既有Notebook作者、歷史貢獻或Git紀錄。

- DE依DA研究需求補充／調整資料，交付已驗證、可直接使用的processed dataset及說明；DA優先讀取該版本，除少量分析衍生變數外，不重新執行完整raw清理整合。PM協調、規範及交付審查，任務分配由團隊確認。
- 後續每Unit開始前記錄Primary Owner、Collaborator、Reviewer、Deliverables；完成後依可核對事實記錄Actual Contribution，不因職務推定已執行或已審查。成員依教師規範自行操作實際工作相關Git提交，不建立虛假author或history。

| Unit | Primary Owner | Collaborator | Reviewer | Deliverables | Actual Contribution |
| --- | --- | --- | --- | --- | --- |
| Unit 1.6 Data Integration Readiness Review | 謝子詮（DE）：整合可行性、GIS診斷、品質驗證 | 詹明翰（DA）：資料定義及分析適切性確認 | 曾翊涵（PM）：進度、規範與交付成果審查 | [整合審查Notebook](data/code/taipei_data_integration_readiness.ipynb)；PROJECT.md正式分工、政策、readiness及Chapter 2交接 | 學生本次明確確認「目前僅本次Codex協助執行，成員驗收與審查尚待完成」。本機執行證據於下方交接據實記錄；不因職務／共同作者推定任何成員已完成修改、驗收或PM審查。 |

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
| Data sources / documentation | [事故官方來源](https://data.taipei/dataset/detail?id=2f238b4f-1b27-4085-93e9-d684ef0e2735)：[2024 CSV](data/raw/113年-臺北市死傷交通事故明細.csv)、[2025 CSV](data/raw/114年-臺北市死傷交通事故明細.csv)、[事故對照表](data/raw/事故對照表.pdf)；[人口 CSV](data/raw/112迄今各里人口數按年齡分.csv)及[官方說明](https://data.taipei/dataset/detail?id=a6394e3f-3514-4542-87bd-de4310a40db3)；[里界 SHP](data/raw/G97_A_CAVLGE_P.shp)及[官方來源（學生提供）](https://data.taipei/dataset/detail?id=6b17b31d-4e16-495e-95b1-9fd1f47c80d8)；[細計-面](data/raw/細計-面.shp)、[細計-文](data/raw/細計-文.shp)及[官方來源（學生提供）](https://data.taipei/dataset/detail?id=3bab0a01-7936-4218-8cb5-f74dfcb43dda)。四個官方來源網址均由學生於 Unit 0.4 提供／確認；都市計畫本機六檔已於Unit 1.4與2026-04-09官方細計資源逐bytes核對一致；原下載日期、計畫生效日與其他圖資歷史適用性仍未認證，詳下表。Unit 0.5 已建立並執行[兩年事故及 PDF 說明](data/raw/taipei_2024_2025_crashes_raw_documentation.ipynb)、[人口說明](data/raw/taipei_population_age_raw_documentation.ipynb)、[里界說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb)及[都市計畫說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)；15 個來源實體檔（含 GIS 配套）逐檔列於 Data Artifacts。新增[Unit 1.1事故驗證](data/code/taipei_2024_2025_crash_validation.ipynb)、[Unit 1.2里界驗證](data/code/taipei_village_boundary_validation.ipynb)及[Unit 1.3人口驗證／crosswalk處理](data/code/taipei_population_validation.ipynb)；[crosswalk說明](data/processed/village_crosswalk_documentation.ipynb)與[新增官方碼表證據說明](data/raw/unit13_official_code_evidence_documentation.ipynb)銜接實際檔案，新增[Unit 1.4都市計畫來源／CRS驗證](data/code/taipei_urban_planning_crs_validation.ipynb)與[官方證據包說明](data/raw/unit14_urban_planning_evidence_documentation.ipynb)；四份既有原始文件不改寫。2026-11-25 已查閱四官方頁的機關、欄名及更新日期；網頁更新日與本機下載／版本證明分開記錄。 |
| Unit of observation | 基礎資料為行政里×年；由 2024 第一當事人 22,368 筆及 2025 現有第一當事人 22,762 筆候選事故建立。Unit 0.2 的檔內唯一性與一致性診斷支持此操作口徑，但無官方事故 ID；尚未完成 GIS 空間配對，不宣稱已有 45,130 筆可用分析樣本。 |
| Current task / target variables | Chapter 0、Unit 1.1–1.5依學生本次指示審查通過。[Unit 1.6整合準備審查](data/code/taipei_data_integration_readiness.ipynb)本地完成15個乾淨kernel code cells及六圖：45130候選事故兩CRS／within／covered_by、區名及地址距離、143修復採用審查、456里覆蓋、912／456鍵值整合及readiness。沒有正式資料集輸出，Unit 1.6待學生驗收／PM審查；不宣稱Chapter 1全部無條件通過，Chapter 2未開始。正式分工與實際貢獻區分見Team及下方交接。 |
| Assignment constraints | Unit 1.6允許真實候選事故CRS／空間配對、記憶體幾何及逐里覆蓋、必要整合試算、新審查Notebook與最小PROJECT更新；沿用.venv及DSSI Urban Crash kernel。不改原始資料、既有Notebook、兩crosswalk或原里界geometry，不重跑Chapter 0／Unit 1.1–1.5，不再查糖廍，不安裝套件、不將工作CRS當官方認證，不輸出正式事故清理／歸里／年度人口／修復GIS／A/B/C或矩陣，不作模型或推論。共同作者保留，正式PM曾翊涵／DE謝子詮／DA詹明翰依最新指示；本輪僅Codex協助，成員驗收審查待完成。Git操作由實際成員自行執行。 |

### Known Data Issues and Verification Status

以下沿用 Unit 0.1、0.2 的實際檢查及學生審查結果；Unit 0.3 未重做資料診斷，未宣稱問題已解決。Unit 0.4 僅補充環境建置與原始資料可讀性驗證，未解除下列實質資料限制。Unit 0.5 已在 raw 說明 Notebook 重算必要唯讀診斷並補充個體幾何有效性；下列已觀測結果與正式驗證待辦分列，不宣稱 Chapter 1 完成。Unit 1.1更新事故驗證、碼表與候選規則；Unit 1.2依學生已通過審查的決策更新狀態，另實際驗證現有里界幾何／拓樸／面積。Unit 1.3另核對研究期人口及代碼，接受固定幾何／面積決策，但不重跑Unit 1.2拓樸或舊研究；Unit 1.4只補都市計畫來源／CRS診斷並記錄人口Revision，不重跑Unit 1.3，未宣稱Chapter 1全部完成。

| Area | 已知事實、限制及待驗證工作 |
| --- | --- |
| Accident Data | Unit 1.1重算：2024原始51,810×49、第一當事人22,368；2025原始22,762×47、全為第一當事人，合計45,130候選，非GIS後最終樣本。groupby保留缺失鍵，所有原始列均納診斷；候選群各恰一筆第一當事人，事故情境群內一致，完整列及第一當事人候選鍵重複皆0；候選鍵不是官方ID。49列schema覆蓋兩年全部欄位，照明映射、死亡發布口徑、職業完整碼表及座標基準仍待證。候選型態／位置有效N為22,359／22,750，受傷人數22,367／22,761，座標可解析22,367／22,760。速限0為328／315、502為1／0；年齡負值1／0、0歲222／217、逾100歲11／18，均不自動判錯／刪事故。詳見[驗證及候選規則](data/code/taipei_2024_2025_crash_validation.ipynb)。 |
| Village Boundary | Unit 1.2重新核對12區456 Polygon、CPTVID唯一非空10碼字串、區里組合唯一、UTF-8及EPSG:3826；無缺失／空／無效／非有限座標／非正面積／完全相同或空間等價幾何、無bbox結構異常。3IQR寬高篩查27里僅大小離群標記，非錯誤。空間索引1,380對中157對正面積交集，涉143里（125同區、32跨區），總1.161746m²，最大士林天壽／天玉1.150362m²，僅1對大於1m²，未採容差忽略或修復。聯集1 Polygon、335孔洞共69.351601m²、最大37.454176m²，外部覆蓋缺獨立市界未完整驗證。幾何面積和268.550083831km²、聯集268.550082669km²；AREA定義仍未知，條件式數值比較最大相對差34.2009%（南港東明），全市正負差抵銷不代表逐里一致。官方網頁更新2026-09-21與DBF寫入欄2026-09-16均非幾何生效版本；2024／2025年末均456里但名稱／代碼／幾何一致性無完整歷史證據。固定456里與幾何面積分母已依Unit 1.3審查決策採用，歷史幾何相同仍未證實；本次人口碼表快照穩定不解除幾何限制。詳見[已執行驗證](data/code/taipei_village_boundary_validation.ipynb)及保留的[raw說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb)。 |
| Population Data | Unit 1.3重算研究期2024–2025：24月、每月456里×計男女三列，共32,832列，選計10,944列；年×月×碼×性別唯一，101年齡合計及男＋女一致，無人口缺失／非數值／負值／非有限值，兩年碼集合一致且同碼無觀測名稱變動。五份戶政司11109／11406／11409／11411／11509臺北456里代碼／名稱相同，支持糖廍里63000070015；本機人口糖?里及里界糖蔀里6300700015均保留。Crosswalk為455 verified_exact_match、1 provisional_match，無重複／跨區／未配對；官方10碼CPTVID轉換規範仍缺，455里規律不作官方認證。Unit 1.3年度912列、合併456列僅為當時記憶體試算，910可用／2待審不再作現行資格限制。Unit 1.4最新Revision已接受糖廍配對，456里同規則納入主要分析；保留provisional證據狀態，但不得僅因此設NA／排除，不另作糖廍排除敏感度或追加查碼。原Notebook不重跑。精確月基準日與歷史空間錯配仍受限，設籍人口非交通暴露。詳見[驗證](data/code/taipei_population_validation.ipynb)、[對照表說明](data/processed/village_crosswalk_documentation.ipynb)。保留先前Unit 0.5原檔觀測：112年1月–115年10月、64,722×107及全檔品質檢查，未重跑其餘年度；[原始說明](data/raw/taipei_population_age_raw_documentation.ipynb)未修改。 |
| Urban Planning Data | Unit 1.4已取官方主／細計ZIP，本機細計六配套與官方2026-04-09資源逐bytes／hash相同，全屬性及WKB亦一致，來源關係A級；頁內容標示更新至2025-01，各計畫生效日與原下載日未知。兩ZIP均無PRJ／CPG／XML；同族市府GIS服務來源metadata為3826、顯示3857，但面數15,511與本機15,518不同，不能認定全檔同版。3個以屬性與輪廓唯一辨識的共同面在3826假設下輪廓差約1e-9m，3828約854.034m；面層B級3826工作候選，點註記缺控制為C級，未正式指定CRS。保留Unit 0.5：15,508 Polygon＋10 MultiPolygon、143無效、5組11列相同WKB、97原圖層／260分區碼、4使用分區空白及範圍要素；未修復／刪重／分類／算面積。主計面3,840／點3,824亦缺CRS，無更完整CRS優勢，不直接替換細計。只可提出固定快照環境候選，非事前資料／實際土地使用。詳見[來源及CRS驗證](data/code/taipei_urban_planning_crs_validation.ipynb)與保留的[raw說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)。 |
| Environment | 歷史狀態：Unit 0.1、0.2 所見 Python 3.12.2 預設環境缺 geopandas、shapely、pyproj、pyogrio、scikit-learn、seaborn。Unit 0.4 已以 Python 3.12.2 64-bit 建立 [.venv](.venv/pyvenv.cfg)，無 system-site-packages，不依賴舊 data/temp/python-deps；19 項指定套件及 pip check、GIS／分群／統計／繪圖與實際 Notebook 驗證均通過。[依賴清單](data/code/urban_crash_requirements.txt)及[驗證紀錄](data/code/urban_crash_environment_validation.json)已保存。原 Windows 受限權限曾阻擋 Notebook 連線檔 ACL；獲准提升該次執行權限後通過。VS Code 畫面的 interpreter／kernel 選擇仍需學生手動核對。 |
| Historical Artifacts | 原始資料說明 Notebook 當前缺失；舊衍生資料索引與部分程式有 LF／CRLF 所致 SHA-256 差異，舊嚴格綁定可能停止。歷史索引、已知 hash 與原成果保留，不默默重設綁定、不重跑舊研究；新輸入版本及正式文件另待驗證。 |

待補來源資訊包括里界下載版本與年度適用性、事故座標基準及 2025 第一當事人發布口徑、都市計畫下載檔專屬CRS／生效歷史／完整官方分類說明。Unit 1.5已承接學生接受面層B級3826工作假設，新增分類依據但非完整官方碼表，未知覆蓋及修復例外仍待審（見下方交接）；不再重開CRS或點註記調查。糖廍里依最新Revision不再追加代碼查證或設定分析資格障礙。Unit 1.3已取得官方人口碼與糖廍里正式名稱，主特徵65歲以上／0–14歲及年度／合併口徑已確認；補充最高齡界線、低樣本門檻等仍待審。事故CRS查閱市府與data.gov.tw同資料集後仍未確認：EPSG:4326僅工作候選，不能排除EPSG:3824等地理基準，未指派CRS；死亡兩欄不合併；另有6／4筆第一當事人程度碼5但2–30日總量為0，屬待查單向一致性疑點，不以單位不同略過或自行填補，詳見Unit 1.1來源表／表22C／R20。

### Project Roadmap and Sequential Handoff

PROJECT.md承接研究方向及單元狀態，不另建ROADMAP.md。Chapter 0及Unit 1.1–1.5已依學生本次指示審查通過；Unit 1.6本地完成後停止待審，不自動進入Chapter 2。事故工作CRS／異常歸里與B2規格仍需明確採用，不能將Chapter 1所有資料標為無條件通過；B2限制不阻其他具條件資料獨立處理。糖廍里以已接受政策正常納入。

| Chapter / Unit | 狀態 | 研究範圍與條件 |
| --- | --- | --- |
| Chapter 0 Project Transition | 已完成；學生審查通過 | 依學生Unit 1.1明確指示，0.1–0.5盤點、定義、脈絡、環境與raw文件化均完成；未建立新研究正式分析資料。 |
| Chapter 0 / Unit 0.1 Existing Project Audit | 已完成；學生審查通過 | 唯讀盤點與歷史成果辨識，非新案正式分析。 |
| Chapter 0 / Unit 0.2 Research Definition & Feasibility Assessment | 已完成；學生審查通過 | 研究定義、可行性與必要唯讀診斷，尚無正式里層級資料。 |
| Chapter 0 / Unit 0.3 Project Documentation Update | 已完成；學生審查通過；待自行提交 | 依本次 Unit 0.4 指示確認審查通過；原階段僅更新 PROJECT.md，貢獻歸屬及 commit／push 仍待確認。 |
| Chapter 0 / Unit 0.4 Environment Setup | 已完成；學生審查通過；既有貢獻索引待核對 | 依本次 Unit 0.5 指示確認審查通過。獨立 .venv、19 項套件及專用 kernel 的實際測試完成；保留環境紀錄、VS Code 手動核對及受限權限說明。 |
| Chapter 0 / Unit 0.5 Raw Data Documentation | 已完成；學生審查通過；既有貢獻索引待核對 | 依學生Unit 1.1指示確認通過；四份已執行raw文件、15個原始檔hash及索引保留，不重建或覆寫。 |
| Chapter 1 Data Validation | 進行中；1.1–1.3審查通過，1.4本地完成待審 | 事故／里界／人口與來源CRS診斷完成，糖廍配對已接受但證據狀態保留；都市計畫面工作CRS、幾何／分類／覆蓋及事故datum／實際配對仍待後續，不等於正式整合完成。 |
| Chapter 1 / Unit 1.1 Cross-Year Traffic Accident Data Validation | 已完成；學生審查通過；待自行提交 | 依本次Unit 1.2指示確認通過；[Notebook](data/code/taipei_2024_2025_crash_validation.ipynb)與原輸出完整保留，下方記錄審查決策，未重跑／清理／合併／歸里。 |
| Chapter 1 / Unit 1.2 Village Boundary Validation | 已完成；學生審查通過；待自行提交 | 依本次Unit 1.3指示確認通過；[Notebook](data/code/taipei_village_boundary_validation.ipynb)與原輸出保留，接受固定456里及幾何面積分母，歷史／拓樸／AREA／datum限制不因此消失。 |
| Chapter 1 / Unit 1.3 Population Data Validation & Village Code Crosswalk | 已完成；學生審查通過；待自行提交 | 原[驗證文件](data/code/taipei_population_validation.ipynb)、[crosswalk](data/processed/village_crosswalk.csv)及[說明](data/processed/village_crosswalk_documentation.ipynb)保持原樣、不重跑。最新Revision接受糖廍納入456里主要分析；provisional僅證據狀態，舊2列NA／待審資格規則已被取代，無須另作糖廍排除敏感度或追加查碼。 |
| Chapter 1 / Unit 1.4 Urban Planning CRS & Source Validation | 已依Unit 1.5指示審查通過；提交仍由學生自行處理 | [Notebook](data/code/taipei_urban_planning_crs_validation.ipynb)、[官方證據包說明](data/raw/unit14_urban_planning_evidence_documentation.ipynb)保留原輸出及四圖；採原細計面B級EPSG:3826工作假設及固定快照限制，點註記排除，不升級正式認證。 |
| Chapter 1 / Unit 1.5 Geometry & Zoning Validation | 已依Unit 1.6指示審查通過；Git提交仍由學生自行處理 | [驗證Notebook](data/code/taipei_urban_planning_geometry_validation.ipynb)、[分類crosswalk說明](data/processed/urban_zoning_crosswalk_documentation.ipynb)、[分類來源說明](data/raw/unit15_zoning_classification_evidence_documentation.ipynb)原檔保留；linework優先、296鍵／13類、方案B及例外待確認政策已採用，不代表所有幾何／B2已無條件通過。 |
| Chapter 1 / Unit 1.6 Data Integration Review | 本地完成；待學生驗收及PM審查，未自行提交 | [Notebook](data/code/taipei_data_integration_readiness.ipynb)15 code cells／六圖，兩CRS結果相同但datum未認證，143修復105算法一致候選／38待審，456里品質及912／456整合通過。B2僅部分就緒，其餘可依明示假設進正式處理。 |
| Chapter 2 Data Processing | 未開始；本單元審查後可分項進行 | 建議2.1事故標準化→2.2里基礎／歸里→2.3 A/C；2.4 B1可獨立推進；2.5 B2限經審查規格；2.6整合驗證。DE交付已文件化processed資料，DA確認需求及驗收，PM協調／審查；各Unit開始前由團隊確認任務，以下非已完成貢獻。 |
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

### Unit 1.1 Accident Validation and Candidate Definitions — 2026-11-26

- Chapter 0銜接：學生已於本次指示確認0.1–0.5通過；上方Unit 0.5原「待審查」敘述保留當時狀態，不再作為本單元阻礙。共同作者沿用詹明翰、謝子詮、曾翊涵，不回填個別分工。
- 文件索引：[跨年事故驗證與候選定義](data/code/taipei_2024_2025_crash_validation.ipynb)；§1單位／研究ID，§2完整欄位映射，§3官方碼表與年度分布，§4缺失／特殊／碼外，§5座標證據，§6 Dataset A，§7 Dataset C，§8清理規則／Sample Flow，§9待審決策。正式交付為一份已執行Notebook，未另建事故資料表。
- 固定輸入為兩年CSV、本機PDF及Unit 0.5事故raw文件；原始三檔hash與0.5一致，讀前／讀後檢查均通過。11個code cells於乾淨dssi-urban-crash kernel、.venv Python 3.12.2，從data/code工作目錄完整執行；不連網、不重跑舊Notebook，輸出僅保存在新文件，開發／驗證暫存位於data/temp/unit11_validation/。
- 研究用record_id建議由source_year、完整來源hash及CSV解析後的1-based原始邏輯列序構成，source_file另留；篩選第一當事人後不重編號。已於記憶體核對跨年唯一，但不是官方事故ID，候選事件鍵只用於診斷，不能據以自動刪重。
- 主要型態、位置、天候、道路型態、車種、性別等觀測碼均在本次可核對表單印列集內；照明／視距有版本混列，職業碼表不完整（21等未印列），碼外未證實值不可逕判無效。PDF支持死亡欄24小時候選解釋，CSV映射及2–30日追蹤／彙整仍待證，兩死亡欄維持分列。
- A九候選特徵已列中英文定義、端點、分子／有效分母、缺失、跨年限制及敏感度；尚非最終分群特徵。時間／週末分母為22,368／22,762，位置與型態22,359／22,750，多人受傷22,367／22,761。C六候選均保留有效N與缺失N；部分已知人數和不是完整總量。
- 20條規則有明確條件及逐年受影響數，均未正式套用清理。除了已確認第一當事人口徑，異常值處理只在記憶體標記／試算；新增R20傷亡條件式疑點：第一當事人程度碼5但2–30日死亡人數為0，有6／4筆，保留兩欄原值待查更新／追蹤口徑。全欄完整案例會令2024歸零，已明列不採用。Sample Flow為獨立有效條件，不是逐步排除漏斗，也不把可解析座標當作已歸里。
- CRS證據：[市府事故頁](https://data.taipei/dataset/detail?id=2f238b4f-1b27-4085-93e9-d684ef0e2735)、[data.gov.tw同資料集](https://data.gov.tw/dataset/130110)與官方表單（本次查閱2026-11-26）未提供足以認證此批datum的說明。X約121、Y約25只支持角度形式；EPSG:4326為未確認工作候選，不能排除EPSG:3824等，未set_crs／轉換／Spatial Join。
- 原Unit 1.1待審清單之速限0／502、年齡負值／0／高齡、照明及multi_injury，已由本次Unit 1.2明確決策更新，見下方審查表；不再將這些處理原則列為未決。官方定義、年齡有效分母、fatal_accident_ratio時間窗及後續低樣本／平滑／最終特徵仍待驗證；本次不重新執行事故分析。
- 後續仍需官方事件／發布口徑、死亡欄生成與追蹤（含R20的6／4筆條件式不一致）、照明／完整碼表及座標基準來源；Chapter 1里界／人口／都市計畫驗證依後續授權進行。原Unit 1.1完成當時未開始Unit 1.2；後續本單元里界驗證見下方。正式資料清理、事故歸里及研究模型仍未執行。

### Unit 1.1 Review Decisions — confirmed in Unit 1.2, 2026-11-26

以下為學生本次明確提供的已通過審查決策；是後續研究規則／候選規格，不代表清理、敏感度或分群已實際執行。Unit 1.1 Notebook保持原樣，其原「待審」狀態由此表銜接。

| Item | 審查決策及適用限制 |
| --- | --- |
| 觀察單位與缺失 | 第一當事人繼續作主要事故觀察單位；不採全欄完整案例刪除。保留45,130候選，非GIS後最終樣本。 |
| 速限0／502 | 保留原值及異常標記；定義未確認前不納主要平均速限統計，不因此刪掉整起事故。 |
| 年齡 | 負值不納有效年齡統計；0歲及超過100歲保留，等待定義確認及敏感度分析，不自行補值或刪事故。 |
| R20 | 2024／2025的6／4筆疑點保留原欄，不自行填補或刪除。 |
| 死亡欄 | 24小時候選欄及2–30日欄保持分列；後續原欄描述與排除R20的敏感度分析並行，發布口徑仍待證。 |
| 照明 | 暫不納主要分群；跨年定義與碼表仍待驗證。 |
| 多人受傷及特徵規格 | `multi_injury_ratio`保留候選；後續比較八個事故型態特徵（早尖峰、晚尖峰、深夜、週末、路口附近、追撞、側撞、人車碰撞）與加入多人受傷比例的九特徵規格，並注意傷亡profile非獨立驗證。 |

### Unit 1.2 Village Boundary Validation Handoff — 2026-11-26

- 文件索引：[行政里界驗證Notebook](data/code/taipei_village_boundary_validation.ipynb)；§1來源／歷史，§2 CRS／屬性，§3個別幾何，§4正面積交集，§5聯集／孔洞，§6面積，§7合成配對，§8事故datum後續，§9七張品質診斷圖，§10限制／交接。依教師data-processing範本保留README欄位；驗證表均在文件內，未登記成正式資料集。
- 五個原始配套hash與Unit 0.5一致；兩份既有銜接Notebook也綁定hash且未執行／修改。新文件11個code cells以.venv Python 3.12.2、乾淨dssi-urban-crash kernel完整執行，保存所有表、七張圖及八種合成情境斷言。暫存程式、執行檔及供目視核對的圖片位於Git忽略的data/temp/unit12_validation/，Notebook內嵌圖片可獨立檢閱。
- 官方[里界資料頁](https://data.taipei/dataset/detail?id=6b17b31d-4e16-495e-95b1-9fd1f47c80d8)為民政局公務GIS參考圖，收錄期間2010-08-17至2025-06-17，資源更新2026-09-21；本機DBF header僅記最後寫入2026-09-16。官方[年末統計表](https://www-ws.gov.taipei/001/Upload/367/relfile/48245/8011552/77090739-2147-45bc-9e12-03b5c5b7f6e8.pdf)顯示2024、2025年底各456里／12區，未提供兩年度全套名稱代碼或幾何。未取得完整異動清冊及相容歷史向量，不能宣稱無合併／更名／邊界微調；未下載額外圖資。
- 拓樸詳表保留157組每組面積／位置、335孔洞及27個bbox大小篩查標記。正常共享線1,034對、點接觸189對；包含與空間等價重複0。正面積門檻敏感度：>0為157對、>1e-8為124、>1e-6為17、>1e-4為10、>0.001為6、>0.01／0.1／1均1、>10為0（單位m²）；未採任何門檻當作修復規則。各里原幾何面積和減聯集為1.161745m²；聯集僅1個連續Polygon，孔洞成因未知，未填洞。
- 原AREA定義／單位／更新算法未獲證實。僅在暫視可與m²對照的假設下計算數值差：60里>1%、17里>5%、10里>10%；最大相對差南港東明34.2009%，最大絕對差南港新光164,708.48數值單位；逐里絕對差合計1,817,551.26但正負差合計僅126.24，不能以全市總量接近認證逐里。行政區合計已列文件；市界外部覆蓋缺版本相容的獨立幾何，統計土地面積271.7997km²不能替代獨立市界測試。
- 原Unit 1.2面積建議（已於Unit 1.3獲學生採用）：歸里與密度分母皆用同一hash原幾何在EPSG:3826的`geometry.area / 1e6`，原AREA保留供稽核；人口須另解歷史地理／代碼對照。事故每km²為空間密度，非設籍人口或交通暴露風險。固定快照現為已確認研究單位，仍不等於證實2024–2025原生邊界相同。
- 合成測試比較within／intersects／covered_by，涵蓋內部、共同邊、共同頂點、界外、重疊內、重疊邊界混合、缺失、不可解析。候選政策：只有within及covered_by皆唯一且同里才列明確內部；邊界／多重候選保留集合，有座標未配對與缺失／解析失敗分列，不取第一筆、不任意最近里或設定距離門檻；政策未用於真實事故。
- 事故datum沿用Unit 1.1未知，本次未取得新增官方定義。後續可經授權比較4326／3824假設轉3826的位置與配對敏感度，記錄operation、accuracy、grid／ballpark及軸序；預設null／近似轉換結果相同不能證明datum，不能反推指定正式CRS。
- 本單元只更新PROJECT.md及新增驗證Notebook；原始資料、舊文件／成果、教師規範均保留。未建立修復後Shapefile、processed、人口crosswalk、真實事故歸里或都市計畫疊合，未分群／推論。原Unit 1.2完成後依序等待審查；本次Unit 1.3已確認通過並完成下方人口驗證。正式歸里仍須datum、歷史對齊、多重／未匹配政策及實際敏感度驗證，並未由crosswalk完成取代。

### Unit 1.2 Review Decisions — confirmed in Unit 1.3, 2026-11-26

以下十項沿用學生本次明確決策；接受研究地理單位不等於完成事故歸里或證實歷史邊界相同。

| Decision | 已確認內容 |
| --- | --- |
| 1–3 固定地理單位 | 採現有456里作2024–2025固定研究單位；不宣稱與兩年歷史幾何完全一致，保留歷史適用及人口空間錯配限制。 |
| 4 原geometry | 原始geometry保留，不修復、不消除重疊、不填補孔洞。 |
| 5–6 面積分母 | 密度統一採EPSG:3826的geometry.area（換算km²）；原AREA保留稽核，不作主要密度分母。 |
| 7–8 事故配對狀態 | 共同邊界、重疊區及無法配對分別保留標記；不任意最近里指派，不取第一筆處理多重配對。 |
| 9–10 事故CRS與後續 | datum仍未確認，EPSG:4326只是候選；後續須實際事故配對及候選CRS敏感度驗證。本單元未執行。 |

### Unit 1.3 Population Validation and Crosswalk Handoff — 2026-11-26

本節保留當時驗證及試算；其中糖廍待審／主要密度NA／資格限制已被下方Unit 1.4最新Revision取代。舊Notebook及crosswalk未改寫或重跑，後續不得將provisional當作排除規則。

- 文件／資料：[人口驗證及crosswalk處理](data/code/taipei_population_validation.ipynb)、[456×11對照表](data/processed/village_crosswalk.csv)、[獨立processed說明](data/processed/village_crosswalk_documentation.ipynb)、[新增官方碼表來源說明](data/raw/unit13_official_code_evidence_documentation.ipynb)與[原始回應證據包](data/raw/unit13_official_code_evidence.zip)。三份新文件按教師範本以三個乾淨kernel實際執行4＋8＋5＝17個code cells；不覆寫／重跑既有文件，不另建年度人口表或HTML。
- 來源／版本：官方[代碼目錄168](https://www.ris.gov.tw/documents/html/5/1/168.html)、[現行索引167](https://www.ris.gov.tw/documents/html/5/1/167.html)、[歷史索引558](https://www.ris.gov.tw/documents/html/5/1/558.html)、RSCD0103及11109／11406／11409／11411／11509的VillageUTF8，共9個原始回應以原bytes封裝於新增ZIP，包內manifest保存精確網址、版本、取得UTC時間、逐檔hash及HTTP欄位；ZIP為本地保存容器，不冒稱政府發布ZIP。完整來源hash固定在Notebook中，離線執行不依賴暫存下載檔或即時網頁。
- 研究人口實測32,832列、計10,944列、24月份各456里，必要數值無缺失／非數值／負值，101年齡和與總人口、男＋女與計均一致；年月里碼性別唯一。兩年456碼集合一致，同碼未觀測名稱變更。官方五快照臺北456里碼／名相同；不是逐月異動清冊，不能由此認證歷史幾何未變。
- 代碼分層：RSCD0103官方名稱為省市縣市鄉鎮市區代碼、X(08)。官方村里表的11碼村里碼與8碼所屬區碼實際核對為8＋3；本機CPTVID為7碼CPTID＋3碼里尾碼，CPID為5碼的層級關係經逐列驗證，但未取得官方10碼編碼／跨碼轉換規格。以12區名稱建立區碼橋接後，455個精確配對里全部符合尾三碼規律，不作任意截碼／補零或全臺通用規則。
- 對照表一里一列，village_id＝CPTVID；population_code、boundary_code、village_id均唯一字串，原始兩端里名完整保留。455 verified_exact_match（99.7807%）、1 provisional_match（0.2193%）、verified_official及unmatched均0；候選覆蓋456／456，一對一、無跨區錯配或漏里。名稱精確配對不稱官方跨碼認證。
- 糖廍里：人口原名糖?里63000070015；里界原名糖蔀里6300700015。五版本官方村里表均列63000070015／63000070／糖廍里，支持人口碼及正式名稱；但尚缺官方CPTVID對照／里界誤植更正依據，因此只列高可信provisional_match。該證據狀態原樣保留；最新Revision已接受糖廍里與其他455里同規則納入，無須額外敏感度或繼續查碼。
- B1年度規則：只用「計」；年度平均人口＝12個月總人口和／12；高齡65+（含100歲以上）、兒童0–14比例各為12月該組人口和／12月總人口和。兩年合併改用24月平均及24月分子／分母，不直接平均年度比例。密度分母固定為同一原geometry在3826下的km²面積，AREA只供稽核。缺月、缺人口、零比率分母不補零；月人口和不解釋為實際人口總量。
- 補充候選可由原欄建立：working_age_population_ratio（15–64，與兒童高齡和為1）、oldest_old_population_ratio（80+或85+待選）、aging_index（高齡／兒童×100）、dependency_ratio〔（兒童＋高齡）／工作年齡×100〕、female_population_ratio（同月女／計）、population_change_rate（年度平均間變化或12月間變化須另定）。分母0則NA，年齡結構有代數依存；補充項不預設主分群，也不把設籍人口當通勤／事故／暴露人口。
- 記憶體試算：年度912列、合併456列，鍵唯一，比例0–1、平均介於月最小最大，逐年重組與24月直接計算的平均／年齡比例／密度一致，幾何面積皆正值。缺月及零分母反例測試通過。配對前後計人口10,944列不增不減；455已驗證配對覆蓋10,920月列／910年列，糖廍里24月列／2年列保留待審。候選密度另作診斷，主要密度2列NA是政策待審而非人口缺失；未正式輸出任何年度人口資料。
- 原後續限制（糖廍分析資格已由最新Revision解除）：保留固定地理／歷史人口空間錯配及里界拓樸限制；精確月內統計基準日與年齡計算細則仍待來源。事故datum、實際事故配對及敏感度、都市計畫CRS／幾何／分類仍未完成。現有Unit 0.5及1.1／1.2文件按原版本保留，不以新索引冒稱已改寫其舊待辦；人口採用決策現以下方Unit 1.4 Revision為準；Unit 1.3完成當時未開始1.4，本次1.4結果另列於下方。

### Unit 1.3 Review Decisions — Latest Revision Applied in Unit 1.4, 2026-11-26

- Unit 1.3審查通過，crosswalk維持456里、455 verified_exact_match＋糖廍里1 provisional_match；證據狀態不升級official。
- 學生根據五版本官方歷史人口碼、萬華區、455里代碼規律及一對一證據，接受63000070015↔6300700015；標準名稱糖廍里，原糖?里／糖蔀里及原始檔案不改。
- 糖廍里直接納主要人口、都市環境及後續整合，與其餘455里同規則；不另作排除糖廍里的敏感度、不再查碼，provisional不構成資格障礙，後續不得僅因此將人口密度或其他人口特徵設NA。此Revision取代附件舊敏感度要求及先前相反設定，不重跑Unit 1.3。
- 舊Unit 1.3程式中的integration_allowed及兩列NA僅是當時記憶體試算，後續新處理必須依456里全納入決策實作，不能直接沿用舊狀態閘門；本次不改舊Notebook／crosswalk或重新計人口。
- B1仍為密度、65+、0–14三主要候選；年度12月平均存量及加總分子／分母比例，合併24月重算，其他人口變數僅補充；事故分群資格不受名稱差異影響。

### Unit 1.4 Urban Planning Source and CRS Handoff — 2026-11-26

以下保留Unit 1.4完成當時的證據與待審狀態；面層工作假設及固定快照已由學生於Unit 1.5接受，現行決策與結果見下節，舊Notebook未改寫。

- 文件索引：[正式驗證Notebook](data/code/taipei_urban_planning_crs_validation.ipynb)、[來源證據說明](data/raw/unit14_urban_planning_evidence_documentation.ipynb)及[證據ZIP](data/raw/unit14_urban_planning_evidence.zip)。兩份新文件從乾淨dssi-urban-crash kernel、.venv Python 3.12.2執行11＋4＝15個code cells，保存完整表及四張品質診斷圖；不重跑既有Notebook。
- 新包保存12個官方原始回應：指定資料頁、主細計原ZIP、GIS入口回應、服務／面／點metadata、少量具名特徵查詢及筆數、官方主細計層級與通檢說明；manifest含URL、取得時間、版本、大小及hash。未成功取得的中央手冊／點控制請求另留失敗紀錄，不充作證據。外層ZIP是本地保存容器，原始回應bytes未更動；Notebook離線重現，不依賴暫存下載。
- 來源／版本：[官方頁](https://data.taipei/dataset/detail?id=3bab0a01-7936-4218-8cb5-f74dfcb43dda)為都發局臺北市都市計畫使用分區圖，內容標示2025-01，細計資源更新2026-04-09 11:49:14、主計11:49:21。本機六個細計SHP／SHX／DBF與本次官方同名配套逐bytes／SHA相同，獨立讀取的全屬性、schema、WKB及bounds一致，來源身分A；DBF header寫入2026-04-09，非計畫生效日。兩官方ZIP均無PRJ／CPG／XML／README。
- CRS直接證據限服務：[UrbanPlan2圖層2 metadata](https://uptilev.gov.taipei/arcgis/rest/services/UrbanPlan2/UrbanPlan2/MapServer/2?f=pjson)及點層0來源sourceSpatialReference為3826，服務顯示參考為3857。服務面15,511筆與下載15,518及欄位不同，不能聲稱全檔同版，outSR=3826亦非原CRS證明。同編號樣本指向不同分區／形狀，不能當跨版穩定ID。
- 以相同分區代碼／使用分區、頂點數及完整邊長序列辨識5個官方面樣本，其中3個取得唯一共同輪廓（官方編號100／5000／10000對本機103／4253／8863），另2個保留無對應，未用最近距離或同ID強配。邊長數值容差1e-6m附1e-8至1e-5敏感度，非地面精度或距離門檻。3826假設下Hausdorff約9.76e-10至2.79e-9m，3828約854.033693m；數值貼合不解釋成測量精度。
- 合理候選僅3826（TWD97／TM2 zone121）及3828（TWD67／TM2 zone121），PyProj核對datum／投影／參數／軸序／範圍。當前3826→3826為noop、accuracy0；3828→3826為資料庫operation的affine xoff828.589、yoff−206.915，accuracy7m，無不可用operation，PROJ_NETWORK關閉、不下載grid。這是所選資料庫轉換，不是任意平移以吻合圖面；完整operation／grid紀錄在Notebook。
- 證據分級：細計面 **B Strongly supported working CRS**，3826為有共同輪廓支持的工作候選；仍缺下載檔專屬投影定義／提供機關版本聲明，不能列A。細計點註記 **C Ambiguous CRS**，同包及服務支持3826候選但未建立3點的獨立共同控制，不能由面控制外推正式認證。原始兩層CRS=None、WKB不變，候選只在記憶體副本測試，未指定正式CRS。
- 原始面頂點417,971、點3，無非有限坐標；面bounds約X294,770.79–319,674.63、Y2,759,513.05–2,790,592.10，坐標量級及里界3826只作旁證。原數值小數對齊比例及97種原圖層bbox已列出，不作測量精度認證、面積或正式分區分類。
- 時間／替代方案：未找到研究兩年度各一份全市細計歷史SHP；計畫生效日與本機原下載日期仍未知，只能提出固定時點環境快照候選，保留2024事後／2025年內變動或後續修訂的時間錯配，不作事前環境、無時間洩漏預測或因果證據。主計面3,840（3,796 Polygon＋44 MultiPolygon）、點3,824，亦無PRJ，沒有較完整CRS優勢；規劃層級與管制內容不同，不直接取代／混算細計。
- Unit 1.5交接：保留Unit 0.5的143無效面、5組11列相同WKB、97原圖層／260分區碼、4使用分區空白及計畫／規劃範圍，部分重疊／覆蓋仍待檢查。官方GIS欄位及分區簡稱renderer有221個符號值，可作查證線索但非完整分類碼表；先取得／審查正式分類與範圍定義，不直接作B2。建議繼續現有細計面，若後續涉及投影後處理／面積／疊合，須學生採用3826工作假設與固定快照限制；本單元未修復、刪重、分類、算面積或Overlay。
- 若暫停B2，D原版仍可保留事故分群及B1人口比較，但環境解釋縮減；D改良版須重評環境特徵充分性。完成本單元後停止，等待學生審查，未開始Unit 1.5。

### Unit 1.5 Geometry and Zoning Validation Handoff — 2026-11-26

以下保留Unit 1.5完成時之結果與待審紀錄；學生於Unit 1.6已接受linework優先、原分類架構與方案B，現行個別例外／覆蓋診斷見Unit 1.6，新舊Notebook不回溯改寫。

- 接受Unit 1.4：續用細計面、記憶體EPSG:3826、B級證據、固定快照及歷史生效限制；不補PRJ、不換主計、不處理細計-文。糖廍里與其他455里同規則，不改provisional、不設資格NA、不重跑1.3。
- [幾何／分類驗證](data/code/taipei_urban_planning_geometry_validation.ipynb)12個code cells、[獨立crosswalk說明](data/processed/urban_zoning_crosswalk_documentation.ipynb)5個、[新官方證據說明](data/raw/unit15_zoning_classification_evidence_documentation.ipynb)4個，均乾淨DSSI Urban Crash kernel實際執行，保留21個code cells及六圖；不產出HTML、修復GIS或逐里Overlay／B2。
- 143無效：Self-intersection 67、Ring Self-intersection 52、Hole lies outside shell 15、Nested shells 9。僅無效筆試算linework／structure／buffer(0)。三法均有效，但後兩法各15空幾何；linework無空面、68筆GeometryCollection含80非面構件、195面components及51個小於1m²碎面。原始面積不是真值；linework面積總改變8.602910km²僅診斷，不能稱修復誤差。全部143筆穩定來源ID／原屬性／原因／bounds／方法差異／非面構件摘要留表，93高優先、50一般，需人審；建議linework作診斷起點，尚未批准正式採用。
- 原始WKB5組11列：1組三筆範圍要素（1／2／3），4組同類同主要屬性但單筆編號不同（13259／13261、14497／14498、14542／14562、15192／15194）。沒有刪列；同類union可避免面積重複。索引空間等價8對，其中新增非相同WKB為14450（圖層5／R3／第三種住宅區）對14454（圖層32／PEA／公園用地），兩原始幾何均有效，約0.000082291m²，屬C跨類衝突，不因極小自行刪除；完整比較見Notebook。
- 97原圖層、260碼完整檢閱；單碼不足以保留名稱／描述／簡稱差異，建立[urban_zoning_crosswalk.csv](data/processed/urban_zoning_crosswalk.csv)296組五欄複合鍵、12欄，對應15518原始列。18鍵8468列official_supported、275鍵7046列research_classification、1鍵1列ambiguous、2鍵3列excluded_non_zoning。資格為15514已分類eligible、3範圍、1待確認；55鍵540列mixed_special_use獨立保留，不逕併住商工。
- 三範圍原列＝圖層368細部計畫範圍1筆＋370規劃範圍2筆，只排除於分區面積用途。第四筆名稱空白「陽明山公園」圖層295／原編號2221，不因空白排除，不擅自當綠地，保留ambiguous_layer／unclassified。
- 新[官方分類證據包](data/raw/unit15_zoning_classification_evidence.zip)：法規FL003962現行114-07-09、歷史112-08-04及都發局專有名詞三件原回應，manifest載URL／版本／取得時間／bytes／SHA-256；歷史member名.html實為PDF，依Content-Type與magic讀取，不改bytes。法規第3條支持大類語義、都發局解釋支持公設研究合併；不證明全部本機代碼或個案計畫生效，不當完整碼表。renderer仍僅參考。住宅／商業(特)按明示母類作研究寬類，文教、IF產業服務及B指定用途等邊界歸類待學生審查。
- STRtree僅56,584對相交候選，避免120,396,403全組合。含範圍正面積48,554對；排除範圍後2,006對＝716同類＋1,272跨類＋18待確認對已分類，另共享線6,862對、點接觸1,168對。排除範圍後pairwise面積總22,640.679861m²，不是唯一重疊面積。大於0.01／1／10／100m²為813／320／25／4對，僅容差敏感度，不自動刪微片；全部組合、分位數及主要來源列見Notebook。
- 全市記憶體診斷（linework面構件參考，不是正式分區成果）：固定里聯集268.550083km²；已分類eligible覆蓋195.753924km²＝72.8929%；含待確認候選覆蓋243.679422km²＝90.7389%；未知面47.925545km²，其中未知獨占47.925497km²；全候選未覆蓋24.870661km²＝9.2611%。跨已分類唯一重疊909.784619m²，另已分類與未知重疊47.791979m²，集合可能交疊不可直接相加。候選超出固定研究區5.661111km²（已分類5.540911km²）。不推論未覆蓋處沒有任何分區。
- 面積規則建議待審：同類先union；方案A需官方逐案優先序，本次沒有，故不擅採。推薦B將跨類聯集及已分類對未知交集保留待確認，從各類有效分子扣除；方案C明示為非互斥覆蓋，可合計超100%。不任意指定類別優先或重新正規化成100%。非面構件獨立報告，不能靜默捨棄。
- 五主候選均有原始分區可定義，但未形成正式逐里值。分母固定原里面積，分子經審查規則處理的類別有效面交里；品質指標zoning_coverage_ratio、unclassified_area_ratio、unresolved_overlap_ratio、uncovered_area_ratio獨立報告，不當主要環境分群特徵。未知／未覆蓋／低品質不補零；NA粒度與覆蓋門檻待審，不自訂。交通／農保／其他公設僅補充候選；分區不等於實際使用、綠覆、道路長度或交通暴露。
- Unit 1.6條件：本單元本地驗證及文件已完成，但正式B2尚未無條件具備456里可比性。學生須先審修復／分類／重疊與覆蓋規則，決定未知處理與可接受品質，並另確認整合依賴；本次完成後停止，等待學生確認，不自動開始Unit 1.6。原始六細計配套、五里界配套、人口crosswalk及舊Notebook均保留原bytes，Git寫入由學生自行操作。

### Unit 1.6 Integration Readiness Handoff — 2026-11-26

- [主要整合審查Notebook](data/code/taipei_data_integration_readiness.ipynb)使用教師data/code範本與固定22項輸入hash，乾淨DSSI Urban Crash kernel完整執行15個code cells、六張實際診斷圖；未重跑舊Notebook、未輸出正式資料集。來源、兩crosswalk與舊成果維持原bytes。原有24筆Data Artifacts保留，不把診斷Notebook假登錄為正式資料集。
- 職務已永久確認：PM曾翊涵、DE謝子詮、DA詹明翰；本Unit DE主責、DA協作、PM審查。依學生明確回覆，目前僅Codex協助執行，成員驗收與審查尚待完成；共同作者與主要負責人不同，不追溯改作者／歷史貢獻，不推定人工審查已完成。
- 事故CRS：PyProj本機EPSG定義確認4326=WGS84、3824=TWD97 geographic、3826=TWD97/TM2 121；X=經度、Y=緯度，always_xy。4326→3826含inverse TWD97 to WGS84(1)，operation accuracy 1m；3824投影accuracy=-1未知；兩者均無ballpark、無所需grid或不可用operation，數值pipeline相同，兩年所有位置差分位數及最大值皆0m、行政里／狀態差0。故無法辨識原datum，建議4326僅作明示工作慣例、3824保留替代，不作官方來源認證或以配對率判定。
- 真實候選事故2024／2025為22368／22762，可解析22367／22760；各CRS下within與covered_by同里且唯一22351／22732，占全部99.9240%／99.8682%、占可解析99.9285%／99.8770%；界外或孔洞16／28、缺或不可解析1／2，其餘共享邊界／頂點／正面積重疊／其他多重及單一邊界皆0。四份audit共90260列只表示兩種候選的診斷複本，原候選仍45130筆，全部ID可追溯且互斥完整，未輸出正式歸里。
- 區名：原區序含明示名稱，但正式數字碼規格仍未知，不直接轉CPTID；以原字串區名比TNAME。唯一配對中一致21920／22294、不一致431／438、來源未知0／0；地址開頭無法判讀85／67筆。區名不一致距原始區域≤100m為320／327，>100m各111筆，最大6.410／5.317km；多數地址支持原區名（415／425），不能全部解釋為邊界捨入，遠距例外與可能座標／地址／版本問題留表，不指定最近里。非唯一空間例外另按區／時／型態列完整分布，未作統計推論。
- 歸里候選政策待審：A幾何唯一同里，且不帶區名／明確地址衝突者可先列保守候選21920／22292；其餘幾何唯一仍保留原結果及衝突旗標，不直接刪原事故。B多重候選需可信非空間資訊唯一排除，另標輔助待審；本次沒有多重實例，不能宣稱已驗證B效果。C未解邊界／重疊留待確認；D界外／孔洞／缺座標保留、不納尚無法確認的里統計。不取第一筆、不任意最近指派。2025有1里明確觀測事故數0，但不能由此保證真實全年無事故或將來源缺失補0。
- 都市計畫：143筆優先93高優先均逐筆檢查，linework面有效且正面積；三法面差≤10⁻⁶m²且非空者105筆列算法一致候選，38方法敏感待確認，其中21筆涉及主B2類別。這是浮點／算法一致性條件，非人工或官方正確性認證；原有效面不修復。保留非面構件及微碎片稽核。38筆三方法候選包絡在市研究區20.827694km²，供保守扣除，不保證真實誤差只限包絡。
- 分類：296鍵／13類及CSV不變；IF2筆39016.529m²、B指定展會1筆33594.480m²提出改mixed_special_use待審，診斷暫扣3筆分類待審面，未直接修訂crosswalk。其他B指定用途維持商業母類，C84筆文教維持文教學校寬類（非實際校園人流），540筆混合特殊為已知分類，不一律當未知。陽明山公園仍unclassified。
- 全市47.925545km²未分類面完全來自陽明山公園一筆，分布北投約27.469549、士林20.455996km²。方案B扣正面積跨類／未知交集957.577118m²，線／點接觸另留稽核不混入面積扣除；另保守扣方法敏感包絡與分類待審。候選覆蓋243.679422km²、已分類195.753924、有效174.854933，其中五主類73.143556、已知非五主類101.711378；未覆蓋24.870661、總不確定聯集93.695150km²。各品質集合可能相交，不相加；原里面積不改。
- 456里有效覆蓋率平均75.5839%、中位76.2057%、Q1／Q3為69.3985%／84.3513%，範圍0–99.3972%；90%以下407里，≥50／70／80／90／95／99%為441／331／162／49／16／2里。低值包含北投湖田0%、大屯0.3198%、湖山0.8060%、泉源1.3224%及士林溪山12.6513%；城市核心也有未覆蓋，不能只以山區解釋。完整456里表、407低覆蓋清單、行政區與地圖保存在Notebook診斷輸出，未選正式排除門檻。
- B2完整比例／零值政策：全部456里都有不確定範圍，故本輪沒有可認證「完整已知零」的里。住宅／商業／工業／文教／公綠觀測正下界為415／319／32／237／374里，其餘41／137／424／219／82里不能因觀測0就說指定分區不存在。L僅已辨識覆蓋或條件性下界；U=min(1,L＋不確定聯集比例)只在接受已知面正確及目前包絡涵蓋全部不確定的假設下成立，否則完整比例上界不可認證，不作信賴區間。正式完整比例不能由L直接填入；品質指標不當主要分群特徵。
- 整合測試通過：CPTVID字串456基礎、912 village-year、456合併鍵唯一，人口crosswalk一對一、24月計10944列全部銜接、年度／24月分子分母重組一致，912人口密度無缺值。糖廍2年及24月同規則計算、密度不缺、原provisional保留。B2固定快照many-to-one接入912列但不是年度獨立環境，同里兩年非獨立社區；B2不足未排除任何事故／B1架構，未保存正式整合資料。

| Dataset readiness（正式處理條件，非已產出） | Status | 限制及Chapter 2交付 |
| --- | --- | --- |
| 事故標準化 | Ready with explicit assumptions | 2.1可先做；來源ID、跨年欄位及局部分母，無官方事件ID與部分發布口徑限制保留。 |
| 事故歸里 | Ready with explicit assumptions | 2.2需學生接受工作CRS及A–D／衝突旗標政策；未解例外保留，不任意指派。 |
| 固定行政里基礎 | Ready with explicit assumptions | 2.2固定456原幾何，保留歷史及微量拓樸限制。 |
| Dataset A | Ready with explicit assumptions | 2.3依2.1／2.2後建分子、有效分母及缺失／低樣本旗標；最終分群樣本待EDA。 |
| Dataset B1 | Ready | 2.4可獨立處理，糖廍正常納入；設籍非交通暴露及固定地理限制保留。 |
| Dataset B2 | Partially ready | 2.5限經審查的觀測覆蓋／品質及條件性範圍，不冒充完整比例；不阻其他資料。 |
| Dataset C | Ready with explicit assumptions | 2.3依歸里；24h／2–30d死亡分列、傷亡缺失不補零，空間密度非事故率。 |
| 跨年度驗證架構 | Ready with explicit assumptions | 2.6保留year、同里依賴、2024擬合／2025指派及固定B2快照；未執行模型。 |

- 研究及交付優先序：先完成D原版基礎版（事故分群＋B1）；B2只在品質／目標量定義審查後補充，D改良版暫不建議啟動獨立環境分群，跨年度事故穩定性可保留，Prediction仍缺目標／時點／防洩漏設計。Chapter 2建議2.1→2.2→2.3、2.4可獨立、2.5有條件、2.6整合驗證；DE在data/交付已驗證／文件化資料，DA在finding/優先使用同版本，PM協調規範與交付審查，不以職務推定已完成工作。每Unit開始前團隊另確認Primary Owner／Collaborator／Reviewer／Deliverables，完成後記Actual Contribution。
- 本單元本地驗證完成，具附明示假設分項進Chapter 2的條件，仍待學生驗收／PM審查；未認證事故datum、全部修復或完整B2，未將Chapter 1所有資料無條件通過。完成後停止，不自動進Chapter 2；Git提交由實際成員依教師規範操作。

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
| 都市計畫分區研究分類對照 | crosswalk | [urban_zoning_crosswalk.csv](data/processed/urban_zoning_crosswalk.csv) | [獨立資料說明](data/processed/urban_zoning_crosswalk_documentation.ipynb) | [幾何／分類驗證](data/code/taipei_urban_planning_geometry_validation.ipynb) | 2026-11-26 Unit 1.5：UTF-8-SIG、296×12；圖層／碼／名／說明／簡稱五欄唯一，260碼、15518原列many-to-one完整覆蓋，保存CSV獨立讀回一致。18鍵official_supported、275研究歸類、1待確認、2範圍排除；55鍵540列特專混合獨立保留。結構已驗證，正式修復／B2面積及低品質規則待審，非逐里資料。 | `4326d92d1567167ca67c13dc1c083426bf6d4d789b88ed5da1feec422306383f` |
| 都市計畫分類官方原始證據包 | raw | [ZIP](data/raw/unit15_zoning_classification_evidence.zip) | [來源說明](data/raw/unit15_zoning_classification_evidence_documentation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.5：三官方原始回應＋manifest，逐件URL／時間／版本／bytes／hash核對；112-08-04歷史PDF74頁及現行114-07-09條例、都發局名詞。歷史member名.html實為application/pdf，以magic讀取，原bytes保留。本地容器不是官方發布ZIP；分類語義證據非260碼完整認證或個案有效期證明。 | `82effe1535fc7577d73accf81ee0663daa78944a11517b9e50c7bc2e197ba9b9` |
| 都市計畫官方來源及CRS查證原始證據包 | raw | [ZIP](data/raw/unit14_urban_planning_evidence.zip) | [來源說明Notebook](data/raw/unit14_urban_planning_evidence_documentation.ipynb)；[來源／CRS驗證](data/code/taipei_urban_planning_crs_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.4：12個官方原始回應與manifest／失敗紀錄；主細計ZIP各6配套均無PRJ，六本機細計檔與官方同bytes。服務來源3826／顯示3857及3個共同面控制支持面B級工作候選，點C級；不是正式processed圖資或A級本機CRS認證。逐回應URL、取得時間、版本、大小及hash保存在包內，外ZIP為本地保存容器。 | `695e15f7230c076b2b827f72b4337273ff795f6fc7e9c52680641c972dd72730` |
| 戶政司官方代碼查證原始回應證據包 | raw | [ZIP](data/raw/unit13_official_code_evidence.zip) | [來源說明Notebook](data/raw/unit13_official_code_evidence_documentation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.3：9份官方原始回應與包內manifest；來源／版本／取得時間／逐檔hash齊備，5個村里快照臺北皆456里且碼／名相同，RSCD0103以CP950讀取。現行與歷史快照不認證歷史幾何；本地封裝非政府原ZIP。 | `9f27bd2f9211f4c21253876529efec1414b82f0b7014f6d4028b70f66b58cc40` |
| 臺北市固定研究行政里代碼對照 | crosswalk | [village_crosswalk.csv](data/processed/village_crosswalk.csv) | [資料說明Notebook](data/processed/village_crosswalk_documentation.ipynb) | [人口驗證與處理](data/code/taipei_population_validation.ipynb) | 2026-11-26 Unit 1.3：UTF-8-SIG、456×11、全欄字串，磁碟讀回一致；三鍵唯一、一對一無跨區／漏里，455 verified_exact_match、1 provisional_match（糖廍）；verified_official與unmatched皆0。證據狀態按原表保留；Unit 1.4 Revision已接受糖廍里，456里同規則納主要分析，provisional不得作排除／設NA原因，不需糖廍排除敏感度或再查碼；本CSV未修改、非年度人口表。 | `dd9e762419c302cf5b4bb19daad2673d7d54d0bb750204e7e33ecbf1a9983f69` |
| 臺北市 114 年死傷交通事故明細 | raw | [CSV](data/raw/114年-臺北市死傷交通事故明細.csv) | [2024–2025 新研究原始說明](data/raw/taipei_2024_2025_crashes_raw_documentation.ipynb)；[歷史文件（缺失／pending）](data/raw/taipei_2025_casualty_crashes_documentation.ipynb)；[事故對照表](data/raw/事故對照表.pdf)；[Unit 1.1 驗證及候選定義](data/code/taipei_2024_2025_crash_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.1：hash與0.5一致；第一當事人22,762；候選鍵及完整列無重複；型態／位置有效22,750、受傷數22,761；速限0為315、502為0。候選規則未正式清理。保留前次紀錄：2026-11-25：重新計算本機 SHA-256，UTF-8-SIG、22,762×47、全為第一當事人，候選鍵與完整列無重複、2 筆候選紀錄缺座標；已執行新 raw 文件，CRS／官方事件及跨年映射待驗證。歷史驗證紀錄保留：2026-09-29：已核對 UTF-8 with BOM、22,762 列、47 欄、民國 114 年 1–12 月、0 筆完整列重複、欄位缺失、候選事故鍵及主要代碼分布；另已核對 4 頁事故對照表（SHA-256：`f40ded1ded1c816a38f421bc972cdc1320bbd280e647792207ec037d05fd3670`）。夜間規則後續已確認為臺北市當日日落後至隔日日出前，固定 18:00–06:00 作敏感度分析，但尚未實際計算與驗證；觀察單位、事故唯一鍵、重傷所需的其他資料來源或辨識方式、路口彙整仍 pending。 | `61f0bdb52a49176746ab8b66926224b294498c9e26b2dec6eefe44906fdffa0c` |
| 各里人口年齡原始統計 | raw | [112迄今各里人口數按年齡分.csv](data/raw/112迄今各里人口數按年齡分.csv) | [原始資料說明](data/raw/taipei_population_age_raw_documentation.ipynb)；[Unit 1.3驗證／crosswalk](data/code/taipei_population_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.3：hash與0.5一致；研究24月32,832列／計10,944列，數值／年齡加總／性別／唯一鍵／代碼及名稱穩定檢查通過；455精確配對＋1糖廍暫定；年度912列只在記憶體試算，未正式輸出。保留前次紀錄：2026-11-25：CP950、64,722×107、112年1月–115年10月；研究24個月各456里，101年齡組加總及男＋女一致，無缺失／負值／鍵重複；455／456精確名稱配對，正式碼表及月基準待驗證。未建立年度人口表。 | `a663a4f0329b18bb0514da7fd9f6845312d08fadef71e566faf1930c03541641` |
| 臺北市 113 年死傷交通事故原始明細 | raw | [113年-臺北市死傷交通事故明細.csv](data/raw/113年-臺北市死傷交通事故明細.csv) | [原始資料說明](data/raw/taipei_2024_2025_crashes_raw_documentation.ipynb)；[Unit 1.1 驗證及候選定義](data/code/taipei_2024_2025_crash_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.1：hash與0.5一致；第一當事人22,368，groupby含缺失鍵、候選群及場景一致性／重複檢查完成；型態／位置有效22,359，受傷數22,367；速限0為328、502為1。候選規則未正式清理。保留前次紀錄：2026-11-25：UTF-8-SIG、51,810×49；第一當事人 22,368，候選時地群各恰一筆；完整列與第一當事人候選鍵無重複，1 筆候選紀錄缺座標。傷亡／速限／年齡／CRS 等限制見已執行文件；非正式事故表。 | `b6ad23f05658531998f34ba4995a190d03872940ea48013115da89bb2a4e92c5` |
| 臺北市行政里界圖資配套 CPG | raw | [G97_A_CAVLGE_P.cpg](data/raw/G97_A_CAVLGE_P.cpg) | [原始資料說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb)；[Unit 1.2驗證](data/code/taipei_village_boundary_validation.ipynb)；[Unit 1.3人口碼對照](data/code/taipei_population_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.2：hash與0.5一致；UTF-8宣告與實際讀取一致；區里名無空白，名稱歷史等價及人口crosswalk仍待證。 保留前次紀錄：2026-11-25：文字編碼宣告：UTF-8；本機里名糖蔀里仍保留，正式名稱／碼表待驗證。 五個配套檔均逐檔hash並綁定於已執行文件。 | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` |
| 臺北市行政里界圖資配套 DBF | raw | [G97_A_CAVLGE_P.dbf](data/raw/G97_A_CAVLGE_P.dbf) | [原始資料說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb)；[Unit 1.2驗證](data/code/taipei_village_boundary_validation.ipynb)；[Unit 1.3人口碼對照](data/code/taipei_population_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.2：hash與0.5一致；456×28屬性及全部型態已檢查，CPTVID唯一非空字串、區里組合唯一；header寫入2026-09-16不代表生效版本，AREA定義未知。 保留前次紀錄：2026-11-25：屬性表：456×28；CPTVID唯一10碼、區里名完整；AREA及其他正式碼定義待補。 五個配套檔均逐檔hash並綁定於已執行文件。 | `2f43f92e84279a45b2512cf453e9b72f706d1ad1402665c946b1a354f75d8577` |
| 臺北市行政里界圖資配套 PRJ | raw | [G97_A_CAVLGE_P.prj](data/raw/G97_A_CAVLGE_P.prj) | [原始資料說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb)；[Unit 1.2驗證](data/code/taipei_village_boundary_validation.ipynb)；[Unit 1.3人口碼對照](data/code/taipei_population_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.2：hash與0.5一致；EPSG:3826、TWD97／TM中央經線121°、Easting／Northing及公尺確認；不證明事故datum。 保留前次紀錄：2026-11-25：座標定義：本機WKT辨識EPSG:3826（TWD97、TM中央經線121°、公尺）；不證明事故或都市計畫CRS。 五個配套檔均逐檔hash並綁定於已執行文件。 | `8dac7d82ea889063f9eaa7df408fcaeb7307d32831ea973b6534d0139a4523c5` |
| 臺北市行政里界圖資配套 SHP | raw | [G97_A_CAVLGE_P.shp](data/raw/G97_A_CAVLGE_P.shp) | [原始資料說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb)；[Unit 1.2驗證](data/code/taipei_village_boundary_validation.ipynb)；[Unit 1.3人口碼對照](data/code/taipei_population_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.2：hash與0.5一致；456 Polygon個體有效；157對正面積交集、335內孔、1聯集component，面積及容差敏感度詳驗證；未修復，歷史版本與外部覆蓋仍受限。 保留前次紀錄：2026-11-25：幾何主檔：456 Polygon、12區；無缺失／空／無效／完全相同WKB幾何；年度適用性、重疊／縫隙未認證。 五個配套檔均逐檔hash並綁定於已執行文件。 | `f7fb4813a2283198ca564f5686823c454c5fd832d2f6981a2ee88a94719be3cc` |
| 臺北市行政里界圖資配套 SHX | raw | [G97_A_CAVLGE_P.shx](data/raw/G97_A_CAVLGE_P.shx) | [原始資料說明](data/raw/taipei_village_boundaries_raw_documentation.ipynb)；[Unit 1.2驗證](data/code/taipei_village_boundary_validation.ipynb)；[Unit 1.3人口碼對照](data/code/taipei_population_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.2：hash與0.5一致；同名五配套可共同讀取；空間索引與拓樸診斷已執行，未修改或重新輸出索引。 保留前次紀錄：2026-11-25：幾何索引：與同名SHP／DBF可共同讀取；不以索引可讀認證拓樸。 五個配套檔均逐檔hash並綁定於已執行文件。 | `ab7bc5e63229f676d3580b68e98db59b91a2d327c74ca23b0000ca1c568d414e` |
| 事故代碼對照表參考文件 | raw | [事故對照表.pdf](data/raw/事故對照表.pdf) | [原始資料說明](data/raw/taipei_2024_2025_crashes_raw_documentation.ipynb)；[Unit 1.1 驗證及候選定義](data/code/taipei_2024_2025_crash_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.1：hash與0.5一致；逐碼核對p.1／p.3／p.4，主要型態／位置及補充碼附來源頁；職業／部分版本碼表仍不足，CSV死亡映射與事故CRS未因此認證。保留前次紀錄：2026-11-25：PyMuPDF 讀取4頁及文字，表單印有112.07.01後適用；主要代碼及逐欄定義附於事故文件。原始下載日期／本機與官方位元組版本未認證，CSV映射及完整職業等碼表仍待補。 | `f40ded1ded1c816a38f421bc972cdc1320bbd280e647792207ec037d05fd3670` |
| 都市計畫 細計-文 DBF | raw | [細計-文.dbf](data/raw/細計-文.dbf) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)；[Unit 1.4來源／CRS驗證](data/code/taipei_urban_planning_crs_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.4：hash與0.5一致且與官方細計ZIP同名配套bytes相同；C級點註記，未建立獨立控制，均非正式CRS確認，原圖資未改。保留前次紀錄：2026-11-25：3 Point，無無效／完全相同WKB幾何；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `eba92881fc11e574f24024380c946d73cf213e86040663c4070d15b1d552a7be` |
| 都市計畫 細計-文 SHP | raw | [細計-文.shp](data/raw/細計-文.shp) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)；[Unit 1.4來源／CRS驗證](data/code/taipei_urban_planning_crs_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.4：hash與0.5一致且與官方細計ZIP同名配套bytes相同；C級點註記，未建立獨立控制，均非正式CRS確認，原圖資未改。保留前次紀錄：2026-11-25：3 Point，無無效／完全相同WKB幾何；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `fa1767fc78c69b7683ec53e0fab8937bac6c33868bedee3c3dcc2ed38dcab731` |
| 都市計畫 細計-文 SHX | raw | [細計-文.shx](data/raw/細計-文.shx) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)；[Unit 1.4來源／CRS驗證](data/code/taipei_urban_planning_crs_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.4：hash與0.5一致且與官方細計ZIP同名配套bytes相同；C級點註記，未建立獨立控制，均非正式CRS確認，原圖資未改。保留前次紀錄：2026-11-25：3 Point，無無效／完全相同WKB幾何；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `32d642964d494f49d08830f9c12857f9f4995b56eebf09ef2be994034b864760` |
| 都市計畫 細計-面 DBF | raw | [細計-面.dbf](data/raw/細計-面.dbf) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)；[Unit 1.4來源／CRS驗證](data/code/taipei_urban_planning_crs_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.4：hash與0.5一致且與官方細計ZIP同名配套bytes相同；B級面層，3826工作候選，均非正式CRS確認，原圖資未改。保留前次紀錄：2026-11-25：15,508 Polygon＋10 MultiPolygon，143無效；5組11列相同WKB；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `29b0484feef66c6c8417821ada8a28ed1edc0efcdffb492476fe7ada8739e1d4` |
| 都市計畫 細計-面 SHP | raw | [細計-面.shp](data/raw/細計-面.shp) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)；[Unit 1.4來源／CRS驗證](data/code/taipei_urban_planning_crs_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.4：hash與0.5一致且與官方細計ZIP同名配套bytes相同；B級面層，3826工作候選，均非正式CRS確認，原圖資未改。保留前次紀錄：2026-11-25：15,508 Polygon＋10 MultiPolygon，143無效；5組11列相同WKB；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `67d2ecc469383459e43f2609cf384a4129e09b27c590cbbb82dfa750eba758ee` |
| 都市計畫 細計-面 SHX | raw | [細計-面.shx](data/raw/細計-面.shx) | [原始資料說明](data/raw/taipei_urban_planning_raw_documentation.ipynb)；[Unit 1.4來源／CRS驗證](data/code/taipei_urban_planning_crs_validation.ipynb) | not applicable (source) | 2026-11-26 Unit 1.4：hash與0.5一致且與官方細計ZIP同名配套bytes相同；B級面層，3826工作候選，均非正式CRS確認，原圖資未改。保留前次紀錄：2026-11-25：15,508 Polygon＋10 MultiPolygon，143無效；5組11列相同WKB；SHP／SHX／DBF組合以CP950讀取，12屬性欄；缺PRJ／CPG、CRS=None，未指定CRS／修復／算面積／正式分類。來源版本與部分重疊待驗證；本檔hash及組合見已執行文件。 | `277e5f623c5c81865aa7288fac979a279b340899a4b3bc4335638f797fc5fd69` |
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
| 詹明翰、謝子詮、曾翊涵 | 2026-11-26 Unit 1.1：共同完成[跨年度事故驗證Notebook](data/code/taipei_2024_2025_crash_validation.ipynb)及PROJECT.md狀態／索引更新，保存11個乾淨kernel code cells實際輸出；覆蓋49列schema、官方碼表、全欄品質、座標來源、Dataset A／C候選定義、20條規則及獨立有效分母／樣本影響。未正式清理／跨年合併、歸里或建模；沿用學生明確共同作者，不推定個別分工。 | 待提交（貢獻紀錄未完成） |
| 詹明翰、謝子詮、曾翊涵 | 2026-11-26 Unit 1.2：沿用已確認共同作者，完成[里界品質驗證Notebook](data/code/taipei_village_boundary_validation.ipynb)，保存11個乾淨kernel code cells、拓樸／面積完整診斷、八種合成配對情境及七張圖；更新PROJECT.md的Unit 1.1審查決策、里界結果／限制及文件索引。未修復圖資、指定事故CRS或正式歸里，不推定個別分工。 | 待提交（貢獻紀錄未完成） |
| 詹明翰、謝子詮、曾翊涵 | 2026-11-26 Unit 1.3：沿用已確認共同作者，完成[人口驗證／crosswalk處理](data/code/taipei_population_validation.ipynb)、[crosswalk與獨立說明](data/processed/village_crosswalk_documentation.ipynb)及[新增官方碼表證據包說明](data/raw/unit13_official_code_evidence_documentation.ipynb)，三個乾淨kernel共17 code cells實際執行；驗證24月人口、455精確＋1暫定對照及記憶體年度／兩年規則，更新PROJECT.md的Unit 1.2審查決策、B1定義／限制及來源與資料索引。未輸出年度人口或進行事故歸里，不推定個別分工。 | 待提交（貢獻紀錄未完成） |
| 詹明翰、謝子詮、曾翊涵 | 2026-11-26 Unit 1.4：沿用共同作者，完成[都市計畫來源／CRS驗證](data/code/taipei_urban_planning_crs_validation.ipynb)及[官方原始證據包說明](data/raw/unit14_urban_planning_evidence_documentation.ipynb)，兩個乾淨kernel共15 code cells、四圖，核對六配套bytes、來源版本、候選轉換與3個共同面輪廓；PROJECT.md記錄面B／點C、時間限制及糖廍最新Revision。未重跑1.3或改crosswalk，未修復／分類／算面積／Overlay／輸出processed GIS，不推定個別分工。 | 待提交（貢獻紀錄未完成） |
| 詹明翰、謝子詮、曾翊涵 | 2026-11-26 Unit 1.5：沿用共同作者，完成[幾何／分類驗證](data/code/taipei_urban_planning_geometry_validation.ipynb)、[296鍵crosswalk及獨立說明](data/processed/urban_zoning_crosswalk_documentation.ipynb)、[新官方分類證據說明](data/raw/unit15_zoning_classification_evidence_documentation.ipynb)，三個乾淨kernel共21 code cells、六張診斷圖；PROJECT.md記錄Unit 1.4通過、B級工作CRS、固定快照、記憶體修復／索引重疊／全市覆蓋與待審B2規則。未改原資料或舊Notebook、未輸出修復GIS或逐里B2，不推定個別分工。 | 待提交（貢獻紀錄未完成） |
| 待成員實際執行／驗收後記錄 | 2026-11-26 Unit 1.6本地成果：[整合準備審查](data/code/taipei_data_integration_readiness.ipynb)15個乾淨kernel code cells／六圖，PROJECT.md記錄正式PM曾翊涵、DE謝子詮、DA詹明翰、任務分配、採用政策及readiness。學生明確確認本輪目前僅Codex協助執行，成員驗收與審查尚待完成，故不將職務或保留的共同作者視為三人已完成之個別貢獻；實際修改／驗收／審查及支持commit待後續據實補錄，不回溯改既有作者／紀錄。 | 待提交（貢獻紀錄未完成；成員實際工作待完成） |
