"""Execute actual native firmware on the complete diagram-traversal hypothesis.

No hardware access. Five predeclared runs are reconstruction trials, not certified
official laps. Unverified dimensions, layers and vehicle calibration remain visible.
"""
import argparse
from collections import deque
import csv
from dataclasses import asdict,replace
import hashlib
import json
import math
from pathlib import Path
import random
import shutil
import subprocess

from course_world import Course,Mechanisms,Pose,advance,sense,geometry,crossed_gate,chassis_pitch
from course_referee import audit_trace,verify_controller_trace,verify_sensor_trace
from course_qualification import judge_batch
from simulation_model import Plant
from sim_native import ROOT,Controller,build


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(controller,spec,plant,seed,lift_duration,trace_path,dt_ms=5,diagnostic_limit_s=None):
    if dt_ms not in (1,2,5):
        raise ValueError('dt_ms must be 1, 2 or 5')
    if plant.sample_ms%dt_ms or plant.latency_ms%dt_ms:
        raise ValueError('sampling and latency must align with integration step')
    c=Course(spec);m=Mechanisms(c,lift_duration)
    point,yaw=c.at(0)
    rng=random.Random(seed)
    pose=Pose(point[0]+rng.uniform(-.001,.001),point[1],point[2],yaw+rng.uniform(-.005,.005))
    controller.reset()
    queue=deque();command=(0,0);adc=[500]*5
    rows=[];state=controller.state();outcome='diagnostic_timeout' if diagnostic_limit_s else 'timeout';next_gate=0;station=0.0
    still_since=None
    max_ms=round(min(spec['timing']['maximum_s'],diagnostic_limit_s or spec['timing']['maximum_s'])*1000)
    for ms in range(0,max_ms+1,dt_ms):
        contact=c.contact(pose.x,pose.y,pose.z,m)
        if contact:
            pose.z=contact['z'];station=contact['s']
            pose.pitch=chassis_pitch(c,m,pose)
        ticked=0
        if ms%plant.sample_ms==0:
            queue.append((ms+plant.latency_ms,sense(c,m,pose,plant,rng)))
        while queue and queue[0][0]<=ms:
            _,adc=queue.popleft();command=controller.step(ms,adc);state=controller.state();ticked=1
        g=geometry(c,m,pose,plant)
        rows.append(dict(ms=ms,x=pose.x,y=pose.y,z=pose.z,yaw=pose.yaw,pitch=pose.pitch,
                         vl=pose.vl,vr=pose.vr,left=command[0],right=command[1],station=station,
                         support=contact['index'] if contact else -1,lift_height=m.lift_height,
                         lift_phase=m.lift_phase,seesaw_theta=m.theta,ticked=ticked,
                         a5=adc[0],a4=adc[1],a3=adc[2],a2=adc[3],a1=adc[4],intervention=0,**state,**controller.diagnostics()))
        if contact is None or g['ceiling_collision']:
            outcome='unsupported_surface_or_ceiling';break
        if not g['wheel_road']:
            outcome='wheel_left_road';break
        if not g['body_line']:
            outcome='body_lost_guide';break
        if state['turnFault']:
            outcome='controller_fault';break
        if next_gate==len(c.gates):
            outcome='finished';break
        # A legitimate mechanism wait continues world time. A stopped car outside
        # that mechanism remains a real physical stall even if its state says lift.
        stopped=abs(pose.vl)+abs(pose.vr)<.002
        on_lift=abs(station-c.lift_s)<c.lift_config['half_length_m']
        if stopped and not on_lift and ms>1000:
            if still_since is None:still_since=ms
            if ms-still_since>=10000:
                outcome='stalled_outside_mechanism';break
        else:still_since=None
        old=replace(pose)
        lift_before=m.lift_height
        on_lift=m.step(dt_ms/1000,station,(pose.vl,pose.vr),True)
        if on_lift:pose.z+=m.lift_height-lift_before
        contact=c.contact(pose.x,pose.y,pose.z,m)
        if contact is None:
            outcome='unsupported_surface_or_ceiling';break
        advance(pose,command,plant,contact,dt_ms/1000)
        new=c.contact(pose.x,pose.y,pose.z,m,max_step=.03)
        if new:pose.z=new['z']
        if next_gate<len(c.gates) and crossed_gate(c,c.gates[next_gate],old,pose):next_gate+=1
    with Path(trace_path).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    audit=audit_trace(trace_path,spec,plant,lift_duration)
    audit['native_trace_replay_verified']=verify_controller_trace(trace_path,controller)
    audit['physical_sensor_origin_verified']=verify_sensor_trace(trace_path,controller,spec,plant,seed,lift_duration)
    return dict(seed=seed,outcome=outcome,simulation_seconds=ms/1000,plant=asdict(plant),
                lift_duration_s=lift_duration,trace_file=Path(trace_path).name,**audit),rows


def write_replay(out,spec,results):
    import base64
    try:
        import fitz
    except ImportError:
        raise RuntimeError('Replay map extraction requires PyMuPDF (fitz)')
    pdf=ROOT/spec['source_pdf']
    doc=fitz.open(pdf)
    embedded=doc.extract_image(spec['source_map']['pdf_image_xref'])
    map_url='data:image/jpeg;base64,'+base64.b64encode(embedded['image']).decode()
    data=[]
    for row in results:
        with (out/row['trace_file']).open(newline='',encoding='utf-8') as f:
            trace=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
        data.append(dict(result=row,rows=trace[::4]+([trace[-1]] if (len(trace)-1)%4 else [])))
    payload=dict(spec=spec,map=map_url,runs=data)
    html=(ROOT/'simulation/course_replay.html').read_text(encoding='utf-8')
    (out/'index.html').write_text(html.replace('/*PAYLOAD*/{}',json.dumps(payload,separators=(',',':')).replace('<','\\u003c')),encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--course',type=Path,default=ROOT/'simulation/reconstructed_course.json')
    p.add_argument('--output',type=Path,default=ROOT/'build-output/full-course/current')
    p.add_argument('--source',type=Path,default=ROOT/'firmware/native_car/native_car.ino')
    p.add_argument('--baseline',help='Compile this Git revision instead of current native source')
    p.add_argument('--plant-json',type=Path,help='Explicit hypothetical or measured Plant overrides; frozen before all five trials')
    p.add_argument('--experiment',choices=['capture150','capture150_lift29'],help='Compile a separate test-only settings variant; never changes main firmware')
    p.add_argument('--replay-only',action='store_true')
    p.add_argument('--diagnostic-limit-s',type=float,help='Bound setup/tuning probes; these batches are explicitly not qualification trials')
    p.add_argument('--seed-plan',type=Path,help='Predeclared held-out seed JSON; frozen separately without changing course geometry')
    p.add_argument('--probe-seed',type=int,help='One diagnostic seed; requires diagnostic limit and never qualifies as a five-run batch')
    p.add_argument('--candidate-profile',type=Path,help='Hypothesis-specific ADC event prefix for the separate experimental core')
    args=p.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if args.diagnostic_limit_s is not None and (not math.isfinite(args.diagnostic_limit_s) or args.diagnostic_limit_s<=0):raise ValueError('diagnostic limit must be positive and finite')
    if args.probe_seed is not None and (not args.diagnostic_limit_s or args.seed_plan):raise ValueError('a probe requires a diagnostic limit and cannot use a held-out seed plan')
    spec=json.loads((out/'course.json' if args.replay_only else args.course).read_text(encoding='utf-8'))
    if file_hash(ROOT/spec['source_pdf'])!=spec['source_pdf_sha256']:
        raise ValueError('official PDF source hash mismatch')
    if args.replay_only:
        saved=json.loads((out/'results.json').read_text())
        if file_hash(out/'course.json')!=saved['course_sha256']:raise ValueError('frozen replay course hash mismatch')
        write_replay(out,spec,saved['attempts']);return
    if (out/'manifest.json').exists():
        raise ValueError('Refusing to overwrite a declared batch; use another output directory')
    source=args.source
    if args.baseline:
        folder=out/'source';folder.mkdir(exist_ok=True)
        for n in ('controller.h','native_car.ino'):
            data=subprocess.check_output(['git','show',args.baseline+':firmware/native_car/'+n],cwd=ROOT)
            (folder/n).write_bytes(data)
        source=folder/'native_car.ino'
    if args.experiment:
        folder=out/'experimental'/'native_car';folder.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,folder/'native_car.ino')
        text=source.with_name('controller.h').read_text(encoding='utf-8')
        substitutions={'capture = 100':'capture = 150'}
        if args.experiment=='capture150_lift29':
            substitutions.update({'liftWaitMs = 23350':'liftWaitMs = 29000','maximumLapMs = 180000':'maximumLapMs = 360000'})
        for old,new in substitutions.items():
            if text.count(old)!=1:raise ValueError('experiment setting anchor changed: '+old)
            text=text.replace(old,new)
        (folder/'controller.h').write_text(text,encoding='utf-8')
        source=folder/'native_car.ino'
    if args.candidate_profile:
        if args.experiment:raise ValueError('candidate profile and legacy setting experiment are separate variants')
        from learn_course_mission import stage_profile
        source=stage_profile(source,out/'profiled'/'candidate_car',args.candidate_profile,file_hash(args.course))
    dll,digest=build(source,out/'host')
    seeds=spec['timing']['seeds']
    if args.seed_plan:seeds=json.loads(args.seed_plan.read_text(encoding='utf-8'))['seeds']
    if args.probe_seed is not None:seeds=[args.probe_seed]
    if ((args.probe_seed is None and len(seeds)!=5) or len(set(seeds))!=len(seeds) or any(type(s) is not int for s in seeds)):
        raise ValueError('exactly five distinct predeclared integer seeds required')
    model_files=('tools/course_world.py','tools/course_referee.py','tools/run_course.py','tools/simulation_model.py',
                 'tools/course_qualification.py','tools/sim_native.py','tools/learn_course_mission.py')
    overrides=json.loads(args.plant_json.read_text(encoding='utf-8')) if args.plant_json else {}
    replace(Plant(),**overrides)
    manifest=dict(course_sha256=file_hash(args.course),source_hash=digest,
                  model_files={n:file_hash(ROOT/n) for n in model_files},expected_seeds=seeds,
                  official_geometry_verified=False,baseline=args.baseline,experiment=args.experiment,plant_overrides=overrides,
                  diagnostic_limit_s=args.diagnostic_limit_s,seed_plan_sha256=file_hash(args.seed_plan) if args.seed_plan else None,
                  candidate_profile_sha256=file_hash(args.candidate_profile) if args.candidate_profile else None,trials=[])
    for seed in seeds:
        rng=random.Random(seed)
        plant=replace(Plant(),battery_factor=rng.uniform(.90,1.0),right_gain=rng.uniform(.94,1.0),
                      friction_mu=rng.uniform(.45,.65),dead_pwm=rng.uniform(35,45))
        plant=replace(plant,**overrides)
        manifest['trials'].append(dict(seed=seed,plant=asdict(plant),lift_duration_s=rng.uniform(*spec['mechanisms']['lift']['duration_range_s'])))
    # Persist seed order, physics and hashes before any vehicle trial executes.
    shutil.copy2(args.course,out/'course.json')
    if args.seed_plan:shutil.copy2(args.seed_plan,out/'seed-plan.json')
    if args.candidate_profile:shutil.copy2(args.candidate_profile,out/'candidate-profile.json')
    for name in model_files:
        frozen=out/'model'/name;frozen.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,frozen)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    manifest_hash=file_hash(out/'manifest.json');c=Controller(dll);results=[]
    for trial in manifest['trials']:
        label='seed-'+str(trial['seed'])+'.csv'
        result,_=run(c,spec,Plant(**trial['plant']),trial['seed'],trial['lift_duration_s'],out/label,diagnostic_limit_s=args.diagnostic_limit_s)
        result.update(source_hash=digest,course_hash=manifest['course_sha256'],manifest_sha256=manifest_hash)
        results.append(result)
        print(result['seed'],result['outcome'],result['simulation_seconds'],str(result['gates_crossed'])+'/'+str(result['gates_required']),flush=True)
    batch=judge_batch(results,digest,manifest['course_sha256'],seeds)
    if args.diagnostic_limit_s:batch.update(passed=False,diagnostic_only=True)
    summary=dict(status='reconstruction_trials_completed',official_qualification_passed=False,
                 warning='Inferred full-diagram model, not a verified official metric/layer configuration or calibrated car.',
                 baseline=args.baseline,experiment=args.experiment,diagnostic_limit_s=args.diagnostic_limit_s,manifest_sha256=manifest_hash,source_sha256=digest,
                 course_sha256=manifest['course_sha256'],five_run_model_contract=batch,attempts=results)
    (out/'results.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    write_replay(out,spec,results)
    print('Replay:',out/'index.html',flush=True)


if __name__=='__main__':main()
