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
      <span className={styles.eyebrow}>TIRT AUTONOMOUS CAR / 2026.11.05</span>
      <h1>自駕車，從起點到終點</h1>
      <p>沿著完整賽道看車子如何轉彎、跨越蹺蹺板、等待升降台，也看看新控制架構在哪裡停下。</p>
    </header>
    <Replay />
    <section className={styles.notes} aria-label="專案現況與驗證界線">
      <div><h2>目前的控制架構</h2><p>維護主程式為 native_car，保留可啟動版本作回復。獨立新版 layered_car 把循線／PD 與路線任務拆開；預設空路線僅供循線練習，尚未完成整圈任務。</p><p>這裡完整圈採用既有 junction_context 實驗策略。它不是已部署的車上版本，也不是新兩層控制已完賽。</p></div>
      <div><h2>已驗證與待驗證</h2><p>實際 C++ 核心與物理 ADC 重播核對通過。參考圈另經凍結來源獨立稽核，10 項模型檢查通過；使用已知種子，並非盲測或正式賽道驗收。</p><p>賽道比例、路線連接及車輛動力仍有假設。白字干擾、正式斷線、滑移、翻覆與車上終點停車尚未完整驗證。</p></div>
      <div><h2>升降時間的差異</h2><p>祥儀現場速度較快，因此主程式保留 23.35 秒設定。本頁參考策略使用另一套模型的 31 秒等待；本次機構移動約 26.671 秒，兩者不可混為實車結論。</p></div>
    </section>
    <nav className={styles.links} aria-label="專案延伸資料">
      <a href="/downloads">程式常駐下載</a>
      <a href="/tirt">舊版參數實驗室（不同模型）</a>
      <a href="https://github.com/yuhina0515/tirt-autonomous-car/blob/cfe167dc7abd4e254b8660902cb10c8aebdf5e29/docs/start-finish-2026-11-05/REPORT.zh-TW.md" target="_blank" rel="noreferrer">完整分析報告 ↗</a>
    </nav>
  </article>;
}
