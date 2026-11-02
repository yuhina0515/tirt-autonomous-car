"""Checks of model invariants and actual-sketch replay; no vehicle acceptance."""
import math
from pathlib import Path
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from physics_sim import Plant, nearest, read_adc, wheel
from sim_native import Controller, build


class PlantChecks(unittest.TestCase):
    def test_dead_zone_and_battery(self):
        p=Plant()
        self.assertEqual(wheel(0,20,1,p,.001),0)
        self.assertGreater(wheel(0,100,1,p,.1),0)
        from dataclasses import replace
        self.assertLess(wheel(.2,100,1,replace(p,battery_factor=.8),.001),wheel(.2,100,1,p,.001))

    def test_pwm_zero_coasts_and_acceleration_is_bounded(self):
        p=Plant()
        v=wheel(.3,0,1,p,.001)
        self.assertGreater(v,0)
        self.assertLess(v,.3)
        self.assertLessEqual(wheel(0,230,1,p,.001),p.max_accel_mps2*.001)

    def test_sensor_projection_uses_geometry(self):
        p=Plant(adc_noise=0)
        path=[(0,0),(2,0)]
        center=read_adc(.3,0,0,p,path,0,random.Random(1))
        self.assertEqual(center,[500,500,35,500,500])
        a=read_adc(.3,.014,0,p,path,0,random.Random(1))
        b=read_adc(.3,-.014,0,p,path,0,random.Random(1))
        self.assertEqual(a,list(reversed(b)))
        self.assertEqual(nearest(.5,.1,path)[:2],(.1,.5))

    def test_invalid_model_parameters_fail_early(self):
        for parameters in [dict(sample_ms=0),dict(dead_pwm=255),dict(track_m=0),dict(adc_noise=-1)]:
            with self.assertRaises(ValueError):Plant(**parameters)


@unittest.skipUnless(sys.platform=='win32', 'Actual-sketch bridge currently requires Windows/MSVC')
class ActualSketchReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dll,_=build(ROOT/'car.ino',ROOT/'build-output/physics/native/regression')
        cls.c=Controller(dll)

    def setUp(self):
        self.c.reset()

    def test_reset_replays_identically(self):
        traces=[]
        for _ in range(2):
            self.c.reset()
            traces.append([self.c.step(ms,[500,500,35,500,500]) for ms in range(5,1001,5)])
        self.assertEqual(traces[0],traces[1])

    def test_wide_does_not_directly_trigger_marker_stop(self):
        for ms in range(5,201,5):self.c.step(ms,[500,500,35,500,500])
        for ms in range(205,1501,5):
            self.c.step(ms,[500,35,35,35,500])
            self.assertEqual(self.c.state()['turnFault'],0)
            self.assertEqual(self.c.state()['liftState'],0)
        self.c.step(1505,[500,500,35,500,500])
        self.assertEqual(self.c.state()['liftState'],1)

    def test_valid_side_line_does_not_start_reverse_search(self):
        for ms in range(5,501,5):
            l,r=self.c.step(ms,[500,35,500,500,500])
            self.assertGreaterEqual(l,0);self.assertGreaterEqual(r,0)
            self.assertEqual(self.c.state()['turnActive'],0)

    def test_returning_line_at_gap_deadline_is_allowed_to_confirm(self):
        for mask in [2,4,6,8,12]:
            self.c.reset(dict(gapActive=1,gapAt=0,LOSS_STOP_ENABLED=1))
            adc=[500,35 if mask&8 else 500,35 if mask&4 else 500,35 if mask&2 else 500,500]
            for ms in [120,125,130]:
                l,r=self.c.step(ms,adc)
                self.assertEqual(self.c.state()['turnFault'],0)
                self.assertGreaterEqual(l,0);self.assertGreaterEqual(r,0)
            self.assertEqual(self.c.state()['gapActive'],1)
            self.c.step(135,adc)
            self.assertEqual(self.c.state()['gapActive'],0)

    def test_invalid_gap_deadline_still_stops_and_preserves_stop_output(self):
        self.c.reset(dict(gapActive=1,gapAt=0,LOSS_STOP_ENABLED=1))
        self.assertEqual(self.c.step(120,[500]*5),(0,0))
        self.assertEqual(self.c.state()['turnFault'],1)
        self.assertEqual(self.c.state()['firstFaultF'],0)
        self.assertGreater(self.c.state()['firstFaultLine'],0)

    def test_gap_to_wide_preserves_recovery_at_deadline(self):
        self.c.reset(dict(gapActive=1,gapAt=0,gapDirection=-1,gapDirectionAt=100))
        self.c.step(120,[500,35,35,35,500])
        self.assertEqual(self.c.state()['turnFault'],0)
        self.assertEqual(self.c.state()['gapActive'],0)
        self.assertEqual(self.c.state()['cornerWideRecovery'],1)


if __name__=='__main__':unittest.main()
