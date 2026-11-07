# 地面支撐分離與 V 彎診斷（2026-11-04）

這次新增獨立的 ground-backing 模型假說，未修改原模型、道路合法性、控制器或預設候選。地板可以承重，不代表輪子可以離開道路。已知 701 的支撐缺口被分開後仍未完賽，下一項控制工作是處理短暫方向提示與後續誤差反向，不能把問題全歸因於地板。

## 來源與模型界線

2026-11-04 從官方活動頁重新下載指定組中文規則，1,389,853 bytes，SHA-256 `8c42f4cf04e1d50424f92bc86fbb38ced78f3743b19384695de8e36485d21ef8`，與已保存 PDF 相同。已閱讀並目視檢查 PDF 第5～7頁：圖面與 V 彎照片提供彩色底面的線索，但不能證明底面公尺範圍、高度、材質或實車摩擦。這不是正式完整賽道驗收。

`simulation/reconstructed_course_ground.json` 另宣告像素矩形 `[76,809,1024,1074]`、高度0，沿用原比例假設。實體 contact 優先採道路，否則只有矩形內且在原高度容差內才採地面。道路合法性使用原 painted-road contact；白線反射、V 例外、方向走廊、機構、動力與輪跡容差未放寬。仍採中心單點承重，沒有完整輪胎／底盤支撐、側滑或傾覆模型。

原 `course_world.py`、`simulation_model.py`、原路線及原 profile 保留。舊世界711重播完整 trace SHA 與前次一致：`16d452909240c9a910dcdacae15d77f561e2ebc377f40e4b08e4742036de4720`。新增環境 dispatcher 對舊 profile 僅允許已審查的固定版本，避免未來 wrapper 改變卻沿用舊模型身分。

## 訓練與換行

地面版本重新產生701～705五份 lift teachers，全部通過來源與前綴重播；再產生五份 post-lift teachers。四個 junction 目標仍是 `R L W L R L R L W -> R`，701沒有到達目標，保留拒絕記錄；最終 profile 重播全部五份 teacher 的目標前實際 ADC、核心狀態與輸出。

原始生成 course 為 CRLF；Git 發布為 LF。`transfer_course_newlines.py` 只接受 uniform CRLF/LF，要求正規化位元組與解析 JSON 完全相同，政策 payload 不變，明確保存舊／新 raw SHA 與工具收據。凍結 teacher、trace 與 manifest 不改寫。這是學習完成後的 terminal transport；已轉換 profile 不能跳過 learner 的原始 teacher course 身分檢查。若還要學習，先在原 course 完成，或在新 course 收集新 teachers。

匹配 profile：`simulation/junction_context_ground_mission.json`。實際 staged 程式 SHA 仍是 `054e609023286c2b9955623ca1fd931e3a0a68d73cd3f524d133b221ddc25973`，與前次相同；沒有新韌體控制變更。

## 地面版本完整診斷

| 已知種子 | 結果 | 過門 | 獨立檢查 |
| --- | --- | --- | --- |
| 701 | 189.450s，車身失去覆線 | 195/209 | 失敗；首次方向走廊失敗189330ms |
| 711 | 完成；模擬219.320s | 209/209 | 10項全部通過 |
| 714 | 完成；模擬221.195s | 209/209 | 10項全部通過 |

三份軌跡都通過實際核心重播及物理ADC來源重生。此表僅屬地面版本，不能和原模型湊成功次數，也不是未見驗證或五連跑。最終110項Python測試通過；profiled Nano重新編譯9772 bytes Flash／251 bytes全域RAM，僅為靜態編譯數字。

## 701 的可重現因果

原 teacher 最早方向判定失敗189330ms，189430ms失去物理支撐。地面 teacher 最早失敗仍189330ms，189450ms失去車身覆線，195/209；支撐分離只增加20ms，並未使它過關。

右側 hint 只在188905與188910ms成立，188915ms消失，未滿10ms確認。188975ms普通追線誤差把方向從右改左；189015ms進入F0，189020ms起輸出100/230直到失敗。

189330ms相鄰路段194／195的投影距離均為61.59994mm，超過方向資格60mm，因此沒有 eligible route projection。位移沿 incoming 切線仍為+1.43528mm，沿 outgoing 為−1.82045mm。這是現行規則下的方向走廊離開，不能單獨稱為已證明逆向；`direction_and_layer=false` 也包含未完成過門。裁判規則保留。

下一個隔離實驗應驗證有期限的方向預告，並要求後續離線／同側返回確認；先檢查五份 teacher 的誤觸位置，再重新建立來源綁定 profile。不能只縮短10ms、延長800ms、使用位置 oracle 或改裁判來湊成功。

## Squad 審查

三位獨立唯讀審查者使用工作樹外快照，分別負責支撐／合法性、profile／換行及701控制原因。接受並修正 legacy dispatcher 未被舊 profile 綁定的風險；重播確認 hint 與方向走廊數值。支撐審查未發現功能缺陷，另以1000組姿態比較合法性與 seeded ADC 一致。保留單點支撐與底面推論限制。

「轉換後 lift profile 無法混用原 raw teachers 繼續 junction 學習」維持 fail-closed，明確記錄為受限流程，不自動放寬身分檢查。此輪沒有更改原始 evidence、主程式、rollback 或穩定標籤。

完整診斷、軟體檢查及機器收據見 [ground support receipt](simulations/2026-11-04-ground-support.json)。正式幾何／校正、未見五跑、實車驗收與 onboard finish-stop 尚未完成；741～745仍保留，沒有燒錄、馬達操作或合併。
