# 藍牙採集並上傳 Hina Web

資料流：車上 CSV → 筆電藍牙序列埠 → 本機 `captures/` → HTTPS API → Hina Web SQLite。
接收與上傳在不同程序執行；網路中斷時接收仍持續。原始 BIN、CSV、採集收據留在筆電，
伺服器儲存 CSV 的原始數值與人工標籤，沒有把筆電的原始 BIN 或 COM 位址公開。

## 筆電第一次設定

1. 安裝 Python 3.10 以上並下載此版本 ZIP，完整解壓縮。
2. 先在 Windows 配對車子的藍牙，確認「傳出」序列埠 COM 編號。一次只讓一台電腦連車。
3. 雙擊 `Configure-Upload.cmd`，貼上私人上傳碼。設定預設使用 `https://hina-tw.ddns.net/tirt-data`。
   上傳碼透過 Windows DPAPI 加密，保存在 `%APPDATA%\HinaTirt\upload.xml`。
   每台筆電、每個 Windows 帳號需各自設定，不能複製這份加密檔使用。
4. 雙擊 `Start-LiveCapture.cmd`，輸入藍牙 COM 埠；預設主機端 9600，USB 可選 115200。
   車上 UART 仍為 115200。關閉 CAGEBOT／Arduino 序列監控器，避免占用同一個 COM。

採集模式先燒錄 `stationary_capture.xml`；實車跑圖時使用已實測校正並啟用的跑圖檔。
兩者都是目前的 18 欄 CSV 合約。車上版本若太舊、輸出格式不同，接收器會保留原始 BIN，
但不會把不符合格式的行當作數值上傳。請查看 `.capture.json` 的 invalidLines。

## 使用時

- L=白線、G=黑底、T=文字、R=跑圖、M=人工事件、U=未標記，Q 結束採集。
- 最長採集 30 分鐘；需要更多次資料可重新啟動。選單期間上傳程序也會補傳先前的採集。
- 每 2 秒檢查新增資料，每批最多 100 筆；這是排程目標，實際延遲取決於網路與排隊量。
- `captures/upload-*.log` 會顯示 UPLOADED 或 PENDING。離線時資料留在本機。
- 結束或下次連網後雙擊 `Retry-Upload.cmd`，補傳所有 `captures/run-*.csv`。
- 不要刪除或手改 `.upload-state.json`；它保存批次、確認位置及伺服器 session ID。
  資料完整補傳以前，保留原 CSV 與這些狀態檔。
- 上傳中的 CSV 必須只追加。若已確認的資料被修改／截短，工具會拒絕繼續，避免悄悄混成同一次採集。
- 網路成功後原始檔仍保留，不會自動刪除。請自行依測試日期備份。

結束採集、上傳中斷或筆電斷線不會讓車停下來。跑圖時用實體按鈕或電源停止。
車上實際版本不明時，session 的 firmware 預設記錄 UNVERIFIED，不能據此聲稱已燒錄新版。

## API

健康狀態：`GET https://hina-tw.ddns.net/tirt-data/health`，不需上傳碼。
其他 API 的憑證一律放 `Authorization: Bearer <token>`，不要放網址。

| 方法／相對路徑 | 權限 | 用途 |
|---|---|---|
| POST `/api/v1/sessions` | upload | 建立 session；body 為 id(UUID)、metadata、header |
| POST `/api/v1/sessions/{id}/batches` | upload | body 為 sequence(從 0 開始)、records(每筆 20 欄，含 host_ms、label) |
| GET `/api/v1/sessions` | read | 最近 100 個 session、筆數與描述 |
| GET `/api/v1/sessions/{id}/export.csv` | read | 完整 CSV，可直接交給 `tools/analyze.py`／`tools/calibrate.py` |

上傳權限不能讀取其他人的採集。下載權限由管理者保管，不放在公開 Release。
相同 session、sequence、內容重傳會回傳相同 SHA-256，不重複增加筆數。
相同 sequence 卻換內容，或跳過 sequence，會收到 409，工具保留待傳資料。
伺服器每批最多 200 筆、請求 256 KiB、每 session 最多 100 萬筆，資料庫預設 2 GiB 配額。
配額滿會拒絕新資料，筆電保留待傳內容。

## 伺服器與驗證範圍

服務：`/srv/docker/tirt-data`，`hina-tirt-data` 容器綁定 `127.0.0.1:8212`。
資料：`/srv/shared/tirt-data/telemetry.sqlite3`，WAL／同步提交；容器重啟保留資料。
私人碼保存在伺服器 `config.json`，不進 Git；資料目前由管理者備份／清理，沒有自動保留期限。
部署只加 Caddy 的 `/tirt-data/*` 路由，既有 `/tirt` 模擬器繼續使用。

本機測試涵蓋權限、併發重傳、批次衝突、重啟持久化、配額、回覆遺失後繼續追加 CSV、
半行資料、已確認檔遭修改與單一上傳程序限制。
2026-10-25 已通過 15 項測試；公開 HTTPS 已驗證 206 筆合成資料、遺失回覆後重送、
Windows 啟動工具上傳、下載內容一致、上傳／下載權限分離，以及容器重啟後仍可下載原資料。
這筆 session 的 experiment 為 `SYNTHETIC_HTTPS_SMOKE_20261025`，不是真車資料。
部署時既有 14 個容器保留原 ID，Caddy 只增加 TIRT 路由，既有頁面 HTTPS 健康檢查通過。
詳見 [驗證紀錄](telemetry-verification.json)。
模擬 CSV 通過不代表實車藍牙已連通；現場仍要核對 COM 埠、實際韌體與資料筆數。

服務回退可先 `docker stop hina-tirt-data`，再移除 Caddy 中有 TIRT telemetry 註解的完整區塊，
執行 Caddy validate、reload。不要整份覆蓋較新的 Caddyfile；部署前備份路徑記錄在伺服器
`/srv/docker/tirt-data/deployment.json`。回退後保留資料目錄與私人設定，供恢復使用。
