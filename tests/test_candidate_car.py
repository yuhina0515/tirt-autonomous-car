"""Actual experimental core inputs, separate from historical parity contracts."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from sim_native import build,Controller
from learn_course_mission import stage_profile,feature_identity,MODELS,sha
import json


@unittest.skipUnless(sys.platform=='win32','Actual host bridge requires MSVC')
class CandidateChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dll,_=build(ROOT/'firmware/candidate_car/candidate_car.ino',ROOT/'build-output/control-recovery/unit-host')
        cls.c=Controller(dll)

    def setUp(self):self.c.reset()

    def test_gray_preview_steers_before_binary_mask_changes(self):
        for ms in range(0,201,5):left,right=self.c.step(ms,[500,130,35,500,500])
        self.assertEqual(self.c.state()['sensorF'],4)
        self.assertLess(left,right)
        self.assertLess(self.c.diagnostics()['linePosition'],0)

    def test_partial_center_is_not_binary_loss(self):
        for ms in range(0,201,5):command=self.c.step(ms,[500,500,200,500,500])
        self.assertEqual(self.c.state()['sensorF'],0)
        self.assertEqual(self.c.state()['turnActive'],0)
        self.assertGreater(min(command),0)

    def test_broad_event_does_not_implicitly_arm_lift(self):
        for ms in range(0,101,5):self.c.step(ms,[500,500,35,500,500])
        for ms in range(105,151,5):self.c.step(ms,[35]*5)
        self.c.step(155,[500,500,35,500,500])
        self.assertEqual(self.c.diagnostics()['wideEvents'],1)
        self.assertEqual(self.c.state()['liftState'],0)
        self.assertEqual(self.c.diagnostics()['markerArmed'],0)

    def test_short_signal_blips_cannot_reset_uncertainty_deadline(self):
        self.c.step(0,[500,500,35,500,500])
        for ms in range(5,805,5):self.c.step(ms,[500,500,35,500,500] if ms%100==0 else [500]*5)
        self.assertEqual(self.c.step(805,[500]*5),(0,0))
        self.assertEqual(self.c.state()['turnFault'],1)

    def test_outer_only_visibility_cannot_renew_inner_confidence(self):
        for ms in range(0,805,5):self.c.step(ms,[35,500,500,500,35])
        self.assertEqual(self.c.state()['turnFault'],1)
        self.assertEqual(self.c.step(805,[35,500,500,500,35]),(0,0))

    def test_separated_inner_peaks_are_not_confident_center(self):
        for ms in range(0,805,5):self.c.step(ms,[500,35,500,35,500])
        self.assertEqual(self.c.state()['turnFault'],1)
        self.assertEqual(self.c.state()['splitActive'],1)


@unittest.skipUnless(sys.platform=='win32','Actual host bridge requires MSVC')
class _MissionHarness(unittest.TestCase):
    SOURCE=ROOT/'firmware/candidate_car/candidate_car.ino'
    @classmethod
    def setUpClass(cls):
        cls.controllers=[]
        source=cls.SOURCE
        course=sha(ROOT/'simulation/reconstructed_course.json')
        for name,words in [('lift',[['LIFT']]),('ambiguous',[['LIFT'],['W','LIFT']]),('mismatch',[['L','LIFT']])]:
            out=ROOT/'build-output/control-recovery/unit-mission'/cls.__name__/name
            out.mkdir(parents=True,exist_ok=True)
            profile=dict(course_sha256=course,feature_sha256=feature_identity(source),
                         sensor_model_sha256={n:sha(ROOT/n) for n in MODELS},words=words)
            path=out/'profile.json';path.write_text(json.dumps(profile),encoding='utf-8')
            staged=stage_profile(source,out/'source',path,course)
            dll,_=build(staged,out/'host');cls.controllers.append(Controller(dll))

    def setUp(self):
        for c in self.controllers:c.reset()

    def enter(self,c):
        for ms in range(0,101,5):c.step(ms,[500,500,35,500,500])
        for ms in range(105,151,5):c.step(ms,[35]*5)
        c.step(155,[500,500,35,500,500])


class MissionChecks(_MissionHarness):

    def test_lift_resumes_after_full_wait_without_stale_uncertainty(self):
        c=self.controllers[0];self.enter(c)
        self.assertEqual(c.state()['liftState'],1)
        for ms in range(160,31156,5):self.assertEqual(c.step(ms,[500,500,35,500,500]),(0,0))
        self.assertEqual(c.state()['liftState'],2)
        for ms in range(31160,31261,5):c.step(ms,[500,500,35,500,500])
        self.assertEqual(c.state()['liftState'],3)
        self.assertEqual(c.state()['turnFault'],0)

    def test_lift_exit_requires_line_and_keeps_absolute_deadline(self):
        c=self.controllers[0];self.enter(c)
        for ms in range(160,31156,5):c.step(ms,[500]*5)
        for ms in range(31160,31401,5):c.step(ms,[500]*5)
        self.assertEqual(c.state()['liftState'],2)
        self.assertEqual(c.state()['turnFault'],0)
        for ms in range(31405,32661,5):c.step(ms,[500]*5)
        self.assertEqual(c.state()['turnFault'],1)
        self.assertNotEqual(c.state()['liftState'],3)

    def test_ambiguous_lift_vs_ordinary_white_event_stops(self):
        c=self.controllers[1];self.enter(c)
        self.assertEqual(c.state()['turnFault'],1)
        self.assertEqual(c.diagnostics()['missionAmbiguous'],1)
        self.assertEqual(c.state()['liftState'],0)

    def test_mismatched_prefix_refuses_lift(self):
        c=self.controllers[2];self.enter(c)
        self.assertEqual(c.state()['liftState'],0)
        self.assertEqual(c.diagnostics()['markerArmed'],0)
        self.assertEqual(c.diagnostics()['missionPhase'],5)

    def test_opposite_inner_signal_cannot_trigger_post_lift_pivot(self):
        c=self.controllers[0];self.enter(c)
        for ms in range(160,31261,5):c.step(ms,[500,500,35,500,500])
        for ms in range(31265,31566,5):c.step(ms,[500,500,35,130,500])
        self.assertEqual(c.state()['turnDirection'],1)
        for ms in range(31570,31641,5):command=c.step(ms,[35,190,35,200,500])
        self.assertEqual(c.state()['cornerWideRecovery'],0)
        self.assertGreaterEqual(min(command),0)


class PreviewRecoveryChecks(_MissionHarness):
    # Rejected full-course experiment: functional tests do not imply adoption.
    SOURCE=ROOT/'firmware/experiments/preview_recovery/preview_recovery.ino'

    def ready_corner(self,c,side):
        self.enter(c)
        for ms in range(160,31261,5):c.step(ms,[500,500,35,500,500])
        gray=[500,130,35,500,500] if side<0 else [500,500,35,130,500]
        for ms in range(31265,31566,5):c.step(ms,gray)
        hint=[35,35,35,500,500] if side<0 else [500,500,35,35,35]
        for ms in range(31570,31641,5):c.step(ms,hint)
        self.assertEqual(c.state()['cornerWideRecovery'],1)
        self.assertEqual(c.state()['turnActive'],1)
        return 31645

    def test_post_lift_preview_slows_both_mirrored_approaches(self):
        c=self.controllers[0]
        for side in (-1,1):
            with self.subTest(side=side):
                c.reset();self.enter(c)
                for ms in range(160,31261,5):c.step(ms,[500,500,35,500,500])
                preview=[280,280,35,500,500] if side<0 else [500,500,35,280,280]
                for ms in range(31265,31366,5):command=c.step(ms,preview)
                self.assertEqual(c.state()['straightPwm'],100)
                self.assertGreaterEqual(min(command),0)
                self.assertEqual(c.state()['cornerWideRecovery'],0)

    def test_narrow_reacquisition_leaves_pivot_before_confidence_renews(self):
        c=self.controllers[0]
        for side in (-1,1):
            with self.subTest(side=side):
                c.reset();ms=self.ready_corner(c,side)
                before=c.diagnostics()['uncertaintyMs']
                c.step(ms,[500,500,35,500,500])
                self.assertEqual(c.state()['turnActive'],0)
                self.assertEqual(c.state()['cornerWideRecovery'],1)
                self.assertGreater(c.diagnostics()['uncertaintyMs'],before)
                for at in range(ms+5,ms+21,5):c.step(at,[500,500,35,500,500])
                self.assertEqual(c.state()['cornerWideRecovery'],0)
                self.assertEqual(c.diagnostics()['uncertaintyMs'],0)

    def test_opposite_inner_peak_ends_pivot_without_clearing_episode(self):
        c=self.controllers[0]
        for side in (-1,1):
            with self.subTest(side=side):
                c.reset();ms=self.ready_corner(c,side)
                opposite=[500,500,500,35,500] if side<0 else [500,35,500,500,500]
                for at in range(ms,ms+101,5):c.step(at,opposite)
                self.assertEqual(c.state()['turnActive'],0)
                self.assertEqual(c.state()['cornerWideRecovery'],1)
                self.assertGreater(c.diagnostics()['uncertaintyMs'],100)
                self.assertEqual(c.state()['turnFault'],0)

    def test_opposite_corner_hint_cannot_restart_episode_or_deadline(self):
        c=self.controllers[0];ms=self.ready_corner(c,-1)
        for at in range(ms,ms+751,5):
            command=c.step(at,[500,500,35,35,35])
            if c.state()['turnFault']:break
            self.assertEqual(c.state()['turnActive'],0)
            self.assertEqual(c.state()['cornerWideRecovery'],1)
        self.assertEqual(c.state()['turnFault'],1)
        self.assertEqual(command,(0,0))


class OrderedRecoveryChecks(_MissionHarness):
    SOURCE=ROOT/'firmware/experiments/ordered_recovery/ordered_recovery.ino'
    ready_corner=PreviewRecoveryChecks.ready_corner

    def test_entry_center_cannot_confirm_a_return_without_departure(self):
        c=self.controllers[0];ms=self.ready_corner(c,-1)
        for at in range(ms,ms+101,5):c.step(at,[500,500,35,500,500])
        self.assertEqual(c.state()['cornerWideRecovery'],1)
        self.assertEqual(c.state()['turnActive'],1)
        self.assertGreater(c.diagnostics()['uncertaintyMs'],100)

    def test_chosen_side_return_softens_pivot_then_center_confirms(self):
        c=self.controllers[0]
        for side in (-1,1):
            with self.subTest(side=side):
                c.reset();ms=self.ready_corner(c,side)
                for at in range(ms,ms+21,5):c.step(at,[500]*5)
                outer=[35,500,500,500,500] if side<0 else [500,500,500,500,35]
                for at in range(ms+25,ms+86,5):command=c.step(at,outer)
                self.assertEqual(c.state()['turnActive'],0)
                self.assertEqual(c.state()['cornerWideRecovery'],1)
                self.assertEqual(c.state()['straightPwm'],90)
                self.assertGreater(min(command),0)
                inner=[500,35,500,500,500] if side<0 else [500,500,500,35,500]
                for at in range(ms+90,ms+111,5):c.step(at,inner)
                for at in range(ms+115,ms+136,5):c.step(at,[500,500,35,500,500])
                self.assertEqual(c.state()['cornerWideRecovery'],0)
                self.assertEqual(c.diagnostics()['uncertaintyMs'],0)

    def test_wrong_side_then_center_cannot_renew_deadline(self):
        c=self.controllers[0];ms=self.ready_corner(c,-1)
        for at in range(ms,ms+21,5):c.step(at,[500]*5)
        for at in range(ms+25,ms+106,5):c.step(at,[500,500,500,35,35])
        for at in range(ms+110,ms+751,5):command=c.step(at,[500,500,35,500,500])
        self.assertEqual(c.state()['turnFault'],1)
        self.assertEqual(command,(0,0))

    def test_opposite_error_does_not_reverse_frozen_capture_direction(self):
        c=self.controllers[0];ms=self.ready_corner(c,-1)
        for at in range(ms,ms+21,5):c.step(at,[500]*5)
        for at in range(ms+25,ms+86,5):c.step(at,[35,500,500,500,500])
        for at in range(ms+90,ms+191,5):c.step(at,[500,500,500,35,500])
        self.assertEqual(c.state()['turnDirection'],-1)
        self.assertEqual(c.state()['turnActive'],0)
        self.assertEqual(c.state()['cornerWideRecovery'],1)
        self.assertGreater(c.diagnostics()['uncertaintyMs'],190)


if __name__=='__main__':unittest.main()
