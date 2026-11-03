# 有序收線與尖角檢查點修正：仍未完賽

有序收線實驗在同一個修正後模型裁判下，兩次均走到198/209；原候選為195/209及194/209。兩次仍在後續寬白交會處車輪出界，合法完成0/2，**未採用為主程式或取代原候選**。官方已核實完整賽道試驗仍0次，沒有燒錄。

## 控制實驗

來源為[獨立有序收線實驗](../firmware/experiments/ordered_recovery/controller.h)，搭配[專用任務profile](../simulation/ordered_recovery_mission.json)。原candidate_car／recovery_mission、native_car、根目錄rollback及穩定標籤均未改動。

這次只改升降後急彎的收線，不加入前次預視降速：入口提示固定本次搜尋方向；中央與選定側離線後，同側外或內感測器返回，才把快速轉彎切成柔和收線。反側誤差可修正輪速，但不能改寫本次搜尋方向。它還不是完整的「外→內→中央」順序證明。

不可見時的柔和搜尋為15/105鏡像；可見時基準90、修正限45，均是暫定PWM。仍須20ms中央窄線確認；各階段共用800ms期限，快速轉彎仍有650ms上限，重複提示不能重開事件。新增四項定向測試，驗證入口殘留中央線、左右同側返回、錯側順序及固定方向。

原711軌跡最後一次右轉：右外側在189.365s返回，中央在189.475s返回；舊版這段約110ms仍快速轉彎。本次利用同側返回提早換收線力度。五份原訓練前綴已重新產生物理ADC，逐筆確認新版至升降訓練目標前的命令／狀態／事件完全相同，5份通過、0份拒絕。沒有以711／714訓練。

## 模型裁判缺陷與修正

原檢查點在每個頂點使用「入彎切線」法向平面。A尖角的車軸在尖角內側轉彎，模型車體覆線與輪跡仍合法，但車軸永遠沒有穿越該平面，因此後續有向路段進度卡住，產生假的錯路訊號。711在尖角附近的入彎平面最大位移仍為-27.016mm；實際越過入／出彎角平分面時，距頂點39.803mm。714相應為-25.972mm、38.344mm。

`crossed_route_gate`在頂點使用入／出切線單位向量相加後的法向；非頂點的起終點／直線檢查仍使用原平面。道路半寬、高度容差、正向越線、檢查點順序、車體／輪跡、方向／分層與機構條件保持；精確180度反轉沒有唯一角平分面，保留原判定。這只是推定路線的進度幾何，不是官方關卡位置或實車合法性的核實。

新增三項幾何回歸，含真實凍結的模型尖角姿態，並反證逆行、過遠切角、錯層及直線／精確反轉。修正對所有頂點一致套用，不依控制器或種子選規則。

## 原判定與修正判定分開比較

| 已知種子 | 舊候選／原判定 | 有序收線／原判定 | 舊候選／修正判定 | 有序收線／修正判定 |
| --- | --- | --- | --- | --- |
| 2026110711 | 192/209 | 194/209 | 195/209 | 198/209 |
| 2026110714 | 194/209 | 194/209 | 194/209 | 198/209 |

修正後711舊版首次失敗為189.630s控制器故障；有序收線為195.290s車輪出界。714舊版188.450s首先錯向、188.575s車輪出界；有序收線196.915s車輪出界。新實驗的`direction_and_layer`複合條件仍為false，因為它也要求走完全部檢查點；不能把它直接解讀成已證實的逆行。

兩個新實驗及711舊版均保留原始凍結結果，再以相同新裁判另外重審；舊714另以新裁判重跑，其物理軌跡SHA與先前保存版完全相同。新舊四個比較都有實際核心重播、物理感測來源及軌跡審核；沒有修改物理模型或混合兩版裁判成績。新實驗至今仍0/2，不能把較大的檢查點數當成完賽。

完整摘要、來源、manifest、trace與新裁判收據雜湊見[機器可讀證據](simulations/2026-11-04-ordered-recovery.json)。原始批次在`build-output/ordered-recovery/{seed-711,seed-714,baseline-714-corner-v1}/`，711舊版仍在`build-output/preview-recovery/baseline-711/`。`corner_details-audited.json`與同名auditor快照是新增重審，原results／manifest沒有覆寫。原始個人採集與模型軌跡不進Git。

## 驗證與重跑

87項Python測試通過，原生／候選／有序實驗共用C++回歸通過，CI新增有序實驗的32位C++檢查。Nano old bootloader：未套profile8360 bytes Flash／191 bytes全域RAM；套用profile9312／229。這是靜態建置數字，不是實車速度、峰值RAM或迴圈量測。

同時修正任務韌體stage資料夾依來源檔名命名，避免`ordered_recovery.ino`被放入`candidate_car`而不能直接Arduino編譯。10ms建置路徑煙霧測試不計入兩次診斷；其來源SHA與正式兩次診斷相同：`34a36dab7740584bfee0e63e652200d4d2578cef5da0aeb5583b51b97ab2b4fe`。learner CLI新增stderr進度，audit收據保留每次完整判定，避免只看到彙總失敗而無法定位。

請使用新的輸出目錄；新執行器會直接採用修正後的頂點判定：

```powershell
py -3.11 tools/run_course.py --source firmware/experiments/ordered_recovery/ordered_recovery.ino --candidate-profile simulation/ordered_recovery_mission.json --plant-json simulation/plant_high_torque_hypothesis.json --probe-seed 2026110711 --diagnostic-limit-s 240 --output build-output/ordered-recovery/repro-711
py -3.11 -m unittest discover -s tests -v
```

## 下一步與交接

新實驗已越過A尖角，後續靠近I上端的寬白交會處，普通循線仍沿先前左向記憶搜尋而出界。下一輪應核對交會前後的可觀測事件與指定出口，將單純「失線延續前向」與真正的岔路選擇分開。寬白本身不能唯一決定轉向或終點，不能憑模型座標把出口直接送入車上控制器。

新種子2026110741～745已在診斷結果前預留，**尚未執行**，不供繼續調參或訓練。正式路線／方向／分層／F／機構與實測馬達、感測、幾何仍不完整，車上終點辨識也未實作。不得宣稱模型或實車完全通過。

English handoff: original controller/profile pairs stay unchanged. Ordered capture
is isolated and still fails0/2. A uniform corner-progress judge correction has
separate frozen audits and negative tests; do not pool old/new judging counts.
Fresh741..745 seeds are reserved and unexecuted. Next investigate observable
post-lift junction context, not longer uncertainty timers or pose access.
