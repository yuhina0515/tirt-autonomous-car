# TIRT離線模擬環境

在完整團隊庫執行`py -3.11 tools/run_simulation.py`，再開啟build-output/simulation/index.html。需要Windows／MSVC（或Visual Studio Community）；模擬本身只用Python標準函式庫，不需要Arduino板、CAGEBOT、Node或網路。首次尚未安裝Python／MSVC時需自行準備。Arduino目標編譯另外使用既有Compile-Native.ps1與公開LED函式庫。

scenarios.json可設定物理參數及情境。預設比較00e0db0原生移植版與目前工作目錄：14種情境×3組參數×兩版，共84次。包含直道、左右60／90／120度改向、寬白V彎、短／長缺口、合成T形文字、窄線雜訊及反向ADC極性；三組參數為名目、低電量／輪差、低抓地／延遲。基準必須存在於本機Git，可用--baseline改變。路線圖形不是正式TAIWAN圖，物理參數不是實車量測值。

每次產生結果JSON、10 ms軌跡CSV與獨立HTML回放。HTML可離線播放、拖曳時間及切換案例；車形只是位置／方向示意。`--replay-only`可由已保存JSON／CSV重建HTML，不重跑控制程式。更改情境設定後應完整重跑，不可將新設定混用舊結果。

驗證：`py -3.11 -m unittest discover -s tests -v`。有新控制行為時，保留舊版對照並新增定向測試，不要求所有物理壓力案例都「到達」。反向ADC案例刻意展示極性錯誤的風險；三白、白字與關卡仍可能有相同觀測。不能把到達數當作實車成功率。

本輪修正：已在搜尋期限內連續確認15 ms的回線，在800 ms邊界可完成轉彎；確認不足或確認完成時間超過原搜尋期限仍故障。原速度、停車開關與根目錄XML／INO不變。完整報告見docs/SIMULATION_ENV_2026-11-03.zh-TW.md。
