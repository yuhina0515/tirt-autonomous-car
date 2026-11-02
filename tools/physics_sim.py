"""Closed-loop sensitivity experiment using actual car.ino and an assumed plant.

No hardware access. This is a planar differential-drive approximation, not a
digital twin, race acceptance test, or model of the actual TAIWAN artwork.
"""
import argparse
import csv
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess

from sim_native import ROOT, Controller, build


@dataclass
class Plant:
    # All values are assumptions, not measured CAGEBOT specifications.
    track_m: float = 0.115
    sensor_ahead_m: float = 0.060
    sensor_spacing_m: float = 0.014
    sensor_radius_m: float = 0.002
    line_width_m: float = 0.020
    road_width_m: float = 0.200
    max_wheel_mps: float = 0.65
    dead_pwm: float = 40
    motor_tau_s: float = 0.080
    coast_tau_s: float = 0.240
    max_accel_mps2: float = 2.5
    left_gain: float = 1.0
    right_gain: float = 0.97
    battery_factor: float = 1.0
    friction_mu: float = 0.55
    sample_ms: int = 5
    latency_ms: int = 5
    adc_noise: float = 4
    line_adc: float = 35
    background_adc: float = 500
    grade_deg: float = 0

    def __post_init__(self):
        for name,value in asdict(self).items():
            if not math.isfinite(value):raise ValueError(name+' must be finite')
        for name in ['track_m','sensor_ahead_m','sensor_spacing_m','sensor_radius_m',
                     'line_width_m','road_width_m','max_wheel_mps','motor_tau_s',
                     'coast_tau_s','max_accel_mps2','left_gain','right_gain','battery_factor','friction_mu']:
            if getattr(self,name)<=0:raise ValueError(name+' must be positive')
        if not 0<=self.dead_pwm<255:raise ValueError('dead_pwm must be in [0,255)')
        if not isinstance(self.sample_ms,int) or self.sample_ms<1:raise ValueError('sample_ms must be a positive integer')
        if not isinstance(self.latency_ms,int) or self.latency_ms<0:raise ValueError('latency_ms must be a nonnegative integer')
        if self.adc_noise<0:raise ValueError('adc_noise must be nonnegative')


def nearest(x, y, points):
    best = (float('inf'), 0.0, 0.0)
    accumulated = 0.0
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        t = max(0, min(1, ((x-ax)*dx + (y-ay)*dy) / length**2))
        d = math.hypot(x-ax-t*dx, y-ay-t*dy)
        if d < best[0]:
            best = d, accumulated + t*length, math.atan2(dy, dx)
        accumulated += length
    return best


def angle(a):
    return (a + math.pi) % (2*math.pi) - math.pi


def scenario(name):
    if name == 'straight':
        return [(0, 0), (2.1, 0)], 0, 0.0
    side = -1 if name.endswith('_right') else 1
    deg = 120 if 'v60' in name else 90 if '90' in name else 60
    rad = math.radians(deg) * side
    return [(0, 0), (1.2, 0), (1.2 + math.cos(rad)*0.9, math.sin(rad)*0.9)], rad, .045 if 'wide' in name else 0


def read_adc(x, y, heading, p, path, patch, rng):
    result = []
    for i in range(5):  # A5,A4,A3,A2,A1: left to right
        lateral = (2-i)*p.sensor_spacing_m
        sx = x + p.sensor_ahead_m*math.cos(heading) - lateral*math.sin(heading)
        sy = y + p.sensor_ahead_m*math.sin(heading) + lateral*math.cos(heading)
        # Area-like footprint averaging. Intermediate readings are intentionally
        # retained; ADC thresholding is performed by the original controller.
        hits = 0
        samples = [(0,0), (p.sensor_radius_m,0), (-p.sensor_radius_m,0),
                   (0,p.sensor_radius_m), (0,-p.sensor_radius_m)]
        for ox, oy in samples:
            d, _, _ = nearest(sx+ox, sy+oy, path)
            on = d <= p.line_width_m/2
            if patch and math.hypot(sx+ox-1.2, sy+oy) < patch:
                on = True
            hits += on
        adc = p.background_adc + (p.line_adc-p.background_adc)*hits/len(samples)
        result.append(round(max(0, min(1023, adc+rng.gauss(0,p.adc_noise)))))
    return result


def wheel(v, pwm, gain, p, dt):
    # Dead zone, battery and asymmetric gain map PWM to unloaded target speed.
    drive = max(0, abs(pwm)-p.dead_pwm)/(255-p.dead_pwm)
    target = math.copysign(p.max_wheel_mps*drive*gain*p.battery_factor, pwm)
    tau = p.motor_tau_s if drive else p.coast_tau_s
    accel = (target-v)/tau
    limit = min(p.max_accel_mps2*p.battery_factor, p.friction_mu*9.81)
    accel = max(-limit, min(limit, accel)) - 9.81*math.sin(math.radians(p.grade_deg))
    return v + accel*dt


def run(controller, p, name, parameters, seed, trace_path=None):
    controller.reset(parameters)
    path, final_heading, patch = scenario(name)
    total = sum(math.dist(a,b) for a,b in zip(path,path[1:]))
    rng = random.Random(seed)
    x, y, heading = .12, .002, 0.0
    vl = vr = 0.0
    command = (0,0)
    queue = []
    trace = []
    max_error = max_speed = 0.0
    max_jump = max_yaw = 0.0
    max_coast = stop_x = stop_y = 0.0
    had_stop = False
    outcome = 'timeout'
    state = controller.state()
    off_road_ms = 0
    dt = .001
    for ms in range(0, 30001):
        if ms % p.sample_ms == 0:
            adc = read_adc(x,y,heading,p,path,patch,rng)
            queue.append((ms + p.latency_ms, adc))
        while queue and queue[0][0] <= ms:
            _, adc = queue.pop(0)
            old = command
            command = controller.step(ms, adc)
            state = controller.state()
            max_jump = max(max_jump,abs(command[0]-old[0]),abs(command[1]-old[1]))
        vl = wheel(vl,command[0],p.left_gain,p,dt)
        vr = wheel(vr,command[1],p.right_gain,p,dt)
        v = (vl+vr)/2
        omega = (vr-vl)/p.track_m
        # Lateral grip bounds the chassis yaw; excess wheel speed becomes slip.
        omega_limit = p.friction_mu*9.81/max(abs(v),.02)
        omega = max(-omega_limit,min(omega_limit,omega))
        heading += omega*dt
        x += v*math.cos(heading)*dt
        y += v*math.sin(heading)*dt
        d, progress, _ = nearest(x,y,path)
        max_error, max_speed = max(max_error,d),max(max_speed,abs(v))
        max_yaw = max(max_yaw,abs(omega))
        wheel_errors = [nearest(x-s*p.track_m/2*math.sin(heading),
                               y+s*p.track_m/2*math.cos(heading),path)[0] for s in [-1,1]]
        if max(wheel_errors)+.0075 > p.road_width_m/2:
            off_road_ms += 1
        stopped = bool(state['turnFault'] or state['lapDone'] or state['liftState']==1)
        if stopped and not had_stop:
            stop_x,stop_y,had_stop = x,y,True
        if had_stop:
            max_coast = max(max_coast,math.hypot(x-stop_x,y-stop_y))
        if ms % 10 == 0:
            trace.append(dict(ms=ms,x=x,y=y,heading=heading,vl=vl,vr=vr,
                              left=command[0],right=command[1],error=d,
                              progress=progress,**state))
        if had_stop and abs(vl)+abs(vr)<.002:
            outcome = 'fault' if state['turnFault'] else 'false_marker'
            break
        if not had_stop and progress > total-.10 and abs(angle(heading-final_heading)) < .45 and d < .04:
            outcome = 'reached'
            break
        if d > .25:
            outcome = 'escaped'
            break
    if trace_path:
        with Path(trace_path).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=trace[0].keys());writer.writeheader();writer.writerows(trace)
    return dict(scenario=name,seed=seed,outcome=outcome,seconds=ms/1000,
                max_error_m=round(max_error,4),max_speed_mps=round(max_speed,4),
                max_command_jump=max_jump,max_yaw_rps=round(max_yaw,3),
                off_assumed_road_ms=off_road_ms,coast_after_stop_m=round(max_coast,4),
                final_state=state,plant=asdict(p)),trace


def parameter_sets(count, seed=20261102):
    # Reproducible strata; bounds fit the rules' total width/length envelope,
    # but are hypothetical build dimensions and unknown motor performance.
    yield Plant()
    rng=random.Random(seed)
    for _ in range(count-1):
        yield Plant(track_m=rng.uniform(.095,.135),sensor_ahead_m=rng.uniform(.040,.085),
                    sensor_spacing_m=rng.uniform(.011,.018),max_wheel_mps=rng.uniform(.40,.85),
                    dead_pwm=rng.uniform(20,60),motor_tau_s=rng.uniform(.04,.14),
                    coast_tau_s=rng.uniform(.12,.35),max_accel_mps2=rng.uniform(1.5,4.5),
                    left_gain=rng.uniform(.9,1.1),right_gain=rng.uniform(.9,1.1),
                    battery_factor=rng.uniform(.8,1.0),friction_mu=rng.uniform(.3,.8),
                    sample_ms=rng.choice([2,5,10]),latency_ms=rng.choice([0,5,10,20]))


PROFILES = {
    'unchanged': {},
    'moderate': dict(SPEED_STRAIGHT=140,STRAIGHT_STAGE2_PWM=120,STRAIGHT_STAGE3_PWM=140,
                     SPEED_CURVE=110,TURN_KP=85,TURN_OUTER_PWM=100,TURN_INNER_PWM=95),
    'baseline_speed': dict(SPEED_STRAIGHT=100,STRAIGHT_STAGE2_PWM=100,STRAIGHT_STAGE3_PWM=100,
                           SPEED_CURVE=100,TURN_KP=75,TURN_OUTER_PWM=100,TURN_INNER_PWM=95),
    'gentle_accel': dict(STRAIGHT_STAGE2_PWM=120,STRAIGHT_STAGE3_PWM=150,SPEED_STRAIGHT=180,
                         STRAIGHT_STAGE2_MS=400,STRAIGHT_STAGE3_MS=900,STRAIGHT_STAGE4_MS=1500),
    'slower_entry': dict(STRAIGHT_STAGE2_PWM=120,STRAIGHT_STAGE3_PWM=150,SPEED_STRAIGHT=150),
}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build-output/physics')
    parser.add_argument('--samples',type=int,default=8)
    parser.add_argument('--seed',type=int,default=20261102)
    parser.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=list(PROFILES))
    parser.add_argument('--models',nargs='+',choices=['stable','simplified'],default=['stable','simplified'])
    parser.add_argument('--candidate',type=Path,help='Additional vendor-exported INO; no runtime parameter overrides')
    parser.add_argument('--reference-source',type=Path,help='Use this INO instead of pinned46bad64 for the simplified reference')
    parser.add_argument('--plant-json',type=Path,help='JSON object of measured Plant field overrides; stored with results')
    args=parser.parse_args()
    if args.samples < 1:
        parser.error('--samples must be positive')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    overrides=json.loads(args.plant_json.read_text(encoding='utf-8')) if args.plant_json else {}
    if not isinstance(overrides,dict):parser.error('--plant-json must contain an object')
    replace(Plant(),**overrides)  # Validate names, units and nonzero time step.
    models={}
    for name,ref in [('stable','v0.4.0'),('simplified','46bad64')]:
        if name not in args.models:continue
        source=output/(name+'.ino')
        if name=='simplified' and args.reference_source:
            source.write_bytes(args.reference_source.read_bytes())
        else:
            result=subprocess.run(['git','show',ref+':car.ino'],cwd=ROOT,capture_output=True,check=True)
            source.write_bytes(result.stdout)
        dll,digest=build(source,output/'native'/name)
        models[name]=(Controller(dll),digest)
    if args.candidate:
        dll,digest=build(args.candidate,output/'native/generated_candidate')
        models['generated_candidate']=(Controller(dll),digest)
    scenarios=['straight']+[base+side for base in ['turn60','turn90','v60','wide_turn60','wide_v60'] for side in ['_left','_right']]
    results=[];traces={}
    for model,(controller,digest) in models.items():
        profiles={k:PROFILES[k] for k in args.profiles} if model=='simplified' else {'unchanged':{}}
        for profile,parameters in profiles.items():
            for i,p in enumerate(parameter_sets(args.samples,args.seed)):
                p=replace(p,**overrides)
                for name in scenarios:
                    label='%s-%s-%s-%d'%(model,profile,name,i)
                    row,trace=run(controller,p,name,parameters,i,output/(label+'.csv') if i==0 else None)
                    row.update(model=model,profile=profile,source_sha256=digest,parameters=parameters)
                    results.append(row)
                    if i==0:traces[label]=trace
            subset=[r for r in results if r['model']==model and r['profile']==profile]
            print(model,profile,{n:sum(r['outcome']==n for r in subset) for n in ['reached','fault','false_marker','escaped','timeout']},flush=True)
    payload=dict(model='assumed planar differential-drive sensitivity model; not calibrated',
                 source='actual vendor-exported sketch in MSVC host DLL; no hardware I/O',
                 seed=args.seed,samples=args.samples,plant_overrides=overrides,
                 sampling_note='One shared nominal set plus seed-specific random sets; not empirical probabilities.',
                 results=results)
    (output/'results.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print('Results:',output/'results.json',flush=True)


if __name__=='__main__':
    main()
