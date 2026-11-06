# 感測掃描速率：理論與實測界線

Nano ATmega328P在16MHz、ADC預分頻128時，ADC時脈125kHz。一般轉換13個ADC週期，即104微秒；五顆約520微秒，只計轉換的上限約1923組/秒。analogRead多工切換、函式、控制和UART中斷還會增加時間。首次轉換較長，通道取樣不是同時發生。

Microchip建議完整解析度的ADC時脈50–200kHz；16MHz下改分頻64會變250kHz，因此本次不超頻ADC。參考：https://developerhelp.microchip.com/xwiki/bin/view/products/mcu-mpu/8-bit-avr/getting-started/8-bit-avr-adc/ 及 https://ww1.microchip.com/downloads/en/devicedoc/atmel-7810-automotive-microcontrollers-atmega328p_datasheet.pdf 。

目前循線loop沒有delay，五顆每次控制前依序讀取。既有的30ms標記確認／100ms離區確認屬於防抖條件，不是掃描間隔；不可為提高反應率一起刪除。

真正的穩定最高掃描率尚未量得：缺少底部感測器型號、類比輸出頻寬與實測資料。高ADC取樣率不代表光學感測器提供同頻寬的新資訊。來源阻抗、多工殘留、USB或電池供電、馬達噪聲、門檻餘裕都影響有效讀值。

回傳版正常行駛，採集全速控制迴圈中的原始值、五顆掃描耗時與迴圈間隔，回傳降採樣到50Hz；不可把50Hz誤稱控制頻率，每筆另外含所有掃描累計的區間最大耗時與掃描數；封包若在接收端遺失仍可能遺失尖峰，不能宣稱完整觀察。先分別量靜態黑／白、邊緣移動、馬達運行，重複確認門檻不抖動與方向反應。USB序列埠在啟動前開好，避免DTR重置行進中的車子；D0/D1外接模組是否衝突須核對。

應比較無回傳與開回傳的實測迴圈耗時，再決定是否有必要改成更複雜的ADC排程。未接實車前僅提供理論估算與量測工具，不宣稱達成穩定最高掃描速率。
