"""Analyze labelled device-timestamped captures; never infer race success."""
import argparse
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build import HEADER

def load(path):
    rows=[];previous=None;wraps=0;intervals=[];total=0
    with Path(path).open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['host_ms','label']+HEADER:raise ValueError('Unexpected CSV header')
        for n,row in enumerate(reader,2):
            if None in row or any(row.get(k) is None for k in HEADER):raise ValueError(f'Invalid row {n}')
            values={k:int(row[k]) for k in HEADER}
            if not 0<=values['millis']<2**32 or not 0<=values['tick']<2**32:raise ValueError('Timestamp/tick out of range')
            if any(not 0<=values[k]<=1023 for k in HEADER[3:8]):raise ValueError('ADC out of range')
            if values['mask'] not in range(0,15,2) or not 0<=values['state']<=6:raise ValueError('Mask/state out of range')
            if not 0<=values['reason']<=12 or not 0<=values['contrast']<=1000:raise ValueError('Reason/contrast out of range')
            if any(not 0<=values[k]<=255 for k in ('left_pwm','right_pwm')):raise ValueError('PWM out of range')
            if previous is not None:
                dt=(values['millis']-previous['millis'])&0xffffffff
                ticks=(values['tick']-previous['tick'])&0xffffffff
                if not 0<dt<2**31 or not 0<ticks<2**31:raise ValueError('Reset/duplicate/out-of-order data: split runs')
                wraps+=values['millis']<previous['millis'];intervals.append(dt);total+=dt
            previous=values;values['label']=row['label'];values['host_ms']=int(row['host_ms']);rows.append(values)
    if len(rows)<2:raise ValueError('At least two device records are required')
    return rows,intervals,total,wraps

def analyze(path):
    rows,intervals,total,wraps=load(path)
    return {'source_file':Path(path).name,'source_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        'records':len(rows),'device_observed_span_ms':total,'clock_wraps':wraps,
        'median_log_interval_ms':statistics.median(intervals),'max_log_interval_ms':max(intervals),
        'max_reported_tick_gap_ms':max(r['dt'] for r in rows),
        'states':dict(Counter(r['state'] for r in rows)),'reasons':dict(Counter(r['reason'] for r in rows)),
        'labels':dict(Counter(r['label'] for r in rows)),
        'sensor_statistics':{k:{'min':min(r[k] for r in rows),'median':statistics.median(r[k] for r in rows),'max':max(r[k] for r in rows)} for k in HEADER[3:8]},
        'rejected_tick_counter_delta':(rows[-1]['rejected']-rows[0]['rejected'])&0xffffffff,
        'timing_fault_counter_delta':(rows[-1]['timing_faults']-rows[0]['timing_faults'])&0xffffffff,
        'limits':['Track logs are decimated snapshots; unobserved raw transitions cannot be reconstructed.',
                  'A large log interval can be UART loss or scheduling delay; reported dt is only that record tick.',
                  'Labels are human annotations, not automatic ground truth.',
                  'No route, stop distance, motor speed or white-text immunity is certified.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=analyze(a.csv);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
