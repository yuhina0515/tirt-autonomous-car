"""Reject stale mission identities and fabricated observation serials."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from learn_course_mission import feature_identity,stage_profile,observable_events,lift_observation,MODELS,sha,canonical_sha
from course_world import Course


class ProfileChecks(unittest.TestCase):
    def test_canonical_model_identity_is_portable_without_changing_raw_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.py';b=Path(d)/'b.py'
            a.write_bytes(b'x=1\n');b.write_bytes(b'x=1\r\n')
            self.assertEqual(canonical_sha(a),canonical_sha(b))
            self.assertNotEqual(sha(a),sha(b))

    def test_station_annotation_cannot_relabel_a_crossing_as_lift(self):
        c=Course(json.loads((ROOT/'simulation/reconstructed_course.json').read_text()))
        events=[dict(ms=0) for _ in c.gates]
        point,_=c.at(11.1485865)
        row=dict(x=point[0],y=point[1],z=point[2],ms=30240,station=c.lift_s)
        self.assertFalse(lift_observation(row,c,events))
        point,_=c.at(c.lift_s)
        row.update(x=point[0],y=point[1],z=point[2],station=0)
        self.assertTrue(lift_observation(row,c,events))
        self.assertFalse(lift_observation(row,c,[]))
    def test_motion_or_sensor_change_requires_retraining(self):
        source=ROOT/'firmware/candidate_car/candidate_car.ino'
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);candidate=folder/source.name;candidate.write_bytes(source.read_bytes())
            header=source.with_name('controller.h').read_text()
            candidate.with_name('controller.h').write_text(header)
            course=sha(ROOT/'simulation/reconstructed_course.json')
            profile=dict(course_sha256=course,feature_sha256=feature_identity(source),
                sensor_model_sha256={n:sha(ROOT/n) for n in MODELS},words=[['L','W','LIFT']])
            path=folder/'mission.json';path.write_text(json.dumps(profile))
            staged=stage_profile(candidate,folder/'staged',path,course)
            self.assertEqual(feature_identity(staged),feature_identity(candidate))
            candidate.with_name('controller.h').write_text(header.replace('base = 180','base = 181'))
            with self.assertRaisesRegex(ValueError,'semantics changed'):stage_profile(candidate,folder/'bad',path,course)
            candidate.with_name('controller.h').write_text(header)
            profile['sensor_model_sha256'][MODELS[0]]='0'*64;path.write_text(json.dumps(profile))
            with self.assertRaisesRegex(ValueError,'model changed'):stage_profile(candidate,folder/'bad',path,course)

    def test_event_serial_is_actual_discrete_tick_observation(self):
        rows=[dict(eventSerial=0,eventCode=0,ticked=0),dict(eventSerial=1,eventCode=2,ticked=1),
              dict(eventSerial=1,eventCode=2,ticked=0),dict(eventSerial=2,eventCode=1,ticked=1)]
        self.assertEqual([code for code,_ in observable_events(rows)],[2,1])
        with self.assertRaisesRegex(ValueError,'serial'):observable_events([dict(eventSerial=2,eventCode=1,ticked=1)])
        with self.assertRaisesRegex(ValueError,'serial'):observable_events([dict(eventSerial=1,eventCode=1,ticked=0)])
