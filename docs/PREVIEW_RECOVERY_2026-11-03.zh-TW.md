# 預視與收線實驗：未採用

這次修改通過定向測試，完整模型診斷仍失敗，而且714退步，因此沒有取代原候選。[失敗實驗來源](../firmware/experiments/preview_recovery/controller.h)與[專用任務profile](../simulation/preview_recovery_mission.json)另行保存；維護主程式、原candidate_car、rollback與穩定標籤不變。官方驗收仍0次，沒有燒錄。

## 修改與反證

升降流程完成後，單側外／內灰階與中央線同時可見時，基準PWM上限降至100；中央窄線或反側有效內線出現時，立即退出固定轉彎，尚未確認的收線基準上限85。同一不確定事件不能重新觸發固定轉彎；仍需20ms中央窄線確認，800ms總期限不變。

合成ADC的舊／新實際核心對照：預視基準PWM175→100，中央線首次返回後固定轉彎旗標1→0，不確定時間兩者均65ms。新增四項測試，涵蓋左右鏡像預視、中央線先退出再確認、反側內線不清除事件，以及反側強提示不能重新啟動轉彎或延長期限。這些只證明指定功能，沒有證明車身走向正確。

## 完整模型診斷

| 種子 | 先前候選 | 本次實驗 | 首次方向違規：先前→本次 |
| --- | --- | --- | --- |
| 2026110711 | 189.630s控制器故障，192/209 | 189.310s失去路面支撐，192/209 | 186.660→186.760s |
| 2026110714 | 188.575s車輪出界，194/209 | 188.535s控制器故障，192/209 | 188.450→188.295s |

711舊版本輪重新執行；714舊版取自先前凍結heldout-final證據，沒有偽稱重跑。課程、物理設定、裁判、感測與核心重播程式文字核對相同；訓練工具有歷史差異，兩版profile與來源雜湊分別保存。使用相同高扭力假設與對應種子的物理條件；都不是實車參數。

新兩跑均通過獨立物理軌跡審核、實際核心命令／狀態重播及種子感測來源重新生成，皆有方向違規，合法完成0/2。這兩個種子已被診斷，不能算未見驗證或與先前五跑湊成新成績。診斷時限240s；711舊版重跑設210s，三跑都在時限前實際失敗。沒有放寬路面、方向或關卡條件。

完整摘要與收據：[機器可讀結果](simulations/2026-11-03-preview-recovery.json)。本輪凍結原始軌跡、來源、模型、manifest及離線回放保存在`build-output/preview-recovery/{baseline-711,candidate-711,candidate-714}/`，原始檔未提交Git。套用profile的來源SHA為`f29b9fe14492c5824d79d418a67acf63d2b26a54425a8f364a54bf2f13b5577a`；另行封存後重新stage的來源SHA與兩跑完全相同。

## 驗證與重跑

任務profile以五個原訓練種子的已審核物理目標，完成新版核心到目標前的ADC／命令／狀態／事件逐筆重驗，5份通過、0份拒絕。沒有用驗證種子訓練。新增實驗是獨立Arduino資料夾，檔名改名不影響來源內容身分。

最終80項Python測試通過（20.721s）。Nano Old Bootloader：實驗未套profile8312 bytes Flash／188 bytes全域RAM，套用profile9226／226；只是靜態編譯，不代表峰值記憶體或實車迴圈。原生與候選C++回歸通過。Python使用`py -3.11`，避免系統預設3.9低於專案最低版本。

每次指定新輸出目錄，不覆寫凍結批次：

```powershell
py -3.11 tools/run_course.py --source firmware/experiments/preview_recovery/preview_recovery.ino --candidate-profile simulation/preview_recovery_mission.json --plant-json simulation/plant_high_torque_hypothesis.json --probe-seed 2026110711 --diagnostic-limit-s 240 --output build-output/preview-recovery/repro-711
py -3.11 -m unittest discover -s tests -v
```

## 下一步

714最後僅短暫出現中央窄線，仍不滿20ms；711退出固定轉彎後仍走向路面外。單純降速及提早退出固定轉彎不足以完成合法收線。下一輪應分離預視與收線兩個因素，以同側外→內→中央的順序、輪速滯後及轉向收斂測試設計控制；不能只把反側誤差當成合法出口，也不能延長不確定期限來掩蓋失敗。坡道倒退、正式幾何與機構事實、實測馬達／感測延遲及車上終點辨識仍未解決。

English handoff: this is a rejected, reproducible experiment, not a new default.
Keep the original candidate/profile pair. Continue from frozen failed traces,
separate preview and capture changes, and reserve new unseen seeds only after
tuning. No source promotion, upload, merge or hardware acceptance occurred.
