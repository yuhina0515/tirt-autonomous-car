# 路口事件前綴：兩個已知模型診斷完整通過

新實驗在**既有推定模型**中，兩個已知種子均走完209/209，獨立判定項目全通過。這是兩次已知模型診斷，**不是未見資料五連跑、官方賽道驗證或實車驗收**。原候選、native_car、回退檔案及穩定標籤未改動，沒有燒錄或升版。

| 已知種子 | 前次有序收線 | 本次路口前綴 | 模型起終點計時 | 模擬啟動至結束 |
| --- | --- | --- | --- | --- |
| 2026110711 | 198/209、車輪出界 | 209/209、全部判定通過 | 218.880s | 219.320s |
| 2026110714 | 198/209、車輪出界 | 209/209、全部判定通過 | 220.755s | 221.195s |

兩版使用同一修正裁判、路線與物理假設；沒有改地面、馬達／摩擦、車體或感測器參數。模型計時由起點越線到終點越線，兩次起點都是440ms；不能把模擬啟動時間當圈時，更不能當作實車速度量測。舊版沒有完整圈時可比；本次證明特定模型診斷的完賽能力，尚未證明最快速度。

## 為什麼需要事件上下文

前次在I上端寬白交會後，普通循跡仍沿舊左向記憶搜尋而出界。以原訓練種子701～705執行有序收線後，702～705到達交會，四者的升降後事件前綴均為：

```text
R L W L R L R L W -> R
```

第一個W是普通通過，最後一個才是教師目標，不能只數「升降後第一個寬白」。701較早停止，保留為拒絕目標案例，沒有臆造成功指令。

[新核心](../firmware/experiments/junction_context/controller.h)在觀測升降離開流程完成後匹配字串。終端W匹配後將設定方向送入有序收線；不同出口同時匹配，或同一觀測可能是普通W／目標W，都故障停止。前綴不符且遇到W時不猜方向，一次指令消耗後不能重觸發。800ms不確定期限不重開、中央確認仍20ms，路口轉彎期間持續中央寬白仍保留300ms期限。未設定junction表時不虛構出口；相同完整字串的文字仍不能區分，不能宣稱完美抗白字。

## 教師與來源證據

[學習工具](../tools/learn_junction_context.py)只接受路線宣告的訓練種子，拒絕711／714及預留741～745。教師以凍結模型頂點198為離線選取點，由相鄰有向路段推得右轉；頂點、位置與時間不進入Arduino。標籤使用已審核的實際感測器足跡、方向／高度與此前依序過門，**不讀CSV的station註記作標籤**。

五份教師均重新驗證manifest、來源、模型與trace雜湊、物理動力學、種子感測來源及實際核心重播。新版另重驗五份原升降前綴；套用最終路口profile後，再逐筆確認所有教師在目標前的命令、狀態、診斷完全相同，沒有略過欄位差異。701未到目標，整條失敗軌跡重播；其餘四個目標另確認正確方向、事件序號／W及未重設的不確定計時。全部通過後才寫出正式實驗profile。

[指令與來源／教師收據](../simulation/junction_context_mission.json)含四個已驗證目標、一個拒絕目標。特徵身分涵蓋核心與adapter、學得的literal區塊除外；完整profile及實際stage來源SHA再由manifest凍結。修改指令、來源、模型或資料後，不得沿用舊跑圖的驗證結論。

已知711／714的新舊CSV分別有39,005及39,330筆記錄完全相同，首次差異恰在195.025s／196.650s的目標W（eventSerial27）：輸出輪速、轉彎狀態與missionPhase改變，當時位置／ADC／不確定計時未改動。這支持改善來自交會決策，而非前段偷偷改速。兩個種子只用於診斷，沒有成為教師。

## 驗證、收據與重跑

100項Python測試通過，包含八項路口控制測試與資料洩漏、物理標籤、非法指令反證。原生／候選／新實驗共用C++契約通過，CI新增junction_context的32位C++檢查。Nano old bootloader：未套profile8574 bytes Flash／203 bytes全域RAM，套用後9772／251；不是峰值RAM或實測控制週期。

兩次診斷均通過物理軌跡、實際核心命令／狀態、種子感測來源，以及起終點／檢查點／車體覆線／輪跡／方向分層／機構／無故障等判定。`lapDone`仍false，模型依獨立終點越線結束，沒有車上終點停車辨識。

[機器可讀摘要](simulations/2026-11-04-junction-context.json)保存來源與收據雜湊。原始教師在`build-output/junction-context/teacher-701..705/`、診斷在`diagnostic-711/`與`diagnostic-714/`、學習證據在`junction-learning/`。stage來源SHA為`054e609023286c2b9955623ca1fd931e3a0a68d73cd3f524d133b221ddc25973`。原始模型軌跡未提交Git；重跑必須用新輸出目錄：

```powershell
py -3.11 tools/run_course.py --source firmware/experiments/junction_context/junction_context.ino --candidate-profile simulation/junction_context_mission.json --plant-json simulation/plant_high_torque_hypothesis.json --probe-seed 2026110711 --diagnostic-limit-s 240 --output build-output/junction-context/repro-711
py -3.11 -m unittest discover -s tests -v
```

重新學習先用ordered_recovery及其既有profile收集原訓練種子701～705；用`learn_course_mission.py --source firmware/experiments/junction_context/junction_context.ino`重驗升降資料，再以`learn_junction_context.py <五個教師目錄> --source ... --lift-profile ... --vertex 198 --workers 5 --output ...`審核及產生指令。CLI在stderr回報進度，stdout保留JSON摘要。

## 尚未完成與下一步

預留741～745尚未執行，沒有新五連跑。701在189.430s的較早案例仍未解決：z=0、模型車體覆線與V例外輪跡通過，車軸卻無物理支撐，距V頂點96.111mm。這個支撐邊界需先分離「物理底面」與「合法黑道路面」並核對平面場地事實；不能直接擴支撐或放寬輪跡讓測試過關。路口前綴沒有修復它，完整重播保留此結果。

正式比例／方向／分層／F／機構、實測車身與馬達／感測延遲、車上終點辨識及實車完賽仍未核實。兩個已知推定模型診斷成功，不足以升版或宣稱高速刷圈完成。

English handoff: known711/714 pass209/209 under the unchanged inferred model and
judge, including physical/core/sensor audits. Teaching used only701..705
(4targets,1rejected); all5 final-profile prefixes replayed exactly. Native and
previous candidates remain unchanged. Fresh741..745 are unexecuted. Investigate
the701 support/road-legality boundary independently before unseen qualification.
No upload, merge or real-car acceptance.
