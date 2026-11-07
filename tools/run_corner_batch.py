"""204 nonzero artwork vertices x1000 local actual-core trials; deterministic receipts."""
import argparse,ctypes,csv,hashlib,json,math,shutil,time
from collections import Counter
from pathlib import Path
from sim_native import ROOT,compile_bridge

def window(points,vertex,radius=.6):
    def side(indices):
        out=[points[vertex]];remaining=radius
        for i in indices:
            a=out[-1];b=points[i];length=math.dist(a,b)
            if length>=remaining:
                out.append([a[k]+(b[k]-a[k])*remaining/length for k in (0,1)]);break
            out.append(b);remaining-=length
        return out
    local=list(reversed(side(range(vertex-1,-1,-1))))+side(range(vertex+1,len(points)))[1:]
    # Exact arclength crop; no isolated-angle replacement or invented tangent.
    return local

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--trials',type=int,default=1000);args=ap.parse_args()
    if not 1<=args.trials<=1000:raise ValueError('trials must be1..1000 for disjoint seeds')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);host=out/'host';host.mkdir()
    shutil.copy2(__file__,out/'run_corner_batch.py')
    shutil.copytree(ROOT/'firmware/layered_car',host/'layered')
    shutil.copy2(ROOT/'tools/corner_batch.cpp',host/'bridge.cpp')
    source=ROOT/'simulation/reconstructed_course_ground.json';shutil.copy2(source,out/'course.json')
    spec=json.loads(source.read_text());pts=[[x*.005,-y*.005] for x,y in spec['points_px']]
    bends=[]
    for i in range(1,len(pts)-1):
        a,b,c=pts[i-1:i+2];h1=math.atan2(b[1]-a[1],b[0]-a[0]);h2=math.atan2(c[1]-b[1],c[0]-b[0]);angle=math.degrees(math.atan2(math.sin(h2-h1),math.cos(h2-h1)))
        if abs(angle)>.01:bends.append(dict(vertex=i,angle=angle,path=window(pts,i)))
    manifest=dict(kind='local_planar_stress_not_full_world',controller='layered_empty_route',trials_per_vertex=args.trials,bends=bends,
        seed_formula='202611060000 + vertex*1000 + trial_index',dt_ms=5,latency_ms=5,time_limit_ms=15000,
        road_width_m=.19,line_width_m=.02,body_m=[.18,.12],wheel_width_m=.015,
        limitations=['flattened elevation','no mechanisms or extra paint','no mission/full-lap history','strict wheel check without V exception','unmeasured distributions'],
        hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,ROOT/'tools/corner_batch.cpp',Path(__file__),*list((ROOT/'firmware/layered_car').glob('*.h'))]})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    dll=ctypes.CDLL(str(compile_bridge(host)));fn=dll.corner_trial;fn.argtypes=[ctypes.POINTER(ctypes.c_double),ctypes.c_int,ctypes.c_uint64,ctypes.POINTER(ctypes.c_double)];fn.restype=None
    summaries=[];start=time.time()
    with (out/'trials.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['vertex','trial','seed','outcome','ms','first_wheel_exit_ms','first_body_loss_ms','max_error_m','fault','gates','required'])
        for bend in bends:
            coords=(ctypes.c_double*(len(bend['path'])*2))(*[v for p in bend['path'] for v in p]);counts=Counter();examples={}
            for trial in range(args.trials):
                seed=202611060000+bend['vertex']*1000+trial;r=(ctypes.c_double*8)();fn(coords,len(bend['path']),seed,r);vals=list(r)
                # Passage and strict road/body checks are independent, never silently upgraded to race compliance.
                status='pass' if r[0]==1 and r[2]<0 and r[3]<0 else 'wheel_exit' if r[2]>=0 else 'body_line_loss' if r[3]>=0 else {0:'timeout',1:'pass',2:'controller_fault',3:'wrong_marker',4:'missed_gate'}[int(r[0])]
                counts[status]+=1;examples.setdefault(status,dict(seed=seed,metrics=vals));writer.writerow([bend['vertex'],trial,seed,*vals])
            summaries.append(dict(vertex=bend['vertex'],angle_deg=bend['angle'],counts=dict(counts),examples=examples))
            f.flush();(out/'progress.json').write_text(json.dumps(dict(completed=len(summaries),total=len(bends),elapsed_s=time.time()-start)))
    totals=Counter();[totals.update(s['counts']) for s in summaries]
    result=dict(total_trials=len(bends)*args.trials,vertices=len(bends),trials_per_vertex=args.trials,totals=dict(totals),corners=summaries,elapsed_s=time.time()-start,official_qualification=False)
    (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='corners'}))
if __name__=='__main__':main()
