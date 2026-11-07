"""Independent completeness and five-consecutive-run qualification contracts.

No controller can declare its own completion. This module never fabricates a
course, infers grade connectivity from a plan image, or simulates 3D machinery.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECONSTRUCTION_FIELDS=('metric_geometry','directed_route_and_branch_exits',
 'layer_connections_and_heights','checkpoint_order_and_placement','shortcut_boundaries',
 'F_marker_definition','start_finish_detection_geometry','seesaw_geometry_and_dynamics',
 'lift_geometry_and_settled_feedback','vehicle_geometry_and_motor_calibration')
REQUIRED_CHECKS=('start_crossing','ordered_gate_checks','body_line_coverage',
 'wheel_road_coverage_with_V_exception','direction_and_layer','shortcut_boundary',
 'seesaw_crossing','lift_stop_and_settled_exit','finish_crossing','no_fault_or_intervention')


def preflight(spec, root=ROOT):
    issues=[]
    source=root/spec['rules_source']
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=spec.get('rules_sha256'):
        issues.append('rules_source_hash_mismatch')
    for name in RECONSTRUCTION_FIELDS:
        entry=spec.get('reconstruction',{}).get(name)
        if not isinstance(entry,dict) or not entry.get('value') or not entry.get('source'):
            issues.append('missing_verified_'+name)
    if tuple(spec.get('required_evidence',[]))!=REQUIRED_CHECKS:
        issues.append('incomplete_referee_contract')
    return issues


def judge_attempt(record, source_hash, course_hash):
    reasons=[]
    if record.get('source_hash')!=source_hash:reasons.append('controller_changed')
    if record.get('course_hash')!=course_hash:reasons.append('course_changed')
    if (not isinstance(record.get('trace_sha256'),str) or len(record['trace_sha256'])!=64
            or any(c not in '0123456789abcdef' for c in record['trace_sha256'])):
        reasons.append('missing_trace')
    seconds=record.get('elapsed_s')
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<seconds<=360:
        reasons.append('invalid_or_overdue_elapsed_time')
    checks=record.get('independent_checks',{})
    for name in REQUIRED_CHECKS:
        if checks.get(name) is not True:reasons.append(name)
    return {'passed':not reasons,'reasons':reasons}


def judge_batch(records, source_hash, course_hash, expected_seeds=None):
    attempts=[judge_attempt(r,source_hash,course_hash) for r in records]
    streak=longest=0
    for result in attempts:
        streak=streak+1 if result['passed'] else 0;longest=max(longest,streak)
    seeds=[r.get('seed') for r in records]
    unique_seeds=all(type(seed) is int for seed in seeds) and len(seeds)==len(set(seeds))
    predeclared=expected_seeds is not None and len(expected_seeds)==5 and seeds==expected_seeds
    return dict(passed=len(records)==5 and longest==5 and unique_seeds and predeclared,
                required_runs=5,attempts=attempts,longest_streak=longest,
                five_distinct_predeclared_seeds=unique_seeds and predeclared)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--course',type=Path,default=ROOT/'simulation/official_course.json')
    p.add_argument('--output',type=Path,default=ROOT/'build-output/official-qualification.json')
    args=p.parse_args();spec=json.loads(args.course.read_text());issues=preflight(spec)
    # Executable inferred reconstruction has a separate constrained2.5D world and
    # trace referee. It does not establish authoritative metric/layer geometry.
    issues.append('official_metric_layer_model_and_vehicle_calibration_not_verified')
    report=dict(status='blocked',qualification_target='official_complete_course',
                course_sha256=hashlib.sha256(args.course.read_bytes()).hexdigest(),
                blocking_issues=issues,required_consecutive_completions=5,
                executed_official_runs=0,consecutive_completions=0,
                passed=False,attempts=[],
                available_experimental_tools=['run_course.py','audit_course_run.py'],
                note='No trials were run; this is a preflight report, not five failed or successful laps.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));return 2


if __name__=='__main__':raise SystemExit(main())
