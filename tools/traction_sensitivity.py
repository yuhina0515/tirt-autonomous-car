"""Declared force/load hypotheses, not measurements or lateral-stability proof."""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

from course_world import Pose,advance
from simulation_model import Plant,wheel


def evaluate():
    rows=[];circle=[]
    for fraction in (.70,.85,1.0):
        p=Plant(max_accel_mps2=6,right_gain=1,drive_normal_fraction=fraction)
        for grade in (0,17.5712587783,25):
            for pwm in (100,150,230):
                pose=Pose(0,0,0,0)
                support=dict(gx=math.tan(math.radians(grade)),gy=0)
                for _ in range(2000):advance(pose,(pwm,pwm),p,support,.001)
                rows.append(dict(drive_normal_fraction=fraction,grade_deg=grade,pwm=pwm,
                    final_velocity_mps=(pose.vl+pose.vr)/2,x_m=pose.x,
                    friction_climb_possible=p.friction_mu*fraction>=math.tan(math.radians(grade))))
        pose=Pose(0,0,0,0,vl=-.18,vr=.20);initial=(pose.vl+pose.vr)/2
        advance(pose,(255,255),p,dict(gx=0,gy=0),.001)
        ax=((pose.vl+pose.vr)/2-initial)/.001
        ay=(pose.vl+pose.vr)/2*pose.yaw/.001;budget=p.friction_mu*9.81*fraction
        combined=math.hypot(ax,ay)
        if combined>budget+1e-9:raise ValueError('shared traction budget exceeded')
        # Same load fraction must also constrain the standalone plant path.
        one_step=wheel(0,255,1,p,.001)/.001
        if one_step>budget+1e-9:raise ValueError('standalone traction budget exceeded')
        circle.append(dict(drive_normal_fraction=fraction,combined_accel_mps2=combined,budget_mps2=budget))
    root=Path(__file__).resolve().parents[1]
    return dict(status='uncalibrated_constrained_longitudinal_model',duration_s=2,step_s=.001,
        reference_plant=asdict(Plant(max_accel_mps2=6,right_gain=1)),rows=rows,shared_circle=circle,
        model_sha256={n:hashlib.sha256((root/'tools'/n).read_bytes()).hexdigest() for n in ('course_world.py','simulation_model.py')},
        limitations=['No lateral gravity/slip, tire-specific forces or drivetrain holding model.',
            'Load fraction also scales modeled turning grip; caster contribution is unresolved.',
            'Fixed25-degree support is not a moving seesaw; this does not prove whole-course infeasibility.'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();payload=evaluate();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print('Wrote',len(payload['rows']),'force scenarios and3 shared-budget checks to',args.output)


if __name__=='__main__':main()
