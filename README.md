# TIRT 自駕車專案

現況程式為 **434af1d**，開發分支 `docs/legacy-sensor-truth-table`。2026-10-25已整理來源快照；這是尚未完成實車驗收的開發版。最新正式Release仍為 **v0.4.0／e19e214**，沒有用本次快照取代它。

- [現況、完整速度與正式版對比](docs/CURRENT_STATE_2026-10-25.zh-TW.md)
- [現行速度表](docs/SPEED_SETTINGS.zh-TW.md)、[程式與維護說明](car.md)
- [快照參數與雜湊](docs/snapshots/2026-10-25-434af1d.json)
- [v0.4.0發布說明](docs/RELEASE_v0.4.0.zh-TW.md)、[GitHub正式Release](https://github.com/yuhina0515/tirt-autonomous-car/releases/tag/v0.4.0)

## 審查結果

[六部門失敗原因審查（2026-10-25）](docs/audits/2026-10-25-corner-failure-squad.zh-TW.md)：確認2個狀態交接實作缺陷，另列策略／感測／版本證據風險。本輪只診斷，控制程式未修改，缺陷尚未修復。

[Opus5.5 medium獨立審查原文](docs/audits/2026-10-25-opus-5-5-medium.zh-TW.md)與[主審核對](docs/audits/2026-10-25-opus-5-5-medium-verification.zh-TW.md)：同意舊候選重用問題，新增收線備援使用舊入彎方向的缺陷；保留對上一輪審查優先序的不同意見。僅審查，尚未修復。

## 目前主檔

[car.xml](car.xml)是CAGEBOT可編輯主程式；[car.ino](car.ino)由同XML透過本機保存的原廠產生器匯出。修改來源為tools/rewrite_car.py，不要用build.py或config.json覆寫；後兩者只屬firmware/下保留的temporal候選。

直道採100／150／190／230階段，小修正保留階段。一般彎外174、內15或87；尖角搜尋外150、內反轉114；收線100。正常F由A4/A3/A2決定，A5/A1另輔助尖角選側。

彎道寬白時以前進差速通過，白線回到側邊就繼續一般循跡；該事件真正失線才搜尋。LOSS_STOP_ENABLED與CORNER_WIDE_STOP_ENABLED目前都是0，部分失線／彎中寬白逾時改低速補線。升降台依寬白候選消失後立即回中央線、且沒有轉向提示時停車，等待23.35秒；普通圖樣仍可能與十字混淆。

最近交付通過原廠Blockly接點完整性檢查，已同步XML與Arduino；未由本任務編譯、燒錄或實車驗收，仍未取得最新策略通過60／90度彎的回報。來源狀態與車上韌體狀態分開記錄。

## 文件與歷史

修改策略前閱讀[官方規則整理](docs/TIRT_RULES_2026.zh-TW.md)、[硬體紀錄](hardware.md)與[感測圖樣對照](docs/SENSOR_TRUTH_TABLE.zh-TW.md)。感測器物理黑白名稱和F位元不能直接等同；舊說明存在極性用語差異。

升降等待23.35秒低於官方27秒±5%，也沒有下降停止回授，不能宣稱已符合機構完全停止要求。升降位置、終點與整圈仍是候選辨識，無路段定位。

逐次調整文件保留；目前值以[現況文件](docs/CURRENT_STATE_2026-10-25.zh-TW.md)及來源為準。[整理前累積README](docs/history/README-before-snapshot-2026-10-25.md)是歷史封存，不作當前設定。legacy/與three_sensor/保留基礎來源；[採集工具](docs/LIVE_CAPTURE.zh-TW.md)不是修改策略的前置要求，Bluetooth重連工作維持擱置。
