"""Teacher-label and data-leak boundaries, not vehicle completion evidence."""
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from course_world import Course
from simulation_model import Plant
from learn_junction_context import junction_observation,junction_turn,training_seed,audit_teacher
from learn_course_mission import sha


class JunctionTeacherChecks(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads((ROOT/'simulation/reconstructed_course.json').read_text())
        self.course=Course(self.spec);self.plant=Plant()

    def test_label_uses_sensor_pose_and_order_not_csv_station(self):
        c=self.course;point,yaw=c.at(c.stations[198]);p=self.plant
        row=dict(ms=100,x=point[0]-p.sensor_ahead_m*math.cos(yaw),
            y=point[1]-p.sensor_ahead_m*math.sin(yaw),z=point[2],yaw=yaw,liftState=3,station=-999)
        gates=[dict(ms=0) for _ in c.gates]
        self.assertTrue(junction_observation(row,c,gates,p,198))
        row['station']=c.stations[198];row['x']-=1
        self.assertFalse(junction_observation(row,c,gates,p,198))
        row['x']+=1;row['yaw']+=math.pi
        self.assertFalse(junction_observation(row,c,gates,p,198))
        row['yaw']=yaw;row['liftState']=2
        self.assertFalse(junction_observation(row,c,gates,p,198))
        row['liftState']=3
        self.assertFalse(junction_observation(row,c,[],p,198))

    def test_exit_direction_is_derived_from_model_tangents(self):
        self.assertEqual(junction_turn(self.course,198),'R')
        self.assertEqual(junction_turn(self.course,194),'L')
        for vertex in (0,True,999):
            with self.subTest(vertex=vertex),self.assertRaises(ValueError):junction_turn(self.course,vertex)

    def test_only_declared_training_seeds_can_label_actions(self):
        training_seed(2026110701,self.spec)
        for seed in (2026110711,2026110741,True,'2026110701'):
            with self.subTest(seed=seed),self.assertRaisesRegex(ValueError,'seed'):training_seed(seed,self.spec)

    def test_heldout_teacher_is_rejected_before_host_build_or_trace_loading(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);(folder/'course.json').write_bytes((ROOT/'simulation/reconstructed_course.json').read_bytes())
            course_hash=sha(folder/'course.json')
            trial=dict(seed=2026110711,plant={},lift_duration_s=27)
            manifest=dict(source_hash='source',course_sha256=course_hash,trials=[trial],expected_seeds=[2026110711],model_files={})
            (folder/'manifest.json').write_text(json.dumps(manifest));digest=sha(folder/'manifest.json')
            attempt={**trial,'source_hash':'source','course_hash':course_hash,'manifest_sha256':digest}
            result=dict(manifest_sha256=digest,source_sha256='source',course_sha256=course_hash,attempts=[attempt])
            (folder/'results.json').write_text(json.dumps(result))
            with self.assertRaisesRegex(ValueError,'seed'):audit_teacher((str(folder),198,str(folder/'work')))


if __name__=='__main__':unittest.main()
