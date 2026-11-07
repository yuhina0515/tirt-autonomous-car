"""Learn one model-junction action from audited post-lift ADC event prefixes.

The teacher uses physical sensor footprint, ordered gates and the frozen route
hypothesis. CSV station annotations never label targets. Firmware receives only
literal L/R/W words and one L/R action, not the teacher's coordinates or progress.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import json
import math
from pathlib import Path
import sys

from course_environment import Course
from course_referee import audit_trace,verify_sensor_trace
from simulation_model import Plant
from sim_native import ROOT,Controller,build
from learn_course_mission import models_for_spec,TOKENS,canonical_sha,feature_identity,sha,observable_events,stage_profile


def training_seed(seed,spec):
    if type(seed) is not int or seed not in spec['timing']['seeds']:
        raise ValueError('held-out or undeclared seed cannot train a junction')


def junction_turn(course,vertex):
    if type(vertex) is not int or not 0<vertex<len(course.points)-1:
        raise ValueError('junction must be an interior route vertex')
    a,b=course.main_segments[vertex-1:vertex+1]
    ax,ay=(a.b[0]-a.a[0])/a.length,(a.b[1]-a.a[1])/a.length
    bx,by=(b.b[0]-b.a[0])/b.length,(b.b[1]-b.a[1])/b.length
    delta=math.atan2(ax*by-ay*bx,ax*bx+ay*by)
    if not .2<abs(delta)<math.pi-.01:raise ValueError('junction is not an unambiguous modeled turn')
    return 'L' if delta>0 else 'R'


def junction_observation(row,course,gate_events,plant,vertex):
    if int(row['liftState'])!=3:return False
    point,yaw=course.at(course.stations[vertex])
    heading=float(row['yaw'])
    if math.cos(heading-yaw)<math.cos(math.pi/6):return False
    sx=float(row['x'])+plant.sensor_ahead_m*math.cos(heading)
    sy=float(row['y'])+plant.sensor_ahead_m*math.sin(heading)
    # The event is emitted on leaving a full-width observation. Include its
    # physical line footprint and one sampling/delivery interval, not a station.
    radius=course.assumptions['line_width_m']/2+plant.sensor_radius_m+plant.max_wheel_mps*(plant.sample_ms+plant.latency_ms)/1000
    required=sum(s<course.stations[vertex] for s in course.gates)
    crossed=sum(e['ms']<=int(row['ms']) for e in gate_events)
    return (math.hypot(sx-point[0],sy-point[1])<=radius and
        abs(float(row['z'])-point[2])<.03 and crossed>=required)


def audit_teacher(task):
    folder,vertex,work=task;folder=Path(folder);work=Path(work)
    results=json.loads((folder/'results.json').read_text(encoding='utf-8'))
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    manifest_hash=sha(folder/'manifest.json')
    if results['manifest_sha256']!=manifest_hash:raise ValueError('teacher manifest changed')
    course_hash=sha(folder/'course.json')
    if course_hash!=manifest['course_sha256'] or results['course_sha256']!=course_hash:raise ValueError('teacher course changed')
    spec=json.loads((folder/'course.json').read_text(encoding='utf-8'));course=Course(spec)
    turn=junction_turn(course,vertex)
    if results['source_sha256']!=manifest['source_hash']:raise ValueError('teacher result source changed')
    if (len(manifest['trials'])!=len(results['attempts']) or
        [r['seed'] for r in results['attempts']]!=manifest['expected_seeds']):raise ValueError('incomplete teacher batch')
    for trial,attempt in zip(manifest['trials'],results['attempts']):
        training_seed(attempt['seed'],spec)
        if (trial['seed']!=attempt['seed'] or trial['plant']!=attempt['plant'] or
            trial['lift_duration_s']!=attempt['lift_duration_s'] or attempt['source_hash']!=manifest['source_hash'] or
            attempt['course_hash']!=course_hash or attempt['manifest_sha256']!=manifest_hash):raise ValueError('teacher trial differs from manifest')
    for name,digest in manifest['model_files'].items():
        if sha(folder/'model'/name)!=digest:raise ValueError('frozen teacher model changed')
    models={n:canonical_sha(folder/'model'/n) for n in models_for_spec(spec)}
    if any(canonical_sha(ROOT/n)!=digest for n,digest in models.items()):raise ValueError('teacher sensor/world model differs')
    dll,digest=build(folder/'host'/'sketch.inc',work/'host')
    if digest!=manifest['source_hash']:raise ValueError('teacher source changed')
    controller=Controller(dll);records=[]
    for trial,attempt in zip(manifest['trials'],results['attempts']):
        seed=trial['seed'];print('Auditing junction teacher seed='+str(seed),file=sys.stderr,flush=True)
        name='seed-'+str(seed)+'.csv'
        if attempt['trace_file']!=name:raise ValueError('unexpected teacher trace filename')
        path=folder/name;plant=Plant(**trial['plant']);trace_hash=sha(path)
        physical=audit_trace(path,spec,plant,trial['lift_duration_s'],attempt['trace_sha256'])
        verify_sensor_trace(path,controller,spec,plant,seed,trial['lift_duration_s'])
        with path.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
        word=[];target=None
        for code,row in observable_events(rows):
            if int(row['liftState'])!=3:continue
            word.append(TOKENS[code])
            if code==1 and junction_observation(row,course,physical['gate_events'],plant,vertex):target=row;break
        records.append(dict(directory=str(folder.resolve()),seed=seed,manifest_sha256=manifest_hash,
            source_sha256=digest,course_sha256=course_hash,sensor_model_sha256=models,trace_sha256=trace_hash,
            word=word,turn=turn,target_ms=int(target['ms']) if target else None,
            reason=None if target else 'modeled_junction_not_observed'))
    return records


def learn(directories,source,lift_profile,vertex,work,workers=1):
    source=Path(source);work=Path(work);work.mkdir(parents=True,exist_ok=True)
    profile=json.loads(Path(lift_profile).read_text(encoding='utf-8'))
    if profile.get('junctions'):raise ValueError('a lift-only source-bound profile is required')
    if profile['feature_sha256']!=feature_identity(source):raise ValueError('lift profile belongs to another complete core')
    tasks=[(str(Path(d).resolve()),vertex,str(work/'teacher-audits'/str(i))) for i,d in enumerate(directories)]
    if workers>1:
        with ProcessPoolExecutor(max_workers=workers) as pool:groups=list(pool.map(audit_teacher,tasks))
    else:groups=[audit_teacher(task) for task in tasks]
    records=[r for group in groups for r in group]
    seeds=[r['seed'] for r in records]
    if len(set(seeds))!=len(seeds):raise ValueError('duplicate junction teacher seed')
    for r in records:
        if r['course_sha256']!=profile['course_sha256'] or r['sensor_model_sha256']!=profile['sensor_model_sha256']:
            raise ValueError('junction teacher differs from lift course/model identity')
    accepted=[r for r in records if r['target_ms'] is not None]
    if not accepted:raise ValueError('no audited junction observation')
    words=sorted({(tuple(r['word']),r['turn']) for r in accepted})
    if len(words)>4:raise ValueError('too many junction hypotheses')
    profile['junctions']=[dict(word=list(word),turn=turn) for word,turn in words]
    profile['junction_teacher']=dict(vertex=vertex,label_source='audited physical sensor footprint and preceding ordered gates; inferred route, not official geometry',
        labeler_sha256=sha(Path(__file__)),training=records)
    draft=work/'draft-profile.json';draft.write_text(json.dumps(profile,indent=2),encoding='utf-8')
    staged=stage_profile(source,work/'profiled'/source.stem,draft,profile['course_sha256'])
    dll,digest=build(staged,work/'prefix-host');controller=Controller(dll)
    for r in records:
        folder=Path(r['directory']);path=folder/('seed-'+str(r['seed'])+'.csv')
        if sha(folder/'manifest.json')!=r['manifest_sha256'] or sha(path)!=r['trace_sha256']:raise ValueError('teacher changed after physical audit')
        manifest=json.loads((folder/'manifest.json').read_text());trial=next(t for t in manifest['trials'] if t['seed']==r['seed'])
        with path.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
        # Match every recorded command, state and diagnostic before the target.
        # Rejected teachers also replay in full; no evidence is discarded.
        prefix_rows=[row for row in rows if r['target_ms'] is None or int(row['ms'])<r['target_ms']]
        prefix=work/('prefix-'+str(r['seed'])+'.csv')
        with prefix.open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(prefix_rows)
        spec=json.loads((folder/'course.json').read_text(encoding='utf-8'));plant=Plant(**trial['plant'])
        verify_sensor_trace(prefix,controller,spec,plant,r['seed'],trial['lift_duration_s'])
        if r['target_ms'] is not None:
            target=next(row for row in rows if int(row['ms'])==r['target_ms'])
            controller.step(r['target_ms'],[int(target[k]) for k in ('a5','a4','a3','a2','a1')])
            state=controller.state();diag=controller.diagnostics();side=-1 if r['turn']=='L' else 1
            if (state['turnFault'] or state['turnDirection']!=side or not state['cornerWideRecovery'] or
                diag['missionPhase']!=6 or diag['eventSerial']!=int(target['eventSerial']) or diag['eventCode']!=1 or
                diag['uncertaintyMs']!=int(target['uncertaintyMs'])):
                raise ValueError('profiled core did not select the audited action at the unchanged event/deadline')
        r.update(revalidated_profiled_source_sha256=digest,prefix_sha256=sha(prefix),prefix_last_ms=int(prefix_rows[-1]['ms']),
                 target_action_verified=r['target_ms'] is not None)
        print('Verified junction prefix seed='+str(r['seed']),file=sys.stderr,flush=True)
    profile['junction_binding']='entire core and source-bound lift profile; all teacher poses/ADC audited, actual profiled commands/states/events identical before target; target action and unchanged timer checked'
    return profile


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directories',nargs='+',type=Path)
    p.add_argument('--source',required=True,type=Path);p.add_argument('--lift-profile',required=True,type=Path)
    p.add_argument('--vertex',required=True,type=int);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--workers',type=int,default=1);args=p.parse_args()
    if not 1<=args.workers<=5:raise ValueError('workers must be1..5')
    payload=learn(args.directories,args.source,args.lift_profile,args.vertex,args.output.parent/'junction-learning',args.workers)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(json.dumps(dict(junctions=payload['junctions'],targets=sum(r['target_ms'] is not None for r in payload['junction_teacher']['training']))))


if __name__=='__main__':main()
