"""Physical and referee regressions; synthetic fixtures are not vehicle laps."""
import copy
import csv
import json
import math
from pathlib import Path
import random
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from course_world import Course,Mechanisms,Pose,advance,geometry,gravity_along,sense,crossed_gate,forward_travel
from course_referee import audit_trace,verify_sensor_trace,directed_travel
from simulation_model import Plant


def fixture(points=None):
    spec=json.loads((ROOT/'simulation/reconstructed_course.json').read_text())
    spec['points_px']=points or [[100,500],[300,500],[500,500],[700,500]]
    spec['raised_occurrences']=[]
    spec['ground_from_vertex']=len(spec['points_px'])-1
    spec['ground_ramp_m']=.01
    spec['mechanisms']['seesaw']['near_px']=[400,500]
    spec['mechanisms']['seesaw']['limit_deg']=0
    spec['mechanisms']['lift']['near_px']=[600,500]
    spec['mechanisms']['lift']['occurrence_after_vertex']=0
    spec['mechanisms']['lift']['lower_landing_until_vertex']=len(spec['points_px'])-2
    spec['mechanisms']['lift']['return_deck_at_vertex']=len(spec['points_px'])-1
    return spec


class WorldChecks(unittest.TestCase):
    def test_ordered_occurrence_resolves_opposing_overlapping_guides(self):
        c=Course(json.loads((ROOT/'simulation/reconstructed_course.json').read_text()));m=Mechanisms(c,27)
        # Frozen seed702 at100530->100535ms: nearest occurrence switches118->137
        # by45micrometres despite forward progress on118 after gate117.
        a=Pose(4.208123640383324,5.334948179545477,.19,-19.019103101856636)
        b=Pose(4.2100196145709345,5.334625363783488,.19,-19.01730180570099)
        self.assertTrue(directed_travel(c,a,b,m,118))
        self.assertFalse(directed_travel(c,b,a,m,118))
        self.assertFalse(directed_travel(c,a,b,m,136))

    def test_adjacent_ramp_caps_do_not_occlude_their_own_guide(self):
        c=Course(json.loads((ROOT/'simulation/reconstructed_course.json').read_text()));m=Mechanisms(c,27)
        pose=Pose(2.0242075771164574,3.8696870155482554,.3322490660868781,-6.3441117038771,.2932694425849533)
        self.assertEqual(sense(c,m,pose,Plant(adc_noise=0),random.Random(0))[2],35)
        x,y=c.xy([700,488]);indices={p['index'] for p in c.local_surfaces(x,y,m)}
        self.assertIn(32,indices);self.assertIn(41,indices)

    def test_shared_traction_budget_under_braking_and_turning(self):
        plant=Plant(max_accel_mps2=6)
        p=Pose(0,0,0,0,vl=-1,vr=0);old=(p.vl+p.vr)/2
        advance(p,(255,255),plant,dict(gx=0,gy=0),.001)
        ax=((p.vl+p.vr)/2-old)/.001;ay=(p.vl+p.vr)/2*p.yaw/.001
        self.assertLessEqual(math.hypot(ax,ay),plant.friction_mu*9.81+1e-9)
        p=Pose(0,0,0,0,vl=-.18,vr=.20);old=(p.vl+p.vr)/2
        advance(p,(255,255),plant,dict(gx=0,gy=0),.001)
        self.assertLessEqual(math.hypot(((p.vl+p.vr)/2-old)/.001,(p.vl+p.vr)/2*p.yaw/.001),plant.friction_mu*9.81+1e-9)
        for fraction in (0,1.01):
            with self.assertRaises(ValueError):Plant(drive_normal_fraction=fraction)

    def test_seesaw_angle_matches_surface_and_projected_board_length(self):
        spec=fixture();spec['mechanisms']['seesaw']['limit_deg']=25
        c=Course(spec);m=Mechanisms(c,27)
        point,yaw=c.at(c.seesaw_s+.1)
        support=c.contact(point[0],point[1],m.pivot_height+.1*math.tan(m.theta),m)
        self.assertIsNotNone(support)
        self.assertAlmostEqual(math.degrees(gravity_along(support,yaw)),25)
        entry=c.seesaw_s-c.seesaw_config['half_length_m']*math.cos(m.theta)
        self.assertAlmostEqual(m.pivot_height-c.seesaw_config['half_length_m']*math.sin(m.theta),c.height(entry))

    def test_physical_stall_outside_platform_is_not_accepted(self):
        spec=fixture();c=Course(spec);point,yaw=c.at(0)
        a=dict(ms=0,x=point[0],y=point[1],z=point[2],yaw=yaw,pitch=0,vl=0,vr=0,left=0,right=0,turnFault=0,intervention=0)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'trace.csv'
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=a);w.writeheader()
                for ms in range(0,10006,5):w.writerow({**a,'ms':ms})
            self.assertFalse(audit_trace(p,spec,Plant(),27)['independent_checks']['no_fault_or_intervention'])

    def test_height_and_pitch_forgery_is_rejected(self):
        spec=fixture();c=Course(spec);point,yaw=c.at(0)
        a=dict(ms=0,x=point[0],y=point[1],z=point[2],yaw=yaw,pitch=0,vl=0,vr=0,left=0,right=0,turnFault=0,intervention=0)
        b={**a,'ms':5,'z':point[2]+.02,'pitch':1.5}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'trace.csv'
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=a);w.writeheader();w.writerows((a,b))
            with self.assertRaisesRegex(ValueError,'height/pitch'):audit_trace(p,spec,Plant(),27)

    def test_forged_adc_and_tick_schedule_are_rejected(self):
        spec=fixture();c=Course(spec);m=Mechanisms(c,27);plant=Plant(adc_noise=0);rng=random.Random(10)
        point,yaw=c.at(0);pose=Pose(point[0]+rng.uniform(-.001,.001),point[1],point[2],yaw+rng.uniform(-.005,.005))
        values=sense(c,m,pose,plant,rng)
        class Dummy:
            def reset(self):pass
            def step(self,ms,adc):return (100,100)
            def state(self):return {}
        a=dict(ms=0,x=pose.x,y=pose.y,z=pose.z,yaw=pose.yaw,pitch=0,vl=0,vr=0,left=0,right=0,ticked=0,a5=500,a4=500,a3=500,a2=500,a1=500)
        b={**a,'ms':5,'ticked':1,'left':100,'right':100,**dict(zip(('a5','a4','a3','a2','a1'),values))}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'trace.csv'
            def write(row):
                with p.open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=a);w.writeheader();w.writerows((a,row))
            write(b);self.assertTrue(verify_sensor_trace(p,Dummy(),spec,plant,10,27))
            write({**b,'a4':35})
            with self.assertRaisesRegex(ValueError,'ADC/ticks'):verify_sensor_trace(p,Dummy(),spec,plant,10,27)
            write({**b,'ticked':0})
            with self.assertRaisesRegex(ValueError,'ADC/ticks'):verify_sensor_trace(p,Dummy(),spec,plant,10,27)

    def test_extra_branches_are_physical_and_visible(self):
        c=Course(json.loads((ROOT/'simulation/reconstructed_course.json').read_text()));m=Mechanisms(c,27)
        x,y=c.xy([110,855])
        self.assertIsNotNone(c.contact(x,y,0,m))
        self.assertTrue(c.white(x,y,.006,m))

    def test_spinning_cannot_trigger_lift(self):
        c=Course(fixture());m=Mechanisms(c,27)
        for _ in range(100):m.step(.005,c.lift_s,(.4,-.4))
        self.assertEqual(m.lift_phase,0)

    def test_referee_rejects_motion_without_wheel_motion_and_missing_fields(self):
        spec=fixture();c=Course(spec);point,yaw=c.at(0)
        a=dict(ms=0,x=point[0],y=point[1],z=point[2],yaw=yaw,pitch=0,vl=0,vr=0,left=0,right=0,turnFault=0,intervention=0)
        b={**a,'ms':5,'x':point[0]+.002}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'trace.csv'
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=a);w.writeheader();w.writerows((a,b))
            with self.assertRaisesRegex(ValueError,'wheel dynamics'):audit_trace(p,spec,Plant(),27)
            a.pop('turnFault');b.pop('turnFault')
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=a);w.writeheader();w.writerows((a,b))
            with self.assertRaisesRegex(ValueError,'required'):audit_trace(p,spec,Plant(),27)

    def test_mechanism_endpoints_and_caster_ramp_visibility(self):
        c=Course(json.loads((ROOT/'simulation/reconstructed_course.json').read_text()));m=Mechanisms(c,27)
        entry=c.seesaw_s-c.seesaw_config['half_length_m']
        self.assertAlmostEqual(m.pivot_height-c.seesaw_config['half_length_m']*math.sin(m.theta),c.height(entry))
        m.theta=-math.radians(c.seesaw_config['limit_deg'])
        exit=c.seesaw_s+c.seesaw_config['half_length_m']
        self.assertAlmostEqual(m.pivot_height+c.seesaw_config['half_length_m']*math.sin(m.theta),c.height(exit))
        m.lift_phase=2;m.lift_height=0
        p,_=c.at(c.lift_s+c.lift_config['half_length_m']+.000001)
        self.assertIsNotNone(c.contact(p[0],p[1],0,m))
        from course_world import chassis_pitch
        point,yaw=c.at(c.stations[18]-.02);pose=Pose(*point,yaw)
        pose.pitch=chassis_pitch(c,m,pose)
        self.assertLess(min(sense(c,m,pose,Plant(adc_noise=0),random.Random(0))[1:4]),70)

    def test_duplicate_course_vertices_rejected(self):
        with self.assertRaises(ValueError):Course(fixture([[100,500],[100,500]]))

    def test_heading_reverses_gravity_and_zero_pwm_coasts(self):
        support=dict(gx=.3,gy=0)
        self.assertAlmostEqual(gravity_along(support,0),-gravity_along(support,math.pi))
        uphill=Pose(0,0,0,0,vl=.2,vr=.2);downhill=Pose(0,0,0,math.pi,vl=.2,vr=.2)
        advance(uphill,(0,0),Plant(),support,.001);advance(downhill,(0,0),Plant(),support,.001)
        self.assertGreater(uphill.vl,0)
        self.assertLess(uphill.vl,downhill.vl)

    def test_sensor_does_not_see_lower_crossing(self):
        # Two crossing roads, separated in height and connected far away.
        s=fixture([[100,500],[500,500],[500,900],[300,900],[300,100]])
        c=Course(s)
        from course_world import Segment
        # Local geometry fixture: horizontal upper strip, vertical lower strip.
        c.segments=[Segment(0,(.5,3.5,.19),(2.5,3.5,.19),0,2),
                    Segment(1,(1.5,2.5,0),(1.5,4.5,0),-100,2)]
        c.grid={}
        for ix in range(0,12):
            for iy in range(8,20):c.grid[(ix,iy)]=c.segments
        m=Mechanisms(c,27);m.theta=0
        # Off the upper centerline but on the hidden lower line: still background.
        self.assertFalse(c.white(1.5,3.53,.196,m))
        self.assertTrue(c.white(1.5,3.5,.196,m))
        self.assertTrue(c.white(1.5,3.53,.006,m))

    def test_seesaw_torque_reverses_and_angle_is_bounded(self):
        s=fixture();s['mechanisms']['seesaw']['limit_deg']=25
        c=Course(s);a=Mechanisms(c,27);b=Mechanisms(c,27)
        a.theta=b.theta=0
        for _ in range(100):
            a.step(.005,c.seesaw_s+.2,(0,0));b.step(.005,c.seesaw_s-.2,(0,0))
        self.assertLess(a.theta,0);self.assertGreater(b.theta,0)
        self.assertLessEqual(abs(a.theta),math.radians(25))
        self.assertAlmostEqual(a.theta,-b.theta)

    def test_lift_stop_transport_and_settled_endpoint(self):
        c=Course(fixture());m=Mechanisms(c,27)
        initial=m.lift_height
        for _ in range(40):m.step(.005,c.lift_s,(.02,.02))
        self.assertEqual(m.lift_phase,0)
        for _ in range(20):m.step(.005,c.lift_s,(0,0))
        self.assertEqual(m.lift_phase,1)
        for _ in range(2700):m.step(.005,c.lift_s,(0,0))
        self.assertGreater(m.lift_height,0);self.assertLess(m.lift_height,initial)
        for _ in range(2800):m.step(.005,c.lift_s,(0,0))
        self.assertEqual(m.lift_phase,2)
        self.assertAlmostEqual(m.lift_height,0)
        x,y,_=c.at(c.lift_s)[0]
        self.assertIsNotNone(c.contact(x,y,0,m))
        self.assertIsNone(c.contact(x,y,initial,m))

    def test_wheel_departure_and_wrong_direction_gate_are_rejected(self):
        c=Course(fixture());m=Mechanisms(c,27);point,yaw=c.at(.5)
        pose=Pose(point[0],point[1]+.06,point[2],yaw)
        self.assertFalse(geometry(c,m,pose,Plant())['wheel_road'])
        a=Pose(point[0]-.01,point[1],point[2],yaw)
        b=Pose(point[0]+.01,point[1],point[2],yaw)
        self.assertTrue(crossed_gate(c,.5,a,b));self.assertFalse(crossed_gate(c,.5,b,a))
        self.assertTrue(forward_travel(c,a,b,m));self.assertFalse(forward_travel(c,b,a,m))

    def test_integration_converges_with_smaller_step(self):
        def simulate(dt):
            p=Pose(0,0,0,0)
            for _ in range(round(1/dt)):advance(p,(140,150),Plant(),dict(gx=0,gy=0),dt)
            return p
        a,b=simulate(.005),simulate(.001)
        self.assertLess(math.hypot(a.x-b.x,a.y-b.y),.003)
        self.assertLess(abs(a.yaw-b.yaw),.004)

    def test_referee_rejects_fake_done_and_nonmonotonic_trace(self):
        spec=fixture();c=Course(spec);point,yaw=c.at(0)
        row=dict(ms=0,x=point[0],y=point[1],z=point[2],yaw=yaw,pitch=0,vl=0,vr=0,left=0,right=0,turnFault=0,lapDone=1,intervention=0)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'trace.csv'
            def write(times):
                with p.open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=row);w.writeheader()
                    for t in times:w.writerow({**row,'ms':t})
            write([0,5,10])
            r=audit_trace(p,spec,Plant(),27)
            self.assertFalse(r['finished']);self.assertFalse(r['independent_checks']['ordered_gate_checks'])
            with self.assertRaises(ValueError):audit_trace(p,spec,Plant(),27,'a'*64)
            write([0,5,5])
            with self.assertRaises(ValueError):audit_trace(p,spec,Plant(),27)


if __name__=='__main__':unittest.main()
