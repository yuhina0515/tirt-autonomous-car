"""Check trial coverage, counters and deterministic first/last trial replays."""
import csv,ctypes,hashlib,json
from collections import Counter
from pathlib import Path
import sys

def audit(directory):
    m=json.loads((directory/'manifest.json').read_text());r=json.loads((directory/'results.json').read_text())
    counts=Counter();statuses=Counter();examples=[];seen=set()
    with (directory/'trials.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            vertex=int(row['vertex']);trial=int(row['trial']);seed=int(row['seed'])
            assert seed==202611060000+vertex*1000+trial and seed not in seen
            assert 0<=trial<m['trials_per_vertex'];seen.add(seed);counts[vertex]+=1
            code=int(float(row['outcome']));wheel=float(row['first_wheel_exit_ms']);body=float(row['first_body_loss_ms'])
            status='pass' if code==1 and wheel<0 and body<0 else 'wheel_exit' if wheel>=0 else 'body_line_loss' if body>=0 else {0:'timeout',1:'pass',2:'controller_fault',3:'wrong_marker',4:'missed_gate'}[code]
            statuses[status]+=1
            if trial in (0,m['trials_per_vertex']-1):examples.append(row)
    assert counts==Counter({b['vertex']:m['trials_per_vertex'] for b in m['bends']})
    assert dict(statuses)==r['totals'] and sum(counts.values())==r['total_trials']
    lib=ctypes.CDLL(str((directory/'host/controller.dll').resolve()));fn=lib.corner_trial
    fn.argtypes=[ctypes.POINTER(ctypes.c_double),ctypes.c_int,ctypes.c_uint64,ctypes.POINTER(ctypes.c_double)];fn.restype=None
    paths={b['vertex']:b['path'] for b in m['bends']}
    for row in examples:
        p=paths[int(row['vertex'])];coords=(ctypes.c_double*(2*len(p)))(*[v for pt in p for v in pt]);values=(ctypes.c_double*8)()
        fn(coords,len(p),int(row['seed']),values)
        expected=[float(row[k]) for k in ['outcome','ms','first_wheel_exit_ms','first_body_loss_ms','max_error_m','fault','gates','required']]
        assert list(values)==expected,row
    receipt=dict(coverage_verified=True,distinct_seeds=len(seen),counter_verified=True,deterministic_replays=len(examples),
        note='Reproducibility audit, not independent validation of the new planar physics/judge',
        hashes={name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in ['manifest.json','trials.csv','results.json','host/controller.dll']})
    (directory/'audit.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
if __name__=='__main__':audit(Path(sys.argv[1]))
