"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import styles from "./Replay.module.css";

const BASE = "/projects/tirt/replay-20261105";
const PHASES = [
  ["起步與中央入口", "中央三顆感測器連續位置 PD，偏差增加時降速。"],
  ["第一立體交疊", "循線通過上下坡；圖面重疊不代表同一平面的岔路。"],
  ["中央與左側蛇形", "連續轉向與短暫方向記憶，回線確認及失線時間均有限。"],
  ["第二立體區", "交叉白線先視為觀測，不能直接判定升降台。"],
  ["左側長直與圓彎", "持續修正位置，看到中央線不代表前方必定直行。"],
  ["第三立體區與蹺蹺板", "循線通過負載變化；牽引力與不倒退仍是模型假設。"],
  ["上方連續 U 形彎", "以 PD、降速與有限時間方向恢復通過連續彎。"],
  ["第四立體區與升降台", "參考策略以事件歷史識別，等待 31 秒後確認窄線離台。"],
  ["升降後回程", "保留選定方向並確認回線，避免普通交叉改寫任務。"],
  ["TAIWAN 急彎與終點", "特定事件前綴選右；沿 A 頂點完整繞行，裁判確認終點越線。"],
];
type Row = Record<string, number>;
type Result = { outcome: string; elapsed_s: number | null; simulation_seconds: number;
  gates_crossed: number; gates_required: number; gate_events: { ms: number; station_m: number }[];
  independent_checks: Record<string, boolean>; first_violation: string | null; first_violation_ms: number | null;
  trace_sha256: string; native_trace_replay_verified: boolean; physical_sensor_origin_verified: boolean };
type Run = { id: string; label: string; rows: number[][]; phaseTimes: (number | null)[]; result: Result };
type Payload = { schema: number; columns: string[]; image: string; runs: Run[];
  points: [number, number][]; raised: { start_vertex: number; end_vertex: number }[];
  dimensions: { width_px: number; height_px: number }; assumptions: Record<string, number>;
  seed: number; courseHash: string; phases: { start: number; end: number; name: string }[] };

export default function Replay() {
  const [data, setData] = useState<Payload | null>(null), [error, setError] = useState("");
  const [selected, setSelected] = useState(0), [ms, setMs] = useState(0), [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(4), [showMap, setShowMap] = useState(true), [showRoute, setShowRoute] = useState(true);
  const [zoom, setZoom] = useState(1), [mapReady, setMapReady] = useState(false), [mapError, setMapError] = useState(false);
  const canvas = useRef<HTMLCanvasElement>(null), source = useRef<HTMLImageElement | null>(null);
  useEffect(() => {
    const abort = new AbortController();
    fetch(`${BASE}/replay.json`, { signal: abort.signal }).then(r => {
      if (!r.ok) throw Error(`資料讀取失敗（${r.status}）`);
      return r.json();
    }).then((p: Payload) => {
      if (p.schema !== 1 || p.runs.length !== 2 || p.runs.some(r => !r.rows.length)) throw Error("回放資料格式不符");
      setData(p);
    }).catch(e => { if (!abort.signal.aborted) setError(String(e)); });
    return () => abort.abort();
  }, []);
  useEffect(() => {
    if (!data) return;
    const image = new Image(); source.current = image;
    image.onload = () => setMapReady(true);
    image.onerror = () => setMapError(true);
    image.src = `${BASE}/${data.image}`;
    return () => { image.onload = null; image.onerror = null; };
  }, [data]);
  const run = data?.runs[selected];
  const rows = useMemo<Row[]>(() => data && run ? run.rows.map(values =>
    Object.fromEntries(data.columns.map((key, i) => [key, values[i]]))) : [], [data, run]);
  const end = rows.at(-1)?.ms ?? 0;
  // Find the preceding recorded frame, preserving the exact final timestamp.
  let low = 0, high = rows.length - 1;
  while (low < high) { const mid = Math.ceil((low + high) / 2); if (rows[mid].ms <= ms) low = mid; else high = mid - 1; }
  const index = low, row = rows[index];
  const gates = run?.result.gate_events.filter(g => g.ms <= ms).length ?? 0;
  const phase = run?.phaseTimes.reduce<number>((best, time, i) => time !== null && time <= ms ? i : best, 0) ?? 0;
  useEffect(() => {
    if (!playing) return;
    let frame = 0, last = performance.now(), accumulated = 0;
    const tick = (now: number) => {
      // Hidden tabs pause; playback speed changes the cursor, not the physics.
      const delta = document.hidden ? 0 : Math.min(100, now - last); last = now;
      accumulated += delta * speed;
      if (accumulated >= 40) { const step = accumulated; accumulated = 0; setMs(t => Math.min(end, t + step)); }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [playing, speed, end]);
  useEffect(() => { if (ms >= end && end > 0) setPlaying(false); }, [ms, end]);
  useEffect(() => {
    if (!data || !row || !canvas.current) return;
    const ctx = canvas.current.getContext("2d"); if (!ctx) return;
    const { width_px: w, height_px: h } = data.dimensions, scale = data.assumptions.metres_per_pixel;
    const xy = (v: Row): [number, number] => [v.x / scale, h - v.y / scale];
    const line = (points: [number, number][], color: string, width: number) => {
      ctx.beginPath(); points.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
      ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke();
    };
    ctx.fillStyle = "#f5f5f2"; ctx.fillRect(0, 0, w, h);
    if (showMap && mapReady && source.current) ctx.drawImage(source.current, 0, 0, w, h);
    if (showRoute) {
      ctx.globalAlpha = .75; line(data.points, "#3674dd", 4);
      data.raised.forEach(r => line(data.points.slice(r.start_vertex, r.end_vertex + 1), "#ad66cb", 6));
      ctx.globalAlpha = 1;
    }
    line(rows.slice(0, index + 1).map(xy), "#efad32", 5);
    const [x, y] = xy(row), length = data.assumptions.body_length_m / scale, width = data.assumptions.body_width_m / scale;
    ctx.save(); ctx.translate(x, y); ctx.rotate(-row.yaw);
    ctx.fillStyle = row.turnFault ? "#d72c49" : "#087f9c"; ctx.strokeStyle = "white"; ctx.lineWidth = 3;
    ctx.fillRect(-length / 2, -width / 2, length, width); ctx.strokeRect(-length / 2, -width / 2, length, width);
    ctx.beginPath(); ctx.moveTo(length / 2 + 9, 0); ctx.lineTo(length / 2 - 3, -6); ctx.lineTo(length / 2 - 3, 6); ctx.closePath(); ctx.fillStyle = "#ffcf5e"; ctx.fill();
    ctx.restore();
  }, [data, row, rows, index, showMap, showRoute, mapReady]);
  function seek(time: number) { setPlaying(false); setMs(Math.max(0, Math.min(end, time))); }
  if (error) return <div className={styles.error} role="alert">{error}。請重新整理頁面重試。</div>;
  if (!data || !run || !row) return <div className={styles.loading} role="status">正在載入兩組模擬軌跡…</div>;
  const finished = run.result.outcome === "finished";
  const checks = Object.values(run.result.independent_checks).filter(Boolean).length;
  const heightPoints = rows.filter((_, i) => i % 10 === 0 || i === rows.length - 1).map(r => `${r.ms / end * 300},${70 - r.z / .6 * 60}`).join(" ");
  return <section className={styles.player} aria-label="完整賽道互動模擬回放">
    <div className={styles.topline}><div><span className={styles.eyebrow}>完整賽道 / 210 路段</span><h2>互動模擬回放</h2></div><span className={styles.badge}>已計算軌跡 · 非即時重算</span></div>
    <p className={styles.caption}>播放、拖曳或跳到指定階段，觀察當下的車身、感測器與馬達。兩組使用同一推定賽道及已知種子；調整播放速度不會改變模擬結果。</p>
    <div className={styles.tabs} role="group" aria-label="選擇控制版本">
      {data.runs.map((r, i) => <button key={r.id} aria-pressed={selected === i} onClick={() => { setSelected(i); setMs(0); setPlaying(false); }}>{r.label}<small>{r.result.gates_crossed} / 209 檢查點</small></button>)}
    </div>
    <div className={styles.workspace}>
      <div className={styles.mapColumn}>
        <div className={styles.mapTools}>
          <label><input type="checkbox" checked={showMap} onChange={e => setShowMap(e.target.checked)} />原始圖面</label>
          <label><input type="checkbox" checked={showRoute} onChange={e => setShowRoute(e.target.checked)} />推定路線</label>
          <label>縮放 <select aria-label="地圖縮放" value={zoom} onChange={e => setZoom(+e.target.value)}><option value={1}>100%</option><option value={1.5}>150%</option><option value={2}>200%</option></select></label>
        </div>
        {mapError && <p role="status">原始圖面載入失敗；仍可查看推定路線與軌跡。</p>}
        <div className={styles.viewport}><canvas ref={canvas} width={data.dimensions.width_px} height={data.dimensions.height_px} style={{ width: `${zoom * 100}%` }} aria-label="車子在推定賽道上的軌跡，黃色箭頭為車頭">賽道視覺回放；各時刻數值列在狀態面板。</canvas></div>
        <div className={styles.legend}><span>● 黃：行駛軌跡</span><span>● 藍：推定路線</span><span>● 紫：高架路段</span></div>
        <div className={styles.transport}>
          <button className={styles.primary} onClick={() => { if (ms >= end) setMs(0); setPlaying(p => !p); }}>{playing ? "暫停" : ms >= end ? "重新播放" : "播放"}</button>
          <button onClick={() => seek(0)}>回到起點</button>
          <button onClick={() => seek(ms - 1000)} aria-label="後退一秒">−1s</button><button onClick={() => seek(ms + 1000)} aria-label="前進一秒">+1s</button>
          <label>速度 <select aria-label="播放速度" value={speed} onChange={e => setSpeed(+e.target.value)}>{[.25, 1, 2, 4, 8, 16].map(n => <option key={n} value={n}>{n}×</option>)}</select></label>
          <button onClick={() => seek(end)}>跳到結果</button>
        </div>
        <label className={styles.timeline}><span>模擬時間 <strong>{(ms / 1000).toFixed(2)} / {(end / 1000).toFixed(2)} 秒</strong></span><input aria-label="回放時間" type="range" min={0} max={end} step={5} value={ms} onChange={e => seek(+e.target.value)} /></label>
        <div className={styles.chart}><span>物理高度隨時間（公尺）</span><svg viewBox="0 0 300 80" role="img" aria-label={`當前物理高度 ${row.z.toFixed(3)} 公尺`}><polyline points={heightPoints} fill="none" stroke="#76b9e7" strokeWidth="1.5" /><line x1={ms / end * 300} x2={ms / end * 300} y1="0" y2="80" stroke="#efad32" /></svg></div>
      </div>
      <aside className={styles.panel}>
        <div className={styles.phaseCard}><span className={styles.eyebrow}>目前階段 {phase + 1} / 10</span><h3>{PHASES[phase][0]}</h3><p>{PHASES[phase][1]}</p></div>
        <div className={styles.stats}>
          <div><span>目前檢查點</span><strong>{gates} <small>/ 209</small></strong></div>
          <div><span>左右 PWM</span><strong>{row.left} / {row.right}</strong></div>
          <div><span>物理高度</span><strong>{row.z.toFixed(3)} <small>m</small></strong></div>
          <div><span>控制狀態</span><strong>{row.turnFault ? "故障鎖停" : ms >= end ? "回放結束" : row.liftState === 1 ? "升降等待" : "行駛觀測"}</strong></div>
        </div>
        <h3>感測器原始值</h3><div className={styles.sensors}>{["a5", "a4", "a3", "a2", "a1"].map(key => <div key={key}><label>{key.toUpperCase()}</label><div className={styles.sensorTrack}><i style={{ height: `${Math.min(100, row[key] / 1023 * 100)}%` }} /></div><strong>{row[key]}</strong></div>)}</div>
        <p className={styles.caption}>ADC 0–1023；此模型低值偏白線。A4／A3／A2 為主要循線感測。</p>
        <dl className={styles.telemetry}><dt>左右輪速度</dt><dd>{row.vl.toFixed(3)} / {row.vr.toFixed(3)} m/s</dd><dt>車身俯仰</dt><dd>{(row.pitch * 180 / Math.PI).toFixed(1)}°</dd><dt>蹺蹺板角度</dt><dd>{(row.seesaw_theta * 180 / Math.PI).toFixed(1)}°</dd><dt>升降物理階段</dt><dd>{["等待／未啟動", "移動中", "完成"][row.lift_phase] ?? row.lift_phase}</dd></dl>
        <div className={finished ? styles.pass : styles.fail}><strong>整次結果：{finished ? "模型完整圈完成" : "Signal 故障停止"}</strong><p>{finished ? `起終點計時 ${run.result.elapsed_s?.toFixed(3)} 秒；${checks}/10 項模型檢查通過。` : "103.305 秒停止，82/209 檢查點。分裂線形沒有可用任務方向，達到不確定期限後鎖停。"}</p><small>{finished ? "起點越線前的時間不計入起終點成績。" : "此版本尚未配置路線，參考圈的成功不代表它已完賽。"}</small></div>
      </aside>
    </div>
    <div className={styles.phaseHeader}><h3>沿路十個階段</h3><span>選擇階段跳轉；灰色表示此案例未到達</span></div>
    <div className={styles.phases}>{PHASES.map(([title, response], i) => <button key={title} disabled={run.phaseTimes[i] === null} aria-pressed={phase === i} onClick={() => seek(run.phaseTimes[i] ?? 0)}><span>{String(i + 1).padStart(2, "0")}</span><strong>{title}</strong><small>{response}</small></button>)}</div>
    <details className={styles.evidence}><summary>資料來源、重播檢查與下載</summary><p>2026-11-05 已知診斷種子 {data.seed}。兩組均核對真實 C++ 控制輸出及物理感測器來源。畫面每 50 ms 取樣，保留最後一筆；判定沿用完整原始軌跡，沒有用降採樣資料重新計分。</p><p>這是離線模擬的互動回放，不提供瀏覽器內 C++ 重算。舊版參數實驗室使用另一套模型，結果不可直接比較。</p><p>軌跡 SHA-256：<code>{run.result.trace_sha256}</code></p><a href={`${BASE}/replay.json`} download>下載回放資料</a><a href={`${BASE}/scenarios.json`} download>下載 210 路段分析</a></details>
  </section>;
}
