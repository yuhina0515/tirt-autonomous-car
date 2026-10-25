# car.xml 程式與維護說明

2026-10-25現況程式為434af1d，完整參數、限制與v0.4.0對比見[現況文件](docs/CURRENT_STATE_2026-10-25.zh-TW.md)。本次只整理文件與快照，控制檔案不變。

## 來源與輸出

- 根目錄car.xml／car.ino為現用主檔，修改工具為tools/rewrite_car.py，從legacy/three_sensor_baseline保留來源重建CAGEBOT積木。
- tools/export_car.mjs使用本機原廠Blockly／Arduino產生器；先等待載入事件並逐接點比對，接點被拆開即拒絕輸出。不得只改Arduino，也不得把Boolean條件接到數字比較；目前用整數turnCaptureVisible保存0／1。
- build.py、config.json及firmware/屬另一套保留候選，不產生本版主程式。原廠產生器、私人採集／上傳設定不隨快照散布。

## 感測與命令

由左到右的接線紀錄為A5、A4、A3、A2、A1。中間低於LINE_THRESHOLD70的感測器按8／4／2形成F；A5/A1原始讀值另作外側方向輔助，不進正常sumW。F0＝三顆未低於門檻，F14＝三顆均低於門檻；不能僅用「全黑／全白」判斷F值。

馬達記錄為左方向D7／PWM5，右方向D4／PWM6；前進為D7 LOW、D4 HIGH。這是沿用接線來源，未於本次重測或交換。

現行狀態輸出優先序為故障／完成、升降等待或離台、F10短暫觀察、外側方向探查、尖角、缺口、寬白、一般循跡。部分F0／彎中F14逾時因暫停開關轉低速備援，但其他故障／終點／180秒上限仍有效。

直道階段只累積正常中央線時間。小修正暫停累積且保留階段；長修正先一般彎，回中30 ms恢復。寬白彎道有方向就前進100／50或鏡像，方向過期100／100；側線再出現使用174一般彎，不因仍在線而重啟反轉。中央80 ms結束寬白恢復；普通無方向十字則按30 ms候選、直接F4出口停等。

## 目前驗證界線

最新來源已做原廠Blockly載入接點檢查並同步匯出Arduino；未編譯、燒錄或新增行車驗收。60／90度彎仍屬待確認，沒有新ADC／輪速／位置資料。對照表、時間閾值或成功產生XML都不代表車子已完成一圈。

[速度表](docs/SPEED_SETTINGS.zh-TW.md)、[寬白後仍在線](docs/WIDE_VISIBLE_LINE_2026-10-25.zh-TW.md)、[升降十字出口](docs/LIFT_CROSS_EXIT_2026-10-25.zh-TW.md)、[規則](docs/TIRT_RULES_2026.zh-TW.md)為主要參考。[整理前car.md](docs/history/car-before-snapshot-2026-10-25.md)只作歷史。
