# Native Arduino car

最新[squad賽道／控制修正](../../docs/SQUAD_COURSE_2026-11-03.zh-TW.md)：回線後會清除舊掉線計時，保留800ms絕對期限。預設Nano編譯8776 Flash／203全域RAM、57項軟體測試通過；尚未五連跑或實車驗收。收線150／升降29秒的模擬實驗未採用，主設定維持。

最新模擬測試與800 ms回線邊界修正見../../docs/SIMULATION_ENV_2026-11-03.zh-TW.md；舊移植大小紀錄不代表最新建置。

這是後續主要維護的原生Arduino程式，核心與硬體讀寫分離，不使用CAGEBOT產生器或moto函式庫。它沿用現有Cageboard、馬達、A1～A5及WS2812，不需要更換硬體。

## 開啟與編譯

保留整個native_car資料夾：native_car.ino和controller.h必須放在一起。用Arduino IDE開啟native_car.ino，安裝公開的 **Adafruit NeoPixel 1.15.3** 函式庫。本次實際編譯目標為Arduino Nano／ATmega328P（Old Bootloader）；實車板型、Bootloader與連接埠仍須依車上硬體確認。

在完整團隊庫可執行：

```powershell
arduino-cli lib install "Adafruit NeoPixel@1.15.3"
pwsh -File tools/Compile-Native.ps1
```

若函式庫只存在某個獨立目錄，用`-NeoPixelLibrary <函式庫根目錄>`。工具只編譯，不列舉連接埠、不上傳、不啟動馬達。預設FQBN為arduino:avr:nano:cpu=atmega328old，可用-Fqbn指定其他已確認目標。

## 維護位置

- controller.h：Settings參數、明確的Follow／Search／Gap狀態、升降狀態及故障原因；輸入為毫秒時間與左至右A5/A4/A3/A2/A1原始ADC，輸出為有正負號的左右PWM。沒有Arduino依賴、動態配置或String。
- native_car.ino：ADC、馬達方向／PWM、開機按鈕、LED及選用序列埠。左方向D7／PWM5，右方向D4／PWM6，按鈕D12，LED D13兩顆，僅更新第1顆。
- 直道100／150／190／230、一般彎174／15或87、搜尋150／反轉114、收線100，以及目前停止開關與時間設定保持原樣。本次是移植與精簡，不重新調速度。
- TIRT_DEBUG_SERIAL預設0，完全移除UART及字串處理。設1時以115200 baud、最多50 ms一筆輸出原始A1～A5與F，格式沿用參考版，使用Flash字串，不建立動態String。
- TIRT_LED_ENABLED預設1，使用Adafruit_NeoPixel。設0可編譯不含LED的版本，但本次預設數據是LED開啟版，不能混用比較。

## 回復與界線

根目錄car.xml／car.ino保留f3501be參考版，不由原生版產生，也沒有保證手寫C++可轉回可編輯積木。tools/rewrite_car.py及export_car.mjs僅維護該參考分支；build.py／config.json仍是另一套保留候選。

本次已做Nano目標編譯、逐步輸出／狀態差異檢查與既有情境模型比較；未上傳或實車驗收。啟動按鈕仍只在開機等待；不是運行中的緊急停止。PWM0不是主動煞車，三感測器仍無法唯一辨識白字、彎道與標記，升降23.35秒及終點出口假設仍在。

完整數據、限制及相同LED函式庫的控制比較見[移植報告](../../docs/NATIVE_MIGRATION_2026-11-03.zh-TW.md)。
