"""Line-ending transport must not become world/profile metadata relabeling."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from transfer_course_newlines import transfer,policy_identity


class CourseTextChecks(unittest.TestCase):
    def test_uniform_newlines_preserve_every_policy_and_teacher_field(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);old=d/'old.json';new=d/'new.json'
            old.write_bytes(b'{\r\n  "height": 0\r\n}\r\n');new.write_bytes(old.read_bytes().replace(b'\r\n',b'\n'))
            profile=dict(course_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),junctions=[dict(word=['W'],turn='R')],
                         training=[dict(course_sha256='frozen-raw',trace_sha256='trace')])
            result=transfer(profile,old,new)
            self.assertEqual(policy_identity(result),policy_identity(profile))
            self.assertEqual(result['training'],profile['training']);self.assertNotIn('course_text_transfers',profile)
            self.assertEqual(result['course_text_transfers'][0]['new_raw_sha256'],result['course_sha256'])

    def test_other_text_changes_values_or_unbound_input_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);old=d/'old.json';new=d/'new.json';old.write_bytes(b'{\r\n "height": 0\r\n}\r\n')
            profile=dict(course_sha256=hashlib.sha256(old.read_bytes()).hexdigest())
            for data in (b'{\n "height": 1\n}\n',b'{\n  "height": 0\n}\n',b'{\r\n "height": 0\n}\n'):
                new.write_bytes(data)
                with self.subTest(data=data),self.assertRaises(ValueError):transfer(profile,old,new)
            new.write_bytes(old.read_bytes().replace(b'\r\n',b'\n'))
            with self.assertRaisesRegex(ValueError,'bind'):transfer({'course_sha256':'other'},old,new)


if __name__=='__main__':unittest.main()
