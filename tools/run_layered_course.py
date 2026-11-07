"""Actual layered core in the existing full-course world; no navigation oracle."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
from sim_native import ROOT, Controller, compile_bridge
from simulation_model import Plant
from run_course import run, write_replay


def build_core(out):
    out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in ('motion.h', 'mission.h', 'controller.h', 'layered_car.ino'):
        src = ROOT / 'firmware/layered_car' / name
        shutil.copy2(src, out / name)
        hashes[name] = hashlib.sha256(src.read_bytes()).hexdigest()
    (out / 'bridge.cpp').write_text(r'''
#include "controller.h"
layered::Controller car;
layered::Wheels wheels;
int mask=0,faultMask=0;
extern "C" __declspec(dllexport) void reset_sim(){car=layered::Controller();wheels={};mask=faultMask=0;}
extern "C" __declspec(dllexport) void step_sim(uint32_t ms,int a5,int a4,int a3,int a2,int a1){
 uint16_t adc[]={uint16_t(a5),uint16_t(a4),uint16_t(a3),uint16_t(a2),uint16_t(a1)};
 mask=(a4<70?8:0)|(a3<70?4:0)|(a2<70?2:0);
 bool failed=car.fault!=layered::Fault::None;
 wheels=car.tick(ms,adc);
 if(!failed&&car.fault!=layered::Fault::None)faultMask=mask;
}
extern "C" __declspec(dllexport) int get_state(int field){switch(field){
 case 0:return mask;case 1:return car.fault!=layered::Fault::None;
 case 2:return car.phase()==layered::Phase::Finished;
 case 3:return car.phase()==layered::Phase::Waiting?1:car.phase()==layered::Phase::Exiting?2:0;
 case 13:return faultMask;}return 0;}
extern "C" __declspec(dllexport) int left_command(){return wheels.left;}
extern "C" __declspec(dllexport) int right_command(){return wheels.right;}
extern "C" __declspec(dllexport) int set_parameter(const char*,int){return 0;}
extern "C" __declspec(dllexport) int fault_reason(){return int(car.fault);}
''', encoding='utf-8')
    return compile_bridge(out), hashes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference', type=Path, required=True, help='Frozen reference manifest for identical plant/seed/course')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if out.exists():
        raise ValueError('Choose a fresh output directory')
    out.mkdir(parents=True)
    manifest = json.loads((a.reference / 'manifest.json').read_text())
    trial = manifest['trials'][0]
    spec = json.loads((a.reference / 'course.json').read_text())
    shutil.copy2(a.reference / 'course.json', out / 'course.json')
    dll, hashes = build_core(out / 'host')
    receipt = dict(kind='actual_layered_core_no_route_baseline', source_sha256=hashes,
                   reference_manifest_sha256=hashlib.sha256((a.reference/'manifest.json').read_bytes()).hexdigest(),
                   trial=trial, official_geometry_verified=False, route_configured=False)
    # Freeze all world/bridge inputs before execution; device adapter not executed.
    for name in manifest['model_files']:
        src = a.reference / 'model' / name
        dst = out / 'model' / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != manifest['model_files'][name]:
            raise ValueError('Current model differs from frozen reference: '+name)
        shutil.copy2(src, dst)
    receipt['model_files'] = manifest['model_files']
    receipt['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    shutil.copy2(__file__, out/'run_layered_course.py')
    (out/'manifest.json').write_text(json.dumps(receipt, indent=2))
    controller = Controller(dll)
    result, _ = run(controller, spec, Plant(**trial['plant']), trial['seed'], trial['lift_duration_s'],
                    out/f"seed-{trial['seed']}.csv", diagnostic_limit_s=360)
    result['core_fault_reason'] = controller.lib.fault_reason()
    summary = dict(attempts=[result], route_configured=False, official_qualification_passed=False)
    (out/'results.json').write_text(json.dumps(summary, indent=2))
    write_replay(out, spec, [result])
    print(json.dumps({k:result[k] for k in ('outcome','simulation_seconds','gates_crossed','gates_required','core_fault_reason')}, indent=2))


if __name__ == '__main__':
    main()
