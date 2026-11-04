"""Explicit floor hypothesis must never become legal-road or white-paint data."""
import copy
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from course_environment import Course,geometry,model_features
from course_world import Course as RoadCourse,Mechanisms,Pose,geometry as road_geometry,sense
from ground_support import GroundCourse
from simulation_model import Plant
from learn_course_mission import stage_profile,feature_identity,models_for_spec,sha


class GroundSupportChecks(unittest.TestCase):
    def setUp(self):
        self.base=json.loads((ROOT/'simulation/reconstructed_course.json').read_text())
        self.spec=json.loads((ROOT/'simulation/reconstructed_course_ground.json').read_text())

    def test_no_backing_dispatches_to_exact_legacy_world(self):
        course=Course(self.base)
        self.assertIs(type(course),RoadCourse)
        self.assertEqual(model_features(self.base),[])
        for station in (0,10,30,55,60):
            point,yaw=course.at(station);pose=Pose(*point,yaw);m=Mechanisms(course,27)
            self.assertEqual(geometry(course,m,pose,Plant()),road_geometry(course,m,pose,Plant()))

    def test_frozen_701_pose_has_physical_floor_but_identical_legality(self):
        old=RoadCourse(self.base);new=Course(self.spec)
        pose=Pose(1.5319973895586598,1.8094097048104565,0,-22.916228370142655)
        oldm=Mechanisms(old,27);newm=Mechanisms(new,27)
        self.assertIsNone(old.contact(pose.x,pose.y,pose.z,oldm))
        self.assertEqual(new.contact(pose.x,pose.y,pose.z,newm)['kind'],'ground_backing')
        self.assertIsNone(new.road_contact(pose.x,pose.y,pose.z,newm))
        self.assertEqual(geometry(new,newm,pose,Plant()),road_geometry(old,oldm,pose,Plant()))
        self.assertTrue(geometry(new,newm,pose,Plant())['body_line'])
        self.assertTrue(geometry(new,newm,pose,Plant())['wheel_road'])

    def test_floor_does_not_legalize_ordinary_departure_or_add_white(self):
        course=Course(self.spec);m=Mechanisms(course,27);x,y=course.xy((1000,950))
        pose=Pose(x,y,0,0)
        self.assertEqual(course.contact(x,y,0,m)['kind'],'ground_backing')
        self.assertFalse(geometry(course,m,pose,Plant())['wheel_road'])
        self.assertFalse(course.white(x,y,.006,m))
        self.assertIsNone(course.contact(x,y,.19,m))
        x,y=course.xy((1060,950));self.assertIsNone(course.contact(x,y,0,m))

    def test_road_support_and_existing_sensor_values_take_precedence(self):
        old=RoadCourse(self.base);new=Course(self.spec)
        point,yaw=old.at(old.stations[192]+.2);pose=Pose(*point,yaw)
        a,b=Mechanisms(old,27),Mechanisms(new,27)
        self.assertEqual(new.contact(*point,b)['kind'],'road')
        self.assertEqual(sense(old,a,pose,Plant(),random.Random(2)),sense(new,b,pose,Plant(),random.Random(2)))

    def test_invalid_or_unbounded_backings_are_rejected(self):
        for backing in (dict(height_m=.19,bounds_px=[0,0,1240,1201]),
                        dict(height_m=0,bounds_px=[0,0,99999,1201]),
                        dict(height_m=0,bounds_px=[76,809,76,1074]),
                        dict(height_m=False,bounds_px=[76,809,1024,1074]),
                        dict(height_m=0,bounds_px=[76,float('nan'),1024,1074])):
            spec=copy.deepcopy(self.spec);spec['ground_backings']=[backing]
            with self.subTest(backing=backing),self.assertRaises(ValueError):Course(spec)

    def test_backing_profile_must_bind_feature_and_both_extension_modules(self):
        source=ROOT/'firmware/experiments/junction_context/junction_context.ino'
        course_hash=sha(ROOT/'simulation/reconstructed_course_ground.json')
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);path=out/'profile.json'
            profile=dict(course_sha256=course_hash,feature_sha256=feature_identity(source),
                words=[['LIFT']],sensor_model_sha256={n:sha(ROOT/n) for n in models_for_spec(self.base)})
            path.write_text(json.dumps(profile))
            with self.assertRaisesRegex(ValueError,'features'):stage_profile(source,out/'bad',path,course_hash,course_spec=self.spec)
            profile['model_features']=['ground_backing'];profile['sensor_model_sha256']={n:sha(ROOT/n) for n in models_for_spec(self.spec)}
            path.write_text(json.dumps(profile));stage_profile(source,out/'good',path,course_hash,course_spec=self.spec)
            profile['sensor_model_sha256']['tools/ground_support.py']='0'*64;path.write_text(json.dumps(profile))
            with self.assertRaisesRegex(ValueError,'model changed'):stage_profile(source,out/'stale',path,course_hash,course_spec=self.spec)


if __name__=='__main__':unittest.main()
