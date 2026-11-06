import json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from run_corner_batch import window

class CornerWindowTests(unittest.TestCase):
    def test_crop_preserves_adjacent_turns(self):
        p=[[-2,0],[-.2,0],[0,0],[0,.2],[.2,.2],[2,.2]]
        cut=window(p,2)
        self.assertEqual(cut[1:5],p[1:5])
        self.assertAlmostEqual(sum(math.dist(a,b) for a,b in zip(cut,cut[1:])),1.2)

    def test_route_end_is_not_extended(self):
        p=[[0,0],[.1,0],[.1,.1]]
        self.assertEqual(window(p,1),p)

    def test_all_nonzero_turns_have_nondegenerate_windows(self):
        spec=json.loads((ROOT/'simulation/reconstructed_course_ground.json').read_text())
        p=[[x*.005,-y*.005] for x,y in spec['points_px']];count=0
        for i in range(1,len(p)-1):
            a,b,c=p[i-1:i+2];h=math.atan2(c[1]-b[1],c[0]-b[0])-math.atan2(b[1]-a[1],b[0]-a[0])
            if abs(math.degrees(math.atan2(math.sin(h),math.cos(h))))<=.01:continue
            count+=1;cut=window(p,i)
            self.assertIn(p[i],cut)
            self.assertTrue(all(math.dist(a,b)>0 for a,b in zip(cut,cut[1:])))
        self.assertEqual(count,204)

if __name__=='__main__':unittest.main()
