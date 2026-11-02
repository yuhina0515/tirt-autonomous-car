"""Qualification-contract unit fixtures, never vehicle trial evidence."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from course_qualification import preflight,judge_batch,REQUIRED_CHECKS

class QualificationChecks(unittest.TestCase):
    def record(self,seed):
        return dict(seed=seed,source_hash='source',course_hash='course',trace_sha256='a'*64,
                    elapsed_s=90,independent_checks={name:True for name in REQUIRED_CHECKS})
    def test_official_spec_is_explicitly_incomplete(self):
        issues=preflight(json.loads((ROOT/'simulation/official_course.json').read_text()))
        self.assertIn('missing_verified_metric_geometry',issues)
        self.assertIn('missing_verified_F_marker_definition',issues)
    def test_five_fixture_records_only(self):
        self.assertTrue(judge_batch([self.record(i) for i in range(5)],'source','course',list(range(5)))['passed'])
        self.assertFalse(judge_batch([self.record(i) for i in range(4)],'source','course',list(range(5)))['passed'])
        self.assertFalse(judge_batch([self.record(i) for i in range(5)],'source','course')['passed'])
    def test_a_failure_breaks_streak(self):
        rows=[self.record(i) for i in range(5)];rows[2]['independent_checks']['lift_stop_and_settled_exit']=False
        r=judge_batch(rows,'source','course',list(range(5)));self.assertFalse(r['passed']);self.assertEqual(r['longest_streak'],2)
    def test_source_change_and_duplicate_seed_rejected(self):
        rows=[self.record(i) for i in range(5)];rows[1]['source_hash']='changed'
        self.assertFalse(judge_batch(rows,'source','course',list(range(5)))['passed'])
        self.assertFalse(judge_batch([self.record(1) for _ in range(5)],'source','course',list(range(5)))['passed'])
    def test_controller_done_flag_is_not_evidence(self):
        rows=[self.record(i) for i in range(5)];rows[0]['independent_checks']={};rows[0]['lapDone']=True
        self.assertFalse(judge_batch(rows,'source','course',list(range(5)))['passed'])
    def test_nan_duration_and_missing_trace_rejected(self):
        rows=[self.record(i) for i in range(5)];rows[0]['elapsed_s']=float('nan');rows[1].pop('trace_sha256')
        self.assertFalse(judge_batch(rows,'source','course',list(range(5)))['passed'])
