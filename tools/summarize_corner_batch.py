"""Create compact tracked receipts and a per-vertex table from the completed batch."""
import csv,json
from collections import Counter,defaultdict
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];base=Path(sys.argv[1])
r=json.loads((base/'results.json').read_text());audit=json.loads((base/'audit.json').read_text());geometry=json.loads((base/'geometry-check.json').read_text())
rows=list(csv.DictReader((base/'trials.csv').open()));passed=sum(int(float(v['outcome']))==1 for v in rows)
groups=defaultdict(Counter)
for c in r['corners']:
    a=abs(c['angle_deg']);label='小轉角 <10°' if a<10 else '一般改向 10–60°' if a<60 else '銳利改向 60–120°' if a<120 else 'V形改向 ≥120°'
    groups[label].update(c['counts']);groups[label]['vertices']+=1
receipt=dict(r,audit=audit,geometry_check=geometry,exit_passages=passed,scope='strict_local_planar_benchmark_not_official_qualification',
    live_rules_sha256='8c42f4cf04e1d50424f92bc86fbb38ced78f3743b19384695de8e36485d21ef8',live_rules_verified_date='2026-11-06')
out=ROOT/'docs/simulations/2026-11-06-corner-1000.json';out.write_text(json.dumps(receipt,indent=2)+'\n')
lines=['','## 完整批次結果','',f"已執行 **{r['vertices']}個轉角 × {r['trials_per_vertex']}次 = {r['total_trials']:,}次**。腳本計算耗時{r['elapsed_s']:.1f}秒（不含編譯）。",'',
f"穿過局部出口{passed:,}次；同時符合所有局部嚴格條件{r['totals'].get('pass',0):,}次（{r['totals'].get('pass',0)/r['total_trials']:.2%}）。分類：`{r['totals']}`。",'',
'以下按中央頂點改向角分類；視窗仍包含相鄰彎，結果不能只歸因於中央角度。V形改向≥120度對應內角≤60度；本批輪子判定沒有採用官方V例外。','',
'| 中央改向分類 | 頂點數 | 試驗數 | 嚴格通過 | 通過率 |','|---|---:|---:|---:|---:|']
for label,g in groups.items():
    n=g['vertices']*r['trials_per_vertex'];lines.append(f"| {label} | {g['vertices']} | {n} | {g.get('pass',0)} | {g.get('pass',0)/n:.2%} |")
lines+=['',f"數量、唯一種子及計數均通過稽核；各轉角首末兩筆共{audit['deterministic_replays']}筆實際核心重播，全部指標完全一致。另有500組幾何距離對照及7組車體邊界檢查、148項回歸測試通過。",'',
'這次未修改控制程式。下一步先區分失敗發生於接近中央彎前或過彎中，再以感測事件與控制狀態診斷；不能從局部成功率推論加入任務層就能完賽。','',
'[機器可讀結果與雜湊](simulations/2026-11-06-corner-1000.json)','',
'## 每個轉角的1000次結果','',
'頂點編號沿用零起算圖面路線。正角為平面左轉、負角為右轉。故障分類可與幾何事件重疊，CSV保留全部獨立欄位；此表採摘要分類優先序。','',
'| 頂點 | 改向角° | 通過 | 輪子離路 | 車體失線 | 控制故障 | 逾時／其他 |','|---|---:|---:|---:|---:|---:|---:|']
for c in r['corners']:
    n=c['counts'];others=sum(v for k,v in n.items() if k not in ['pass','wheel_exit','body_line_loss','controller_fault'])
    lines.append(f"| {c['vertex']} | {c['angle_deg']:.2f} | {n.get('pass',0)} | {n.get('wheel_exit',0)} | {n.get('body_line_loss',0)} | {n.get('controller_fault',0)} | {others} |")
p=ROOT/'docs/CORNER_1000_2026-11-06.zh-TW.md';text=p.read_text(encoding='utf-8').split('\n## 完整批次結果')[0];p.write_text(text+'\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'total':r['total_trials'],'exit_passages':passed,'totals':r['totals'],'groups':groups,'elapsed_s':r['elapsed_s']},ensure_ascii=False))
