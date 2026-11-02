# 2026-11-03 原生Arduino控制核心移植

## 交付與來源

使用者明確同意「沿用現有硬體，建立原生Arduino控制核心，先維持行為再精簡」。新的主要維護入口為[firmware/native_car/native_car.ino](../firmware/native_car/native_car.ino)與同資料夾controller.h，不再需要CAGEBOT程式產生器或moto函式庫。

移植基準是f3501be的根目錄car.ino／car.xml，兩份原始主檔保留，作可編輯積木與回復參考。本次沒有覆寫它們、移動正式版標籤或燒錄車子。原生核心不聲稱能反向轉成積木。build.py／config.json及既有temporal候選不變。

## 精簡的內容

| 原來 | 原生版 |
|---|---|
| 1362行匯出INO | 69行Arduino讀寫＋353行核心，合計422行；沒有把核心藏到別處只報69行 |
| 大量可變設定、迴圈暫存全域變數及int旗標 | constexpr設定、明確寬度的整數、bool、Motion／Lift／Fault列舉；elapsed等由時間戳局部計算 |
| 多處四個馬達腳位的輸出鏈 | 核心輸出Wheels；唯一writeWheels處理腳位與正反轉 |
| 控制、GPIO、LED、字串混合 | 純C++核心tick(now, adc)與Arduino介接分離，可重播同一輸入 |
| String組字與十六進位顏色解析 | 固定RGB、Flash序列字串；預設除錯關閉時不開UART |
| CAGEBOT moto_NeoPixel | 公開Adafruit_NeoPixel，預設同樣使用D13、兩顆、第一顆綠／藍 |

原始碼位元組由40997降至21729；行數約減69%。這是程式碼與維護負擔的縮減，真正Flash／RAM另以目標編譯衡量。

## 實際Arduino目標編譯

所有比較使用同一台機器、Arduino CLI1.5.1、Arduino AVR Boards1.8.8、相同Nano Old Bootloader FQBN：arduino:avr:nano:cpu=atmega328old。沒有連線板子，也未確認目前車上的MCU／Bootloader身分。

| 編譯項目 | Flash bytes | 全域RAM bytes |
|---|---:|---:|
| f3501be原始匯出INO＋本機原有Motoshare函式庫 | 17982 | 801 |
| 同一匯出程式，只將LED類別／include換成相同Adafruit函式庫作控制比較 | 17072 | 689 |
| 原生版，LED開啟、DEBUG_SERIAL=0（預設） | 8662 | 203 |
| 原生版，LED開啟、DEBUG_SERIAL=1 | 10146 | 386 |

相對實際原版，預設Flash約少51.8%、全域RAM約少74.7%。即使統一LED函式庫，Flash仍約少49.3%、全域RAM少70.5%。因此縮減不只是換LED函式庫；但數據涵蓋整個程式、型別、常數折疊及預設UART關閉，不能全部歸因於某一項重構。

[建置索引與來源／application HEX雜湊](native-build-2026-11-03.json)記錄這次實際編譯輸入與結果。

Nano上限為Flash30720、SRAM2048 bytes。203是靜態全域用量，不包括完整執行期stack／heap峰值；NeoPixel會配置像素緩衝。未量測實車迴圈時間、輪速、扭矩或電池消耗，不能由Flash縮小宣稱速度提升幾倍。

公開LED依賴固定為[Adafruit NeoPixel1.15.3](https://github.com/adafruit/Adafruit_NeoPixel/tree/1.15.3)，本機取得的提交為67f2ed09e9dd755ab1f606ec5940c50af52afae3。[Arduino CLI編譯參數](https://arduino.github.io/arduino-cli/latest/commands/arduino-cli_compile/)用於指定板型、獨立build路徑與library。原廠函式庫只讀作本機原版比較，不納入Git或交付包。

## 行為維持與驗證

預設保持目前的速度、ADC門檻、A4/A3/A2正常控制、A5/A1方向輔助、開機按鈕、800 ms搜尋、120 ms缺口、15 ms收線確認、寬白恢復、升降等待／離台、終點條件、兩個停車開關0與180秒總期限。

四組差異測試把完全相同的時間戳與原始ADC逐步送進保留INO與原生介接程式，比對左右輪命令及13個可對照觀測欄位；故障行號不是原生版契約，改由Fault列舉表示原因。涵蓋直道階段、修正、左右搜尋／回線、外側確認與探查、三白、升降、終點、缺口邊界、ADC閾值附近、100段固定種子混合序列、32位毫秒計時溢位與180秒期限。比對通過不代表測遍所有輸入。

額外純C++核心測試不需要Arduino／CAGEBOT，覆蓋主要狀態轉移、回線邊界及計時溢位，已加入Linux CI。29項Python既有／新增測試在Windows Python3.11通過。桌面介接仍模擬GPIO、LED與時間；Arduino目標編譯另行完成，兩者不能互相替代。

使用相同的12套假設物理參數×11個情境（132組／版）比較，兩版皆到達94、故障5、逃離14、逾時19；四個到達案例曾越出假設道路輪子邊界，不能算合法完賽。另比對逐案結果及名目案例每步輪命令／狀態，見[機器可讀結果](simulations/2026-11-03-native-migration.json)。物理模型仍未以這台車校正，不是實車成功率。

132組逐案指標與最終狀態全部相等；11組名目案例合計5541筆10 ms軌跡逐欄相等，僅排除不具有跨版本意義的firstFaultLine。原始感測、控制核心與介接均由實際來源編譯，不另寫一份控制演算法來冒充比對。

原生來源是INO＋header共同決定，模擬source_sha256以兩檔內容加明確分隔符計算；建置索引另列兩檔各自SHA-256，不能只核對69行介接程式就認定核心版本相同。

## 編譯、模擬與回復

在完整團隊Git庫執行：

```powershell
py -3.11 -m unittest discover -s tests -v
pwsh -File tools/Compile-Native.ps1 -NeoPixelLibrary <Adafruit_NeoPixel根目錄>
python tools/physics_sim.py --samples 12 --seed 20261103 --models simplified --profiles unchanged --reference-source car.ino --candidate firmware/native_car/native_car.ino --output build-output/native-migration/physics-parity
```

Arduino IDE直接開啟native_car資料夾內的native_car.ino，controller.h須在旁邊，安裝上述公開函式庫即可，不需要啟動CAGEBOT。詳細步驟見[原生程式說明](../firmware/native_car/README.md)。CLI預設不變更安裝的板卡、函式庫或全域設定；Compile-Native.ps1僅編譯，沒有upload命令。

E:/Projects/XiangyiRobotDreamFactory/self-driving_car/firmware/native_car為本機來源副本；根目錄car.xml／car.ino仍為f3501be參考版。native-build資料夾保存預設目標的application HEX及建置索引，不包含bootloader HEX；HEX是已編譯候選，並非已上車版本。回復可選保留根目錄主檔或既有v0.4.0快照，切勿用原生版覆蓋舊積木後再期待反向還原。

## 仍保留的限制

本次目標是維持行為的移植，沒有藉重構宣稱修好所有彎道問題。持續F14可能前進至全程上限；無方向的彎道與標記仍可能有相同序列；終點後須直接回中央窄線；升降23.35秒仍沒有機構停止回授。Settings與既有假設沒有量測校正。

介接在開機等待前明確輸出0，較參考版隱含依賴初始腳位狀態更清楚；預設不啟用Serial，除錯開啟時以無String格式輸出ADC／F。公開LED實作的中斷／更新耗時與原廠實作可能不同，未量測實車時序。沒有新增運行中按鈕急停、馬達煞車、反轉死區補償或實車校正，避免在同一輪移植混入新的控制策略。
