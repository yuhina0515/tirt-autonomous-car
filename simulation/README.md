# TIRT離線模擬環境

完整圖面重建入口為`reconstructed_course.json`與`tools/run_course.py`，詳見[賽道建置與squad報告](../docs/SQUAD_COURSE_2026-11-03.zh-TW.md)。它描繪官方圖中的上方迴路及TAIWAN，含分層支撐、坡度、機構與獨立軌跡裁判；方向、橋接、高度、比例及車型仍有假設，五次連續完成尚未達成。

```powershell
py -3.11 -m pip install -r simulation/requirements.txt
py -3.11 tools/run_course.py --output build-output/full-course/new-run --plant-json simulation/plant_high_torque_hypothesis.json
py -3.11 tools/audit_course_run.py build-output/full-course/new-run
```

上述高扭力設定是敏感度假設，不是實車資料。省略`--plant-json`使用原2.5m/s²假設，其爬坡可行性不足。執行後開啟新批次`index.html`；每批輸出不可覆寫，下一次需更換資料夾名稱。`--baseline add30a7`建立對照；`--experiment capture150_lift29`僅建立未採用的獨立實驗程式。既有批次`--replay-only`使用其凍結賽道重建回放。程式只離線編譯及模擬，沒有上傳或硬體操作。

## 連續控制與路線辨識候選

另有獨立`firmware/candidate_car`實驗版，維護中的主程式仍是`native_car`。結果與停止條件見[控制與物理修正報告](../docs/CONTROL_RECOVERY_2026-11-03.zh-TW.md)。未套用profile時不會將寬白當成升降台；訓練需先走到真正模型平台。以下輸出資料夾需使用新名稱：

```powershell
py -3.11 tools/run_course.py --source firmware/candidate_car/candidate_car.ino --plant-json simulation/plant_high_torque_hypothesis.json --diagnostic-limit-s 150 --output build-output/control-training-repro
py -3.11 tools/learn_course_mission.py build-output/control-training-repro --source firmware/candidate_car/candidate_car.ino --output build-output/control-profile-repro.json
py -3.11 tools/run_course.py --source firmware/candidate_car/candidate_car.ino --candidate-profile build-output/control-profile-repro.json --plant-json simulation/plant_high_torque_hypothesis.json --seed-plan simulation/recovery_validation_seeds.json --output build-output/control-heldout-repro
py -3.11 tools/audit_course_run.py build-output/control-heldout-repro
py -3.11 tools/traction_sensitivity.py --output build-output/traction-repro.json
```

profile綁定程式、賽道與感測物理模型。模型文字身分統一LF／CRLF；批次manifest仍驗證原始位元組。修改程式需重新訓練，或讓新版實際核心在每個訓練目標之前，通過重新生成ADC／命令／狀態／事件的完全一致重播。訓練標籤取自獨立審核的物理位置與依序過門，CSV的station註記不作標籤依據。保留種子不能加入訓練。

`--probe-seed`只能搭配診斷時限，單次或縮短時限的批次一律不能算五連跑。候選版沒有車上終點停車判斷；裁判依實際終點越線停止模型試驗。沒有燒錄或實車驗收。

## 原短情境環境

在完整團隊庫執行`py -3.11 tools/run_simulation.py`，再開啟build-output/simulation/index.html。需要Windows／MSVC（或Visual Studio Community）；模擬本身只用Python標準函式庫，不需要Arduino板、CAGEBOT、Node或網路。首次尚未安裝Python／MSVC時需自行準備。Arduino目標編譯另外使用既有Compile-Native.ps1與公開LED函式庫。

scenarios.json可設定物理參數及情境。預設比較00e0db0原生移植版與目前工作目錄：14種情境×3組參數×兩版，共84次。包含直道、左右60／90／120度改向、寬白V彎、短／長缺口、合成T形文字、窄線雜訊及反向ADC極性；三組參數為名目、低電量／輪差、低抓地／延遲。基準必須存在於本機Git，可用--baseline改變。路線圖形不是正式TAIWAN圖，物理參數不是實車量測值。

每次產生結果JSON、10 ms軌跡CSV與獨立HTML回放。HTML可離線播放、拖曳時間及切換案例；車形只是位置／方向示意。`--replay-only`可由已保存JSON／CSV重建HTML，不重跑控制程式。更改情境設定後應完整重跑，不可將新設定混用舊結果。

驗證：`py -3.11 -m unittest discover -s tests -v`。有新控制行為時，保留舊版對照並新增定向測試，不要求所有物理壓力案例都「到達」。反向ADC案例刻意展示極性錯誤的風險；三白、白字與關卡仍可能有相同觀測。不能把到達數當作實車成功率。

本輪修正：已在搜尋期限內連續確認15 ms的回線，在800 ms邊界可完成轉彎；確認不足或確認完成時間超過原搜尋期限仍故障。原速度、停車開關與根目錄XML／INO不變。完整報告見docs/SIMULATION_ENV_2026-11-03.zh-TW.md。

## Isolated ground-backing hypothesis (2026-11-04)

Use `reconstructed_course_ground.json` only with `junction_context_ground_mission.json`; the original course/profile remain separate. See [support/legality audit](../docs/GROUND_SUPPORT_2026-11-04.zh-TW.md) and [receipt](../docs/simulations/2026-11-04-ground-support.json). Bounds, height and material remain inferred. The backing does not add sensor paint or legalize wheel departure.

Example known diagnostic (choose a fresh output directory):

```powershell
py -3.11 tools/run_course.py --course simulation/reconstructed_course_ground.json --source firmware/experiments/junction_context/junction_context.ino --candidate-profile simulation/junction_context_ground_mission.json --plant-json simulation/plant_high_torque_hypothesis.json --probe-seed 2026110701 --diagnostic-limit-s 240 --output build-output/my-ground-701
```

Known711/714 pass209/209; known701 remains195/209. Never pool these with legacy results or call them unseen qualification. Profile transport changes only uniform CRLF/LF after learning, with exact normalized bytes/policy equality and retained raw receipts. Further training still requires matching raw teacher identity; finish learning before terminal transport, or collect new teachers on the destination course. No hardware operation is implied.
