# race_two_marker RUNNING 遙測協定

遙測只負責回報:D12 啟停與馬達輸出維持正常,遙測不讀序列指令,也不控制馬達。

**狀態:本協定尚未經實車驗證。** 文中的速率與頻寬都是設計值或理論計算,不是硬體實測。實際掃描率、感測器頻寬與穩定上限,必須由實際擷取的資料判定;每次擷取的統計也只代表該次擷取。

## 傳輸

- USB Serial,115200 baud,只由 Arduino 往電腦單向傳送。
- 固定 48 位元組的二進位訊框,多位元組欄位一律為 little-endian。
- 每 20000 µs 一個傳送時段(設計值 50 Hz,以裝置時脈計算)。
- 理論占用:48 × 10 bit × 50 Hz = 24000 bit/s,約為 115200 baud 的 20.8%。
- 傳送前先檢查 `Serial.availableForWrite()`。空間不足時,該時段的訊框直接放棄並將 `dropped` 加 1,不等待、也不會在下一次掃描補送。
- 不使用 heap、`Serial.print` 或 `flush`。訊框放在堆疊上,每個傳送時段占用 48 位元組。

## 訊框格式(版本 1)

| 位移 | 長度 | 型別 | 欄位 | 說明 |
|---:|---:|---|---|---|
| 0 | 2 | u8×2 | sync | 固定 `A5 5A` |
| 2 | 1 | u8 | version | 固定 `1` |
| 3 | 1 | u8 | length | 固定 `48`,為整個訊框的長度 |
| 4 | 2 | u16 | seq | 已送出訊框的序號,從 0 開始,65535 後回到 0 |
| 6 | 2 | u16 | dropped | 因傳送緩衝區不足而放棄的累計訊框數,會回繞 |
| 8 | 4 | u32 | scan_start_us | 本次掃描開始的 `micros()`,約 71.6 分鐘回繞 |
| 12 | 4 | u32 | loop_gap_us | 本次與上次控制迴圈開始的間隔 |
| 16 | 4 | u32 | max_loop_gap_us | 統計窗內最大的 loop_gap_us |
| 20 | 2 | u16 | scan_us | 本次掃描耗時,不含遙測本身;由呼叫端飽和於 65535 |
| 22 | 2 | u16 | max_scan_us | 統計窗內最大的 scan_us |
| 24 | 2 | u16 | scan_count | 統計窗內的掃描次數,含本次,飽和於 65535 |
| 26 | 10 | u16×5 | raw | 依序為 A5、A4、A3、A2、A1 的 ADC 值 |
| 36 | 2 | i16 | left_pwm | 傳給 `writeWheels` 的左輪值,負數代表反轉 |
| 38 | 2 | i16 | right_pwm | 傳給 `writeWheels` 的右輪值,負數代表反轉 |
| 40 | 1 | u8 | mask | 五路 Schmitt 狀態,見下節 |
| 41 | 1 | u8 | phase | 見代碼表 |
| 42 | 1 | u8 | fault | 見代碼表 |
| 43 | 1 | u8 | events | 已確認的全白事件數 |
| 44 | 1 | u8 | flags | 見下節 |
| 45 | 1 | u8 | motion | 低 4 位元為 motion mode,高 4 位元為 motion fault |
| 46 | 2 | u16 | crc | 位移 0 到 45 共 46 位元組的 CRC |

**統計窗:** 從上一個「已送出」訊框之後,到本訊框為止的所有掃描。放棄的時段不會清空統計窗,所以 `max_*` 與 `scan_count` 仍涵蓋被放棄的那段時間。`scan_us` 與 `loop_gap_us` 只是單次取樣,評估尖峰時要看 `max_*`。

**PWM 欄位是命令值,** 不是量測到的輪速或實際出力。

## CRC

CRC-16/CCITT-FALSE:多項式 `0x1021`,初值 `0xFFFF`,輸入輸出皆不反射,最後不做 XOR。

驗證向量:ASCII `123456789` 的結果是 `0x29B1`。

## mask 與 flags

`mask` 的位元與 `raw` 的對應:

| 位元值 | 0x10 | 0x08 | 0x04 | 0x02 | 0x01 |
|---|---|---|---|---|---|
| 腳位 | A5 | A4 | A3 | A2 | A1 |
| raw 索引 | 0 | 1 | 2 | 3 | 4 |

位元為 1 表示該路處於低 ADC 狀態(ADC < 70 時設為 1,≥ 100 時清為 0,其間維持原值)。控制器把這個狀態當作白色處理,但本協定不宣稱它等於實體顏色。

`flags`:

| 位元值 | 名稱 | 意義 |
|---|---|---|
| 0x01 | running | 已由 D12 啟動 |
| 0x02 | stopped | 已由 D12 手動停止 |
| 0x04 | mask_stale | `mask` 可能是舊值 |
| 0x08 到 0x80 | 保留 | 目前固定為 0 |

**mask 可能過期:** 控制器只在 `tick` 內更新 `mask`。尚未啟動、手動停止、完賽或故障時都不再更新,此時 `mask_stale` 為 1,`mask` 不代表目前感測器狀態;要看當下讀值請用 `raw`。旗標採保守判定:進入 Fault 的那一次掃描,`mask` 可能其實已更新,仍會標為過期。

**motion 也可能是舊值:** 等待升降機時內層 motion core 不執行,舊版 R2 慢速離開模式也不經過它,所以此時 `motion` 只代表最後一次的內層狀態。

## 代碼表

| 欄位 | 代碼 |
|---|---|
| phase | 0 BeforeLift、1 WaitLift、2 ExitLift、3 AfterLift、4 Finished、5 Fault |
| fault | 0 None、1 Manual、2 Timing、3 RunLimit、4 ExitTimeout、5 Motion、6 Uncertain |
| motion mode | 0 Follow、1 Search、2 Gap |
| motion fault | 0 None、1 SearchDeadline、2 CapturePattern、3 GapDeadline、4 SplitPattern、5 LiftExitDeadline、6 RunDeadline、7 UnexpectedPattern |

D12 手動停止目前由 sketch 的 `stopped` 表示,不一定會讓 `fault` 變成 Manual,判讀時請同時看 `flags`。

## sketch 呼叫語意

- 每次 `loop` 都呼叫一次 `emit`,放在馬達輸出之後,包含尚未啟動與已停止的掃描。
- `scanStartUs`:`loop` 開頭的 `micros()`。
- `loopGapUs`:與上次 `scanStartUs` 的差,以無號數相減,包含上一輪 `emit` 的耗時。
- `scanUs`:從 `scanStartUs` 到馬達輸出完成,在呼叫 `emit` 前取得;超過 65535 時由呼叫端飽和。
- `applied`:實際傳給 `writeWheels` 的值;未運轉時傳 `race::Wheels()`。
- `raw`:若閒置時不讀 ADC,傳送的就是 sketch 保留的舊值或初值,解讀時要依 `running` 判斷。

超過一個週期的慢掃描會讓時段重新對齊,不會連發補送,這類略過的時段也不計入 `dropped`。可從 `loop_gap_us` 與 `max_loop_gap_us` 看出來。

## 電腦端工具

錄製(只在此指令需要 pyserial;只讀取序列埠,不寫入;已存在的檔案不會被覆寫):

```powershell
python -m pip install pyserial
python tools/decode_race_telemetry.py record --port COM5 --output captures/run1.bin --seconds 400
```

省略 `--seconds` 時會持續錄到按 Ctrl+C。

解碼成 CSV,並輸出 JSON 統計:

```powershell
python tools/decode_race_telemetry.py decode captures/run1.bin --csv captures/run1.csv --summary captures/run1.json
```

完全沒有有效訊框時,結束代碼為 1。`captures/` 不進 Git。

### 重新同步

解碼器尋找 `A5 5A`,檢查 version、length 與 CRC。任何一項不符,就從該處的下一個位元組繼續找,所以損毀訊框之後的完整訊框不會被連帶丟棄。

| 統計欄位 | 意義 |
|---|---|
| crc_errors | 標頭正確但 CRC 不符的候選訊框數 |
| header_rejects | 有 sync 但 version 或 length 不符的次數 |
| skipped_bytes | 重新同步時跳過的位元組數 |
| truncated_tail_bytes | 檔尾不足一個訊框的位元組數 |

### 計數器與分段

CSV 的 `seq_unwrapped`、`dropped_unwrapped`、`time_us_unwrapped` 是已還原回繞的值。序號未前進、後退超過範圍(差值 ≥ 32768,約等於連續遺失 10 分鐘以上),或裝置時間倒退時,視為新的一段(`segment` 加 1),通常代表板子重置。分段之間不串接,也不計入遺失數。

| 統計欄位 | 意義 |
|---|---|
| device_dropped_frames | 裝置端因緩衝區不足而放棄的訊框數(`dropped` 差值) |
| missing_sequence_frames | 已送出但沒有成功解碼的訊框數(`seq` 缺口),例如傳輸損毀或電腦端遺失 |
| frame_rate_hz | 本次擷取的實際訊框率 |
| mean_scan_hz | 本次擷取的平均掃描率,由 `scan_count` 總和除以裝置時間 |
| saturated_scan_windows | `scan_count` 飽和的統計窗數;大於 0 時 mean_scan_hz 偏低 |
| frame_interval_us、sampled_scan_us、sampled_loop_gap_us | 最小、平均、p50、p95、最大值 |
| peak_scan_us、peak_loop_gap_us | 所有統計窗的最大值 |

每段第一個訊框的統計窗會回溯到開機,因此不計入掃描率、間隔與尖峰,只有它的單次 `scan_us` 取樣會被採用。

## 現場注意事項

- 許多 Nano 開啟序列埠時會自動重置。`record` 雖先把 DTR/RTS 設為 false 來降低機率,但不保證有效。請先開始錄製,確認板子就緒後再按 D12;若在運轉中開啟序列埠,可能造成車輛重置並停止。
- 擷取期間 USB 線會連著車身,實際會開動馬達,線材要避免拉扯或干擾車輛,並先在架空狀態確認。
- 每次序列傳輸都會產生中斷,開啟遙測本身可能改變掃描時序,因此這個版本的量測結果不能直接套用到未啟用遙測的版本。

若有接收遺失訊框或scan_count飽和，摘要的mean_scan_hz為null，避免用不完整視窗低估掃描率。第一個訊框的區間尖峰仍納入peak統計。
