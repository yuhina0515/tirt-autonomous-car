import type { Metadata } from "next";
import Replay from "./Replay";
import styles from "./Replay.module.css";

export const metadata: Metadata = {
  title: "TIRT 自駕車專案 · 互動模擬",
  description: "完整賽道模擬回放、逐段策略、感測器與馬達狀態，以及兩層控制的驗證進度。",
  alternates: { canonical: "/projects/tirt" },
};

export default function TirtProject() {
  return <article className={styles.project}>
    <header className={styles.heading}>
      <span className={styles.eyebrow}>TIRT AUTONOMOUS CAR / 2026.11.07</span>
      <h1>自駕車，從起點到終點</h1>
      <p>11/7 最後練習版本、感測邏輯與驗證安排，以及先前模型的互動回放。</p>
    </header>
    <section className={styles.release} aria-label="兩次全白練習候選版">
      <span className={styles.eyebrow}>11/7 09:00–11:00 最後練習</span>
      <h2>兩次全白 R3.2 · 20 秒練習版</h2>
      <p>第一次五顆全白立即停車，連續確認 30 ms 後等待 20 秒；暫停專用低速離台：等待結束仍全白時以原生起步 PWM 100 前進，其餘立即正常循線。外側黑、中央有效窄線連續 100 ms 才重新接受標記；1.5 秒逾時仍保留。第二次確認五顆全白後停止，直到重設。</p>
      <nav className={styles.links} aria-label="練習版本下載">
        <a href="/downloads/files/tirt-two-marker-20261107-r3-2/race_two_marker.ino" download>下載 R3.2 主程式</a>
        <a href="/downloads/files/tirt-two-marker-20261107-r3-2/race_capture.ino" download>下載 R3.2 行駛回傳版（會驅動馬達）</a>
        <a href="/downloads/files/tirt-native-20261104/native_car.ino" download>下載 native_car 回復版本</a>
      </nav>
      <p>單一 INO，不需額外函式庫。Arduino Nano → ATmega328P (Old Bootloader)。先架空車輪；D12 按鈕先放開再按下啟動，運行中再按一次停止，須重設才能重啟。</p>
      <p>控制與回傳測試通過；主程式 Nano 編譯 Flash 8,754 bytes／全域 RAM 294 bytes。請先置中、左偏、右偏各重測 10 次離台，腳本不代表實車成功率。尚未實車驗收；「全白只會遇到兩次」是待現場驗證的策略假設。須確認 F 點升降台、離台循線、額外白區與終點計時器是否真正觸發。</p>
      <p>R3.1 已修正全白前後的不確定計時與窄線恢復連續性，195 項測試通過，Opus 5.5 medium 複核完成；R3.2 將平台等待設為 20 秒，請確認平台停穩後才離台。今天預設 useSlowExit=false；練習需要比較時，改 true 可恢復 R2。回傳版與主程式採相同控制，D12 啟動後正常行駛，以 USB 115200 回傳二進位資料；先開記錄再啟動，緩衝區滿會略過封包，避免阻塞控制。</p>
      <nav className={styles.links} aria-label="練習準備資料">
        <a href="https://github.com/yuhina0515/tirt-autonomous-car/blob/f8965d7/docs/prepractice-2026-11-07/REVIEW.zh-TW.md" target="_blank" rel="noreferrer">練習前邏輯、優先度與停車判讀 ↗</a>
        <a href="https://github.com/yuhina0515/tirt-autonomous-car/blob/92be47e/docs/race-two-marker-2026-11-06/TELEMETRY.md" target="_blank" rel="noreferrer">行駛回傳與 CSV 操作 ↗</a>
        <a href="https://github.com/yuhina0515/tirt-autonomous-car/blob/92be47e/docs/race-two-marker-2026-11-06/LOGIC.zh-TW.md" target="_blank" rel="noreferrer">32 種感測排列與狀態邏輯 ↗</a>
        <a href="https://github.com/yuhina0515/tirt-autonomous-car/blob/92be47e/docs/race-two-marker-2026-11-06/PRACTICE.zh-TW.md" target="_blank" rel="noreferrer">09:00–11:00 練習檢查表 ↗</a>
      </nav>
    </section>
    <h2 className={styles.archiveHeading}>11/5 模型回放 · 非本次候選版</h2>
    <p className={styles.caption}>下方保留既有模型供分析；F 點升降台位置與連接仍待確認，回放沒有套用本次兩次全白／20 秒任務，不能代表新版本已跑完正式賽道。</p>
    <Replay />
    <section className={styles.notes} aria-label="專案現況與驗證界線">
      <div><h2>目前的控制架構</h2><p>本次 race_two_marker 將原生運動控制與兩次全白任務分開；native_car 保留作回復。較早的 layered_car 預設空路線僅供循線練習，尚未完成整圈任務。</p><p>這裡完整圈採用既有 junction_context 實驗策略。它不是已部署的車上版本，也不是新兩層控制已完賽。</p></div>
      <div><h2>已驗證與待驗證</h2><p>實際 C++ 核心與物理 ADC 重播核對通過。參考圈另經凍結來源獨立稽核，10 項模型檢查通過；使用已知種子，並非盲測或正式賽道驗收。</p><p>賽道比例、路線連接及車輛動力仍有假設。白字干擾、正式斷線、滑移、翻覆與車上終點停車尚未完整驗證。</p></div>
      <div><h2>升降時間的差異</h2><p>本次候選版等待 20 秒。回復版本保留祥儀練習時的 23.35 秒；下方舊模型使用 31 秒，模型機構移動約 26.671 秒。這三個設定屬於不同版本，不能混為實車結論。</p></div>
    </section>
    <nav className={styles.links} aria-label="專案延伸資料">
      <a href="/downloads">程式常駐下載</a>
      <a href="/tirt">舊版參數實驗室（不同模型）</a>
      <a href="https://github.com/yuhina0515/tirt-autonomous-car/blob/cfe167dc7abd4e254b8660902cb10c8aebdf5e29/docs/start-finish-2026-11-05/REPORT.zh-TW.md" target="_blank" rel="noreferrer">完整分析報告 ↗</a>
    </nav>
  </article>;
}
