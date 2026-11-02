"""Build native baseline/current, run configured physical scenarios, save replay.
No hardware access. All plant/track features are synthetic, not measured TAIWAN.
"""
import argparse
import csv
from collections import Counter
from dataclasses import replace
import hashlib
import json
import re
from pathlib import Path
import subprocess

from physics_sim import Plant, run, scenario
from sim_native import ROOT, Controller, build


def validate(config):
    if not config.get('plants') or not config.get('cases'):raise ValueError('plants and cases are required')
    for name,plant in config['plants'].items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+',name):raise ValueError('invalid plant name')
        replace(Plant(),**plant)
    names=set()
    for case in config['cases']:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',case['name']) or case['name'] in names:raise ValueError('invalid or duplicate case name')
        names.add(case['name'])
        route=case['route']
        allowed=['straight']+[b+s for b in ['turn60','turn90','v60','wide_turn60','wide_v60'] for s in ['_left','_right']]
        if route not in allowed:raise ValueError('unknown route: '+route)
        replace(Plant(),**case.get('plant',{}))
        for f in case.get('features',[]):
            if type(f['on']) is not bool or not(f['x0']<f['x1'] and f['y0']<f['y1']):raise ValueError('invalid rectangular feature')


def write_replay(out,config,results):
    cases={c['name']:c for c in config['cases']};replays=[]
    for row in results:
        case=cases[row['case']];label=row['model']+'-'+row['plant_name']+'-'+row['case']
        with (out/(label+'.csv')).open() as f:
            trace=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
        path,_,patch=scenario(case['route'])
        replays.append(dict(label=label,outcome=row['outcome'],plant=row['plant'],patch=patch,
                            path=path,features=case.get('features',[]),rows=trace[::3]))
    template=(ROOT/'simulation/replay.html').read_text(encoding='utf-8')
    (out/'index.html').write_text(template.replace('/*DATA*/[]',json.dumps(replays,separators=(',',':')).replace('<','\\u003c')),encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=ROOT/'simulation/scenarios.json')
    p.add_argument('--output',type=Path,default=ROOT/'build-output/simulation')
    p.add_argument('--baseline',default='00e0db0')
    p.add_argument('--replay-only',action='store_true',help='Rebuild viewer from saved results and CSV without simulation')
    args=p.parse_args();config=json.loads(args.config.read_text());validate(config)
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if args.replay_only:
        write_replay(out,config,json.loads((out/'results.json').read_text())['results']);return
    old=out/'baseline-source';old.mkdir(exist_ok=True)
    for name in ['controller.h','native_car.ino']:
        r=subprocess.run(['git','show',args.baseline+':firmware/native_car/'+name],cwd=ROOT,capture_output=True,check=True)
        (old/name).write_bytes(r.stdout)
    results=[];hashes={}
    for model,source in [('baseline',old/'native_car.ino'),('current',ROOT/'firmware/native_car/native_car.ino')]:
        dll,digest=build(source,out/'host'/model);hashes[model]=digest;c=Controller(dll)
        for plant_name,override in config['plants'].items():
            for case in config['cases']:
                plant=replace(Plant(),**{**override,**case.get('plant',{})})
                label=model+'-'+plant_name+'-'+case['name']
                row,trace=run(c,plant,case['route'],{},config['seed'],out/(label+'.csv'),case.get('features'))
                row.update(model=model,plant_name=plant_name,case=case['name']);results.append(row)
        print(model,dict(Counter(r['outcome'] for r in results if r['model']==model)),flush=True)
    summary=dict(baseline=args.baseline,source_hashes=hashes,config_sha256=hashlib.sha256(args.config.read_bytes()).hexdigest(),
                 warning='Uncalibrated synthetic planar plant; reached does not imply legal or real-world completion.',results=results)
    (out/'results.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    write_replay(out,config,results)
    print('Replay:',out/'index.html',flush=True)


if __name__=='__main__':main()
