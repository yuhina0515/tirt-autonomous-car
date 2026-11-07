import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analyze_course_scenarios import catalogue,intersection

class CatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=json.loads((ROOT/'simulation/reconstructed_course_ground.json').read_text())
        cls.report=catalogue(cls.spec)

    def test_full_directed_coverage(self):
        r=self.report
        self.assertEqual((r['vertices'],r['segments'],r['gates']),(211,210,209))
        self.assertEqual([x['vertices'] for x in r['segments_analysis']],[[i,i+1] for i in range(210)])
        self.assertEqual([i for p in r['phases'] for i in range(p['start'],p['end'])],list(range(210)))

    def test_mechanisms_and_finish_not_double_counted(self):
        expected={'seesaw':[115],'lift':[154],'finish':[209],'contextual_right':[198]}
        for tag,indices in expected.items():
            self.assertEqual([r['segment'] for r in self.report['segments_analysis'] if tag in r['tags']],indices)

    def test_intersection_bounds(self):
        self.assertEqual(intersection((0,0),(2,0),(1,-1),(1,1)),(.5,.5))
        self.assertIsNone(intersection((0,0),(2,0),(3,-1),(3,1)))

    def test_other_route_cannot_silently_reuse_phase_labels(self):
        spec=dict(self.spec,points_px=self.spec['points_px'][:-1])
        with self.assertRaises(ValueError):catalogue(spec)
        spec=dict(self.spec,points_px=list(reversed(self.spec['points_px'])))
        with self.assertRaises(ValueError):catalogue(spec)

if __name__=='__main__':unittest.main()
