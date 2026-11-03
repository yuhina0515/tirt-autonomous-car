"""Recompute course evidence from pose traces, never controller completion flags."""
import csv
import bisect
import hashlib
import math
from collections import deque
from dataclasses import replace
import random
from pathlib import Path

from course_world import Course, Mechanisms, Pose, crossed_gate, geometry, advance,chassis_pitch,sense,forward_travel

REQUIRED_COLUMNS={'ms','x','y','z','yaw','pitch','vl','vr','left','right','turnFault','intervention'}


def crossed_route_gate(course,station,previous,current):
    """Use the directed tangent bisector at vertices, not the incoming ray.

    An axle rounding a legal corner can remain behind the incoming endpoint
    plane forever. The bisector separates incoming and outgoing route strips.
    Width, height, positive crossing and ordered-gate requirements remain; this
    is model progress geometry, not an official checkpoint-placement claim.
    Straight-interior/start/finish gates keep their original tangent plane.
    """
    i=bisect.bisect_left(course.stations,station)
    if not (0<i<len(course.main_segments) and abs(course.stations[i]-station)<1e-9):
        return crossed_gate(course,station,previous,current)
    incoming,outgoing=course.main_segments[i-1:i+1]
    nx=(incoming.b[0]-incoming.a[0])/incoming.length+(outgoing.b[0]-outgoing.a[0])/outgoing.length
    ny=(incoming.b[1]-incoming.a[1])/incoming.length+(outgoing.b[1]-outgoing.a[1])/outgoing.length
    length=math.hypot(nx,ny)
    if length<1e-9:
        # An exact reversal has no unique bisector. Preserve the original rule
        # rather than silently accepting a U-turn with no route evidence.
        return crossed_gate(course,station,previous,current)
    nx/=length;ny/=length
    point,_=course.at(station)
    before=(previous.x-point[0])*nx+(previous.y-point[1])*ny
    after=(current.x-point[0])*nx+(current.y-point[1])*ny
    if not before<=0<after:return False
    t=-before/(after-before)
    x=previous.x+t*(current.x-previous.x);y=previous.y+t*(current.y-previous.y)
    z=previous.z+t*(current.z-previous.z)
    lateral=abs(-(x-point[0])*ny+(y-point[1])*nx)
    return lateral<course.assumptions['road_width_m']/2 and abs(z-point[2])<.03


def directed_travel(course,previous,current,mechanisms,next_gate,tolerance_m=1e-6):
    """Disambiguate route occurrence using the referee's ordered gate history.

    Physical proximity alone cannot identify opposing overlapping occurrences.
    Only the expected segment and its two immediate neighbors supply tangents;
    height, distance, negative-progress and ordered-gate checks still apply.
    This state belongs exclusively to the referee, never the controller.
    """
    dx,dy=current.x-previous.x,current.y-previous.y
    if math.hypot(dx,dy)<=tolerance_m:return True
    before=course.gates[next_gate-1] if next_gate else 0
    after=course.gates[next_gate] if next_gate<len(course.gates) else course.length
    expected=min(len(course.main_segments)-1,bisect.bisect_right(course.stations,(before+after)/2)-1)
    x,y,z=(current.x+previous.x)/2,(current.y+previous.y)/2,(current.z+previous.z)/2
    eligible=[p for p in course.projections(x,y,mechanisms) if p['s']>=0 and
        abs(p['index']-expected)<=1 and p['d']<course.assumptions['body_width_m']/2 and abs(p['z']-z)<.03]
    for p in eligible:
        seg=course.main_segments[p['index']]
        if (dx*(seg.b[0]-seg.a[0])+dy*(seg.b[1]-seg.a[1]))/seg.length>=-tolerance_m:return True
    return False


def audit_trace(path,course_spec,plant,lift_duration,expected_hash=None):
    path=Path(path)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_hash is not None and digest!=expected_hash:
        raise ValueError('trace hash mismatch')
    with path.open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    if len(rows)<2:
        raise ValueError('trace requires at least two poses')
    if not REQUIRED_COLUMNS.issubset(rows[0]):
        raise ValueError('trace lacks required physical/control columns')
    c=Course(course_spec)
    m=Mechanisms(c,lift_duration)
    previous=None
    previous_ms=None
    previous_contact=None
    next_gate=0
    start_ms=finish_ms=None
    body_ok=wheels_ok=layer_ok=no_fault=True
    direction_ok=True
    seesaw_entered=seesaw_exited=lift_entered=lift_exited=False
    mechanism_violation=False
    seen_seesaw_negative=False
    fault=None
    first_violation_ms=None
    gate_events=[]
    times=[]
    still_since=None
    for row in rows:
        numeric={k:float(v) for k,v in row.items()}
        if not all(math.isfinite(v) for v in numeric.values()):
            raise ValueError('nonfinite trace value')
        ms=numeric['ms']
        if ms<0 or (previous_ms is not None and not 0<ms-previous_ms<=10):
            raise ValueError('nonmonotonic or undersampled trace')
        pose=Pose(*(numeric[k] for k in ('x','y','z','yaw','pitch','vl','vr')))
        if previous is None:
            initial,yaw=c.at(0)
            if ms!=0 or math.hypot(pose.x-initial[0],pose.y-initial[1])>.002 or abs(pose.z-initial[2])>.0001 or abs(pose.yaw-yaw)>.01 or max(abs(pose.vl),abs(pose.vr))>0:
                raise ValueError('trace does not start at the declared stationary initial pose')
        if previous is not None:
            direction_ok &= directed_travel(c,previous,pose,m,next_gate)
            # Independently evolve the mechanisms from observed physical contact.
            dt=(ms-previous_ms)/1000
            old_height=m.lift_height
            on_lift=m.step(dt,previous_contact['s'] if previous_contact else -1,
                          (previous.vl,previous.vr),previous_contact is not None)
            predicted=replace(previous)
            if on_lift:predicted.z+=m.lift_height-old_height
            support=c.contact(predicted.x,predicted.y,predicted.z,m,max_step=.03)
            if support:
                advance(predicted,previous_command,plant,support,dt)
                if any(abs(getattr(predicted,k)-getattr(pose,k))>.00005 for k in ('x','y','yaw','vl','vr')):
                    raise ValueError('trace pose/velocity disagrees with wheel dynamics')
        contact=c.contact(pose.x,pose.y,pose.z,m,max_step=.03)
        if contact is None:
            layer_ok=False
        elif abs(contact['z']-pose.z)>.00005 or abs(chassis_pitch(c,m,pose)-pose.pitch)>.00005:
            raise ValueError('trace height/pitch disagrees with physical support')
        g=geometry(c,m,pose,plant)
        if previous is not None:
            # Sweep between stored poses at <=1mm / 0.01rad resolution rather
            # than allowing a brief wheel departure between valid endpoints.
            distance=math.hypot(pose.x-previous.x,pose.y-previous.y)
            count=max(1,math.ceil(distance/.001),math.ceil(abs(pose.yaw-previous.yaw)/.01))
            for part in range(1,count):
                t=part/count
                interpolated=Pose(*(getattr(previous,k)+t*(getattr(pose,k)-getattr(previous,k))
                                    for k in ('x','y','z','yaw','pitch','vl','vr')))
                middle=geometry(c,m,interpolated,plant)
                g['body_line'] &= middle['body_line']
                g['wheel_road'] &= middle['wheel_road']
                g['ceiling_collision'] |= middle['ceiling_collision']
        body_ok &= g['body_line']
        wheels_ok &= g['wheel_road']
        layer_ok &= not g['ceiling_collision']
        no_fault &= numeric['turnFault']==0 and numeric['intervention']==0
        if previous is not None and next_gate<len(c.gates) and crossed_route_gate(c,c.gates[next_gate],previous,pose):
            gate_events.append(dict(index=next_gate,ms=ms,station_m=c.gates[next_gate]))
            if next_gate==0:
                start_ms=ms
            next_gate+=1
            if next_gate==len(c.gates):
                finish_ms=ms
        station=contact['s'] if contact else -1
        on_real_lift=contact is not None and abs(station-c.lift_s)<=c.lift_config['half_length_m']
        if abs(pose.vl)+abs(pose.vr)<.002 and not on_real_lift:
            if still_since is None:still_since=ms
            # Official PDF p7:10s motion loss outside a legitimate mechanism stop.
            if ms-still_since>=10000:no_fault=False
        else:still_since=None
        if contact:
            if abs(station-c.seesaw_s)<=c.seesaw_config['half_length_m']:
                seesaw_entered=True
                seen_seesaw_negative |= m.theta<0
            elif seesaw_entered and station>c.seesaw_s+c.seesaw_config['half_length_m']:
                seesaw_exited=True
            on_lift=abs(station-c.lift_s)<=c.lift_config['half_length_m']
            if on_lift:
                lift_entered=True
                if m.lift_phase==1 and max(abs(pose.vl),abs(pose.vr))>c.lift_config['stop_speed_mps']+.001:
                    mechanism_violation=True
            elif lift_entered and not lift_exited:
                lift_exited=True
                if m.lift_phase!=2:
                    mechanism_violation=True
        if fault is None:
            if not layer_ok: fault='unsupported_surface_or_ceiling'
            elif not direction_ok: fault='reverse_or_wrong_branch_travel'
            elif not wheels_ok: fault='wheel_left_road'
            elif not body_ok: fault='body_lost_guide'
            elif not no_fault: fault='controller_fault_or_intervention'
            elif mechanism_violation: fault='lift_left_before_settled'
            if fault is not None:first_violation_ms=ms
        previous,previous_ms,previous_contact=pose,ms,contact
        previous_command=(numeric['left'],numeric['right'])
        times.append(ms)
    checks=dict(start_crossing=start_ms is not None,
                ordered_gate_checks=next_gate==len(c.gates),
                body_line_coverage=bool(body_ok),
                wheel_road_coverage_with_V_exception=bool(wheels_ok),
                direction_and_layer=bool(direction_ok and layer_ok and next_gate==len(c.gates)),
                shortcut_boundary=not c.spec['shortcut']['enabled'],
                seesaw_crossing=seesaw_entered and seesaw_exited and seen_seesaw_negative,
                lift_stop_and_settled_exit=lift_entered and lift_exited and m.lift_phase==2 and not mechanism_violation,
                finish_crossing=finish_ms is not None,
                no_fault_or_intervention=bool(no_fault and not mechanism_violation))
    elapsed=(finish_ms-start_ms)/1000 if finish_ms is not None and start_ms is not None else (times[-1]-times[0])/1000
    return dict(trace_sha256=digest,elapsed_s=elapsed,independent_checks=checks,
                gates_crossed=next_gate,gates_required=len(c.gates),gate_events=gate_events,
                first_violation=fault,first_violation_ms=first_violation_ms,finished=finish_ms is not None,
                mechanism_state=dict(lift_phase=m.lift_phase,lift_height_m=m.lift_height,seesaw_deg=math.degrees(m.theta)))


def verify_controller_trace(path,controller):
    """Re-execute the actual compiled core against recorded timestamped ADC."""
    controller.reset()
    command=(0,0)
    with Path(path).open(newline='',encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if int(row['ticked']):
                command=controller.step(int(row['ms']),[int(row[k]) for k in ('a5','a4','a3','a2','a1')])
            if command!=(int(row['left']),int(row['right'])):
                raise ValueError('trace commands disagree with actual native controller')
            for name,value in controller.state().items():
                if int(row[name])!=value:
                    raise ValueError('trace controller state mismatch: '+name)
            for name,value in controller.diagnostics().items():
                if int(row[name])!=value:raise ValueError('trace diagnostic mismatch: '+name)
    return True


def verify_sensor_trace(path,controller,course_spec,plant,seed,lift_duration):
    """Regenerate noise, footprint, sample and delivery times before core replay."""
    c=Course(course_spec);m=Mechanisms(c,lift_duration);rng=random.Random(seed)
    point,yaw=c.at(0)
    initial=(point[0]+rng.uniform(-.001,.001),point[1],yaw+rng.uniform(-.005,.005))
    queue=deque();delivered=[500]*5;previous=None;previous_ms=None;previous_contact=None
    controller.reset();command=(0,0)
    with Path(path).open(newline='',encoding='utf-8') as f:
        for row in csv.DictReader(f):
            ms=int(row['ms']);pose=Pose(*(float(row[k]) for k in ('x','y','z','yaw','pitch','vl','vr')))
            if previous is None:
                if any(abs(a-b)>1e-9 for a,b in zip((pose.x,pose.y,pose.yaw),initial)):
                    raise ValueError('initial pose does not match declared seed')
            else:
                m.step((ms-previous_ms)/1000,previous_contact['s'] if previous_contact else -1,
                       (previous.vl,previous.vr),previous_contact is not None)
            if ms%plant.sample_ms==0:
                queue.append((ms+plant.latency_ms,sense(c,m,pose,plant,rng)))
            ticked=0
            while queue and queue[0][0]<=ms:
                _,delivered=queue.popleft();command=controller.step(ms,delivered);ticked=1
            if ticked!=int(row['ticked']) or delivered!=[int(row[k]) for k in ('a5','a4','a3','a2','a1')]:
                raise ValueError('recorded ADC/ticks disagree with physical sensor and declared seed')
            if command!=(int(row['left']),int(row['right'])):
                raise ValueError('commands disagree with regenerated sensor/core replay')
            for name,value in controller.state().items():
                if int(row[name])!=value:raise ValueError('regenerated controller state mismatch: '+name)
            if hasattr(controller,'diagnostics'):
                for name,value in controller.diagnostics().items():
                    if int(row[name])!=value:raise ValueError('regenerated diagnostic mismatch: '+name)
            previous,previous_ms=pose,ms
            previous_contact=c.contact(pose.x,pose.y,pose.z,m,max_step=.03)
    return True
