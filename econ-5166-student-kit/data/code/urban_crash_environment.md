# Unit 0.4 環境建立與驗證紀錄

2026-11-25 完成。本文件是執行環境紀錄，合成資料結果不是正式研究發現。
所有路徑均相對於含 `AGENTS.md` 的 `econ-5166-student-kit/`，不是 Git 根目錄。

## 已建立環境

- Windows 11 AMD64、Python 3.12.2 64-bit。
- Interpreter：`.venv/Scripts/python.exe`；未啟用 system-site-packages。
- 19 項指定套件全部安裝、import 及相關功能驗證成功；無未安裝的選用套件。
- 17 項核心套件與已成功驗證的 libpysal／esda 延伸套件，分列於
  [依賴清單](urban_crash_requirements.txt)；共固定 127 項 distribution，含遞迴依賴及 pip。
- [機器可讀驗證結果](urban_crash_environment_validation.json)保存實際版本、底層 GIS 版本、測試斷言結果及原始檔讀取摘要。
- Kernel：`dssi-urban-crash`，顯示名稱 **DSSI Urban Crash**，僅登記於
  `.venv/share/jupyter/kernels/dssi-urban-crash/`。移動專案後須重新產生該 kernel 的 interpreter 路徑。
- 本次前後比較：175 個既有檔案（排除獲准更新的 PROJECT.md）SHA-256 相同；
  全域 Python 的 127 項套件版本與既有 `python3` kernelspec 未變。
  `.venv/` 與 `data/temp/` 已由既有 `.gitignore` 排除，未修改忽略規則。

## 重現方式

以下 PowerShell 指令用於新副本／尚無 `.venv` 的工作包根目錄，不刪除或覆寫既有環境。
本次實際使用 Python 3.12.2；不同 Python patch、作業系統或 wheel 平台仍須重新驗證。
版本固定保留當次成功組合，但不保證未來 PyPI 永久供應所有 wheels。

```powershell
# 在 econ-5166-student-kit/ 執行
if (Test-Path .venv) { throw '已有 .venv，先驗證，不覆寫' }
py -3.12 -m venv .venv
# 僅本終端程序；原執行主機預設 PIP_NO_INDEX=1，曾阻擋下載
$env:PIP_NO_INDEX = '0'
& .\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple --only-binary=:all: --no-cache-dir -r data/code/urban_crash_requirements.txt
& .\.venv\Scripts\python.exe -m pip check
if (Test-Path .venv/share/jupyter/kernels/dssi-urban-crash) { throw '專用 kernel 已存在，先核對，不覆寫' }
& .\.venv\Scripts\python.exe -m ipykernel install --prefix .venv --name dssi-urban-crash --display-name 'DSSI Urban Crash'
& .\.venv\Scripts\python.exe -B data/code/validate_urban_crash_environment.py
```

現有環境只需執行最後一行進行檢查，不需重建。程式預設測試全部項目；
`--only` 可針對失敗項目重試並保留其餘結果。腳本會更新同目錄驗證 JSON，
其餘測試 CSV、PNG、已執行 Notebook、快取與執行紀錄均位於 Git 忽略的
`data/temp/urban_crash_environment/`。原始 Unit 0.4 前置快照僅供本機保護檔比較；
新副本沒有快照時，保護檔比較會明記未檢查，不能當作已驗證。

程式僅針對 libpysal 匯入時的範例快取定位函數作程序內路徑導向，
避免在使用者全域資料目錄建立未使用的範例資料夾；未修改已安裝套件，
沒有替換空間權重或統計方法，也沒有下載範例資料。

## 實際驗證與限制

| 項目 | 實際結果 |
| --- | --- |
| A 套件與依賴 | 19 項 import 成功、版本為穩定發行版、astral=3.2、pip check 無衝突；均來自新 .venv。 |
| B 資料處理 | 合成 CSV 往返、分組加總、one-to-one merge、缺值及 numpy 運算符合預期。 |
| C GIS | EPSG:3826 合成點線面；CRS 往返、歸屬、intersection／overlay、面積 100、交集 50、聯集 150、長度 5 及 make_valid 斷言通過。 |
| D 機器學習 | seed=5166；StandardScaler、PCA、KMeans、Ward、silhouette、ARI／AMI 通過已知三群的檢查。 |
| E 統計 | 合成 ANOVA F=27、Kruskal H=7.2、chi-square=20、Cramér's V=1 及 BH 校正符合預期。 |
| F 空間統計 | 合成 4×4 rook 網格 16 格、48 個有向鄰接、無孤島；Moran's I=0.75，符合預期。 |
| G 圖表 | matplotlib 折線、seaborn 熱圖及 GeoPandas 合成地圖成功；微軟正黑體及 DejaVu Sans fallback，中文字／負號／數值標籤正常，無缺字警告，已透過影像工具目視檢查。 |
| 原始資料 smoke read | 兩年事故、人口、里界、兩份都市計畫 SHP 及四頁 PDF 讀取成功；詳見 JSON。 |
| Notebook | nbformat 建立、nbclient 實際執行 3 個 code cells；sys.executable 與專案 .venv 相同。 |

首次測試的 groupby 斷言錯把群組輸出順序當作固定，已改以群組鍵核對值；
字型檢查已補上 DejaVu Sans 的負號 fallback，重試後皆通過。套件版本未調整。
第一次 Notebook 啟動在受限執行權限下發生 Windows `SetFileSecurity` WinError 5；
以已獲授權的較高執行權限重試後成功，未停用 Jupyter 安全連線檔權限檢查，
未安裝全域套件或更動作業系統權限設定。Windows Proactor／ZMQ 的 selector thread
提示及本機 TCP transport 提示未阻止執行，未隱藏提示或標成測試失敗。
在相同受限沙箱重現時，Notebook 檢查仍可能需要主機允許啟動 kernel 及設定其連線檔權限。

**資料讀取成功僅代表工具可開啟檔案。** 里界 PRJ 可辨識為 EPSG:3826；
細計-面／細計-文仍缺 PRJ，讀取後 CRS=None，未自行指定座標系統。
本次未進行真實資料的幾何修復、空間歸里、疊合或面積計算，也未重跑舊研究。
都市計畫來源版本／CRS、里界適用年度、事故座標基準、官方事故發布口徑及人口代碼對照等既有問題仍待後續驗證。

## VS Code 與單元銜接

命令列已證實專用 kernel 可執行，但不能證明 VS Code 畫面目前選中哪個 kernel。
學生需手動：

1. 確認 VS Code 的 Python、Jupyter 擴充套件可用。
2. `Python: Select Interpreter` → `Enter interpreter path` →
   選取工作包 `.venv/Scripts/python.exe`。
3. 開啟本次暫存測試 Notebook，右上角 `Select Kernel` → `Python Environments`，
   選相同 `.venv`；若顯示 DSSI Urban Crash，可選它並核對路徑。
4. 僅在測試 Notebook 執行 `import sys; print(sys.executable)`，確認為上述新環境；
   不切換或重跑舊研究 Notebook。

環境方面已具備進入 Unit 0.5 Raw Data Documentation 的條件；
Unit 0.5 文件化時須保留上述未知事項，不能宣稱所有資料已可分析。
本階段完成後停止，等待學生審查。所有貢獻歸屬及學生自行 commit／push 仍待完成。
