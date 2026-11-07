**結論：兩個修正都合適且夠小，我沒有發現回歸。** 這次只讀了這兩個檔案並做推演，沒有實跑測試。

**Fix1（`controller-r3-1.h:57`）**
- 只有 `useSlowExit=false` 會走到這裡，因為慢速模式已在第 54 行 return。
- 第 48 行的 1500ms 期限先於第 57 行判斷，所以全白無法延長期限。
- **取捨：** 出場時一個全白 tick 就會重置 800ms 預算。例如失線 700ms、全白 1 tick、再失線 700ms，車不會報 Uncertain，可能繼續低速前進或 pivot，直到 1500ms 才停。這段時間有上限，比誤停可接受，但要知道 Uncertain 在出場階段會變弱。

**Fix2（第 60 行）**
- `uncertain` 與 `uncertainAt` 都保留，白色短暫閃現不會延長預算。
- `recovering` 被清除後，要重新連續看到窄線 30ms 才算恢復。
- 第 59 行的 `phase!=ExitLift` 現在等於恆真，但無害。
- 確認全白時，第 64 行清除 `uncertain`，第 60 行也已清除 `recovering`，不會把殘留狀態帶進等待。
- **行為變化：** 恢復變嚴格，只會讓車更早停，不會更晚停。

**測試（`prepractice_priority.cpp`）**
- 第 39–47、49–56 行的時間序列推演正確，修正前後的結果確實不同。
- **缺口 1：** 沒有測試全白與失線交替時，是否在 exit+1500 觸發 `ExitTimeout`。這是 Fix1 的主要安全依據，建議補上，加幾行即可。
- **缺口 2：** 測試 include 的是 `firmware/race_two_marker/controller.h`。請確認它與 `controller-r3-1.h` 內容相同，再採信測試結果。
