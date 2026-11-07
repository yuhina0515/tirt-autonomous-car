# 程式與維護入口

目前以[firmware/native_car/native_car.ino](firmware/native_car/native_car.ino)及同資料夾controller.h作原生Arduino控制主來源。直接維護C++，不用CAGEBOT產生器，不能承諾反向轉回積木。[編譯步驟](firmware/native_car/README.md)／[2026-11-03移植數據與界線](docs/NATIVE_MIGRATION_2026-11-03.zh-TW.md)。

- 核心：Follow／Search／Gap互斥狀態，另有升降與故障列舉；輸入時間與原始ADC，輸出有正負號的左右PWM。
- 介接：保留現有腳位、按鈕與LED，以公開Adafruit_NeoPixel替代moto函式庫。預設除錯關閉，無String。
- 直道100／150／190／230及既有轉彎、收線、標記與停止策略不變；29項測試及Nano Old Bootloader目標編譯通過，尚未上傳或實車驗收。
- 修改原生版不用重新產生XML。根目錄car.xml／car.ino凍結為f3501be回復參考，既有產生器僅適用參考版。不要用產生器覆寫firmware/native_car。

## 保留參考版說明

以下記錄2026-11-02匯出程式與其維護流程，並非原生版的產生方式。


目前為[2026-11-02精簡候選](docs/SIMPLIFICATION_2026-11-02.zh-TW.md)。舊434af1d及10月26日交接作歷史比較。

後續已加入[物理情境模擬與缺口修正](docs/PHYSICS_SIMULATION_2026-11-02.zh-TW.md)：cross_gap先接納有效窄線再確認15 ms，120 ms缺口期限只處理尚未回線圖樣；故障輸出不被後續命令覆寫。原速度設定保留，緩升速試驗須以--speed-profile gentle及獨立--output重建，不作預設推薦。

## 來源與輸出

根目錄car.xml／car.ino為主檔。修改tools/rewrite_car.py，從legacy/three_sensor_baseline重建XML，再以tools/export_car.mjs與本機保存的原廠產生器匯出Arduino。匯入後等待事件完成並逐父接點檢查；不得只改INO，也不得用數字比較接Boolean。build.py／config.json／firmware屬保留候選。

## 控制契約

- A4/A3/A2低於70按8／4／2形成F，A5/A1另作外側方向輔助。左方向D7／PWM5，右方向D4／PWM6；前進D7 LOW、D4 HIGH，沿用接線，未重測。
- 有效側線前進循跡，F0配合合格方向才啟動搜尋。只有800 ms搜尋總期限；150 ms只限制外側方向修正，收線開始後不再改入彎方向。
- 先選方向再算回線資格。入彎／完成／備援交接消耗舊候選。收線後備援使用最新captureSide；一個loss_fallback函式供各處共用。
- 寬白以前進通過；沒有一般900 ms鎖停或白面內終點停車。升降與終點共用無轉向的F14→F4出口判斷，詳見本次說明。缺口轉寬白移交方向並保留恢復事件，中央80 ms解除恢復。
- 輸出優先序：故障／完成、升降、F10觀察、外側探查、搜尋、缺口、寬白、一般循跡。F10及外側探查仍可能暫停，180秒等故障停止保留。
- 速度及停止開關保持原值；直道階段、小修正及比例循跡不變。

## 驗證界線

原廠Blockly父接點核對與Arduino匯出通過，10項模型／桌面原程式重播檢查通過。使用者已另行授權離線模擬；仍未做Arduino編譯、燒錄或行車驗收。來源不代表車上韌體。終點後無中央窄線時，新出口判斷不會停車；持續F14可前進至180秒上限。關卡仍非唯一辨識，PWM0不是主動煞車。
