"""Re-audit a saved batch using its hash-verified frozen model and actual core."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory',type=Path)
    p.add_argument('--current-referee',action='store_true',help='Also audit historical traces with the current stricter physical/sensor referee')
    p.add_argument('--audit-label',default='strict',help='Name a new auditor snapshot when code changes; existing snapshots are immutable')
    args=p.parse_args();out=args.directory.resolve()
    if not re.fullmatch('[a-z0-9_-]+',args.audit_label):raise ValueError('invalid audit label')
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    results=json.loads((out/'results.json').read_text(encoding='utf-8'))
    if sha(out/'manifest.json')!=results['manifest_sha256']:
        raise ValueError('batch manifest hash mismatch')
    if sha(out/'course.json')!=manifest['course_sha256']:
        raise ValueError('frozen course hash mismatch')
    if manifest.get('seed_plan_sha256') and sha(out/'seed-plan.json')!=manifest['seed_plan_sha256']:
        raise ValueError('held-out seed plan hash mismatch')
    if manifest.get('candidate_profile_sha256') and sha(out/'candidate-profile.json')!=manifest['candidate_profile_sha256']:
        raise ValueError('candidate mission profile hash mismatch')
    for name,digest in manifest['model_files'].items():
        if sha(out/'model'/name)!=digest:
            raise ValueError('frozen model hash mismatch: '+name)
    auditor_files={}
    if args.current_referee:
        root=Path(__file__).resolve().parents[1]
        for name in ('course_world.py','course_referee.py','simulation_model.py','course_qualification.py','sim_native.py','audit_course_run.py'):
            src=root/'tools'/name
            auditor_files[name]=sha(src)
            dest=out/(args.audit_label+'-audit-model')/name;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and sha(dest)!=auditor_files[name]:
                raise ValueError('refusing to overwrite a different strict auditor version')
            dest.write_bytes(src.read_bytes())
    else:
        sys.path.insert(0,str(out/'model'/'tools'))
    from course_referee import audit_trace,verify_controller_trace
    from course_qualification import judge_batch
    from simulation_model import Plant
    from sim_native import Controller,build
    import course_referee
    dll,digest=build(out/'host'/'sketch.inc',out/'audit-host')
    if digest!=manifest['source_hash']:
        raise ValueError('frozen native source hash mismatch')
    c=Controller(dll);spec=json.loads((out/'course.json').read_text(encoding='utf-8'))
    if [r['seed'] for r in results['attempts']]!=manifest['expected_seeds']:
        raise ValueError('attempts do not match predeclared seed order')
    audited=[]
    for trial,row in zip(manifest['trials'],results['attempts']):
        if (row['seed']!=trial['seed'] or row['plant']!=trial['plant'] or
            row['lift_duration_s']!=trial['lift_duration_s'] or row['source_hash']!=digest or
            row['course_hash']!=manifest['course_sha256'] or row['manifest_sha256']!=results['manifest_sha256']):
            raise ValueError('trial differs from declared physics')
        name=row['trace_file']
        if Path(name).name!=name or name!='seed-'+str(trial['seed'])+'.csv':
            raise ValueError('unexpected trace filename')
        r=audit_trace(out/name,spec,Plant(**trial['plant']),trial['lift_duration_s'],row['trace_sha256'])
        verify_controller_trace(out/name,c)
        if hasattr(course_referee,'verify_sensor_trace'):
            course_referee.verify_sensor_trace(out/name,c,spec,Plant(**trial['plant']),trial['seed'],trial['lift_duration_s'])
        r.update(seed=trial['seed'],source_hash=digest,course_hash=manifest['course_sha256'])
        audited.append(r)
    batch=judge_batch(audited,digest,manifest['course_sha256'],manifest['expected_seeds'])
    if manifest.get('diagnostic_limit_s'):batch.update(passed=False,diagnostic_only=True)
    report=dict(hash_verified_traces=len(audited),native_trace_replays_verified=len(audited),
                physical_sensor_origins_verified=len(audited) if hasattr(course_referee,'verify_sensor_trace') else 0,
                stricter_current_auditor=bool(args.current_referee),auditor_sha256=auditor_files,
                model_batch=batch,official_qualification_passed=False)
    (out/(args.audit_label+'-audited.json' if args.current_referee else 'audited.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
