# TIRT autonomous-car practice

祥儀 CAGEBOT 自駕車的隊友同步儲存庫。保留可編輯的 **CAGEBOT XML 與同源 Arduino**，
以實際採集資料調整循跡策略。

車上實際版本目前不確定，請先記錄本次實際燒錄的版本。此儲存庫的新控制器已通過軟體測試，
**尚未上車或完成賽道驗證**。三顆感測器不能保證把所有白色文字與白線區分開。

## v0.2.0-rc.1 預發行版

目標：從大片全白區出發，通過銳角彎與虛線，再回到全白區停止。
新增失線前偏向記憶、內輪停止的限時尋線，以及全白起終點處理。
下載及現場設定見 [Release 操作說明](docs/RELEASE.zh-TW.md)。
預設檔仍須實測校正後才能啟動；15 秒最短圈程與 250 ms 全白確認是暫定參數，
**不代表已辨識完整一圈**，途中寬白線或文字仍可能被誤認為終點。

## 明天先做什麼

需要透過筆電藍牙同步資料到 Hina Web，請使用 [藍牙即時採集與 API 說明](docs/LIVE_CAPTURE.zh-TW.md)：
第一次執行 `Configure-Upload.cmd` 設定私人碼，再雙擊 `Start-LiveCapture.cmd`。
離線資料留在本機，恢復連線後用 `Retry-Upload.cmd` 補傳。

1. 下載本儲存庫 ZIP 並解壓縮。保持輪子架空，在 CAGEBOT 開啟
   `firmware/stationary_capture/stationary_capture.xml` 並燒錄。
   **這份採集程式不驅動馬達、不需要按啟動鈕。**
2. 接 USB，關閉其他序列監控器，雙擊 `Start-Capture.cmd`，選 USB 的 COM 埠、115200。
   若改用已測通的藍牙，主機端選 9600；車上 UART 仍為 115200。一次只連一台電腦。
3. 以實際車身高度分別量白線 `LINE`、黑底 `BACKGROUND`、白色文字 `TEXT`。
   先把感測器列**沿著白線方向**擺放，讓五顆都在白線上，再取黑底；每種至少 30 筆。
   不要把「一顆在線、四顆在黑底」標成五顆白線校正。
4. 產生校正建議、檢查範圍後，啟用測試設定並重新產生跑圖 XML，步驟見
   [明天測試單](docs/FIELD_TEST.zh-TW.md)。未校正的預設跑圖檔**不會啟動馬達**。
5. 架空確認左右方向、啟動／停止按鈕，再落地依序測直線、彎道、短文字、長文字及失線。

記錄工具的 `Q` 只結束收資料，**不會讓車停車**。跑圖時按車上按鈕停止；必要時關閉電源。

## 策略改了什麼

- 仍只用中間 **A4、A3、A2** 控制；A5、A1 只記錄，不影響決策。
- 每顆依自己的黑底／白線讀值正規化，使用濾波和遲滯，不只比單一門檻。
- 以連續強度估計偏移，PD 修正左右輪；PWM 上限 100，彎道降速、加速有斜率限制。
- 全亮、分裂、低對比和跳邊屬於「需要時間確認的觀測」，不直接指定固定輪速。
- 失線前可信位置明顯偏邊時，向該側尋線，內輪停止、外輪 PWM 65，最長 650 ms。
- 中央失線以低速直行跨過短缺口，最長 200 ms；其他不確定狀態預設 120 ms。
- 寬白區低速直行，最多 350 ms；離開起點並達最短圈程後，連續全白 250 ms 會停止。
- 每次不確定事件進入時固定期限；短暫正常片段或分類變化不能延長期限。停止後需重新按鈕啟動。
- 路口、文字、升降台、終點**不能只用相同的亮線圖樣辨識**。本版終點為時間條件候選，沒有正式路線順序辨識。

[更新後的 00000～11111 對照及時間策略](docs/CONTROL_POLICY.zh-TW.md) ·
[資料欄位](docs/TELEMETRY.md) · [測試證據](docs/VERIFICATION.md)

## 檔案與修改方式

| 檔案 | 用途 |
|---|---|
| `build.py` | 控制策略來源，僅使用可匯入 CAGEBOT 的積木 |
| `blockly_codegen.py` | 同一份 XML → Arduino，未知積木會拒絕匯出 |
| `config.json` | 暫定端點、速度與時間參數；預設未校正、未啟用驅動 |
| `firmware/practice_controller/` | 新跑圖 XML＋Arduino；預設不會啟動 |
| `firmware/stationary_capture/` | 馬達關閉的資料採集 XML＋Arduino |
| `legacy/` | 修改前程式，方便回退；不代表正式賽已驗證 |
| `tools/` | 接收、標記、校正建議、分析工具 |
| `tests/` | 控制回歸、CAGEBOT 匯入驗證與資料處理測試 |

Python 3.10+，產生檔案不需第三方 Python 套件：

```powershell
python build.py
python build.py --profile capture --out firmware/stationary_capture
python -m unittest discover -s tests -v
```

修改行為請改 `build.py`，修改參數請改設定 JSON，再同步產生、提交 XML 與 `.ino`。
若直接在 CAGEBOT 修改積木，請先保存 XML，再使用 `--from-xml` 匯出相同來源的 Arduino：

```powershell
python build.py --from-xml saved.xml --out build-output/edited
```

這不是任意 C++ 轉積木工具；禁止只改 `.ino` 後宣稱 XML 已同步。

Arduino CLI 編譯目標為已確認的 ATmega328P 舊 bootloader Nano，USB bootloader 為 57600：

```powershell
arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328old firmware/practice_controller
arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328old firmware/stationary_capture
```

新程式不需 NeoPixel 等外加函式庫。`legacy` 的原始匯出可能需要 CAGEBOT Motoshare。
工具不會自動燒錄。先確認板子、COM 埠與輪子架空。

## 隊友同步

`git pull --ff-only` 後先閱讀設定及 manifest，再燒錄，請勿將車上版本與最新來源混為一談。
每次測試記下 Git commit、設定 JSON、車上韌體、賽道位置、電池與感測器高度。
`captures/` 預設不進 Git；分享資料前另行確認內容，保留原始 BIN、CSV、接收收據及測試註記。

MIT，沿用原專案 contributors 授權。原廠編輯器、JavaScript、驅動與教案不隨本庫散布。
連續加權位置與逐顆校正的原理可參考
[Pololu QTR 方法文件](https://www.pololu.com/docs/0J19/3)；本車不是 Pololu 硬體，仍需自己的量測。
