import copy
import csv
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from build import validate,build,HEADER
from analyze import load,analyze
from calibrate import endpoints
from blockly_codegen import xml_to_ino

class Tests(unittest.TestCase):
 def setUp(self):self.config=json.loads((ROOT/'config.json').read_text())
 def test_config_rejections(self):
  changes=[{'drive_enabled':True},{'min_pwm':100},{'uncertain_stop_ms':20},
           {'on_strength':300},{'period_ms':30},{'log_period_ms':10},
           {'line_adc_A5_to_A1':[499]*5},{'drive_enabled':'true'},
           {'lap_enabled':1},{'finish_confirm_ms':400},{'min_lap_ms':180000},
           {'search_pwm':101},{'search_timeout_ms':20},{'departure_confirm_ms':15000},
           {'wide_pwm':101},{'wide_pwm':True},{'wide_hint_ms':501},{'wide_hint_ms':True},
           {'swap_motor_channels':1},{'swap_motor_channels':'true'}]
  for change in changes:
   c=copy.deepcopy(self.config);c.update(change)
   with self.subTest(change=change),self.assertRaises(ValueError):validate(c)
 def test_reproducible_xml_ino(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);a=build(ROOT/'config.json',t/'one','track');b=build(ROOT/'config.json',t/'two','track')
   self.assertEqual(a['xml_sha256'],b['xml_sha256']);self.assertEqual(a['ino_sha256'],b['ino_sha256'])
   self.assertFalse(a['drive_armed'])
 def test_checked_in_exports_are_current(self):
  with tempfile.TemporaryDirectory() as t:
   for profile,folder in [('track','practice_controller'),('capture','stationary_capture')]:
    result=build(ROOT/'config.json',Path(t)/folder,profile)
    saved=json.loads((ROOT/'firmware'/folder/'manifest.json').read_text())
    self.assertEqual(result,saved)
    self.assertEqual((Path(t)/folder/(folder+'.xml')).read_bytes(),(ROOT/'firmware'/folder/(folder+'.xml')).read_bytes())
    self.assertEqual((Path(t)/folder/(folder+'.ino')).read_bytes(),(ROOT/'firmware'/folder/(folder+'.ino')).read_bytes())
 def test_unknown_block_rejected(self):
  with self.assertRaises(ValueError):xml_to_ino('<xml xmlns="https://developers.google.com/blockly/xml"><block type="opaque_cpp"/></xml>')
 def test_crossing_profile_exports(self):
  path=ROOT/'configs/field_crossing_20261025.json';c=json.loads(path.read_text());validate(c)
  self.assertFalse(c['lap_enabled']);self.assertTrue(c['drive_enabled']);self.assertEqual(c['wide_pwm'],50)
  self.assertEqual(c['wide_timeout_ms'],900);self.assertEqual(c['wide_hint_ms'],250)
  with tempfile.TemporaryDirectory() as t:
   folder=Path(t)/'field_crossing';result=build(path,folder,'track')
   self.assertEqual(result,json.loads((ROOT/'firmware/field_crossing/manifest.json').read_text()))
   for suffix in ('.xml','.ino'):
    self.assertEqual((folder/('field_crossing'+suffix)).read_bytes(),(ROOT/'firmware/field_crossing'/('field_crossing'+suffix)).read_bytes())
 def test_motor_swap_profile_exports(self):
  path=ROOT/'configs/field_motor_swap_20261025.json';c=json.loads(path.read_text());validate(c)
  self.assertTrue(c['swap_motor_channels']);self.assertFalse(c['lap_enabled'])
  self.assertEqual(c['max_pwm'],70)
  baseline=json.loads((ROOT/'configs/field_crossing_20261025.json').read_text())
  self.assertEqual(c['line_adc_A5_to_A1'],baseline['line_adc_A5_to_A1'])
  self.assertEqual(c['background_adc_A5_to_A1'],baseline['background_adc_A5_to_A1'])
  with tempfile.TemporaryDirectory() as t:
   folder=Path(t)/'field_motor_swap';result=build(path,folder,'track')
   self.assertEqual(result,json.loads((ROOT/'firmware/field_motor_swap/manifest.json').read_text()))
   for suffix in ('.xml','.ino'):
    self.assertEqual((folder/('field_motor_swap'+suffix)).read_bytes(),(ROOT/'firmware/field_motor_swap'/('field_motor_swap'+suffix)).read_bytes())
 def test_measured_field_profile_exports_and_limits(self):
  config_path=ROOT/'configs/field_low_speed_20261025.json'
  c=json.loads(config_path.read_text());validate(c)
  self.assertTrue(c['calibration_measured']);self.assertTrue(c['drive_enabled'])
  self.assertFalse(c['lap_enabled']);self.assertLessEqual(c['max_pwm'],70)
  self.assertEqual(c['max_run_ms'],60000)
  with tempfile.TemporaryDirectory() as t:
   folder=Path(t)/'field_low_speed';result=build(config_path,folder,'track')
   self.assertTrue(result['drive_armed']);self.assertFalse(result['physical_acceptance'])
   self.assertEqual(result,json.loads((ROOT/'firmware/field_low_speed/manifest.json').read_text()))
   for suffix in ('.xml','.ino'):
    self.assertEqual((folder/('field_low_speed'+suffix)).read_bytes(),(ROOT/'firmware/field_low_speed'/('field_low_speed'+suffix)).read_bytes())
 def write_csv(self,path,label,adc,start=0,states=6):
  with path.open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['host_ms','label']+HEADER)
   for i in range(40):w.writerow([i*20,label,(start+i*20)&0xffffffff,i+1,20]+[adc]*5+[4,states,0,0,0,1000,0,0,0,0])
 def test_capture_and_calibration(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);l=t/'line.csv';b=t/'background.csv'
   self.write_csv(l,'LINE',40);self.write_csv(b,'BACKGROUND',800)
   c,e=endpoints(l,b,self.config);self.assertTrue(c['calibration_measured']);self.assertFalse(c['drive_enabled'])
   self.assertEqual(c['line_adc_A5_to_A1'],[40]*5);self.assertEqual(e['line_records'],40)
   report=analyze(l);self.assertEqual(report['records'],40);self.assertEqual(report['device_observed_span_ms'],780)
 def test_reject_unlabelled_moving_and_overlap(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);l=t/'line.csv';b=t/'bg.csv';self.write_csv(b,'BACKGROUND',800)
   for label,adc,state in [('UNLABELLED',40,6),('LINE',40,2),('LINE',780,6)]:
    self.write_csv(l,label,adc,states=state)
    with self.subTest(label=label,adc=adc,state=state),self.assertRaises(ValueError):endpoints(l,b,self.config)
 def test_wrap_and_reset(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'wrap.csv';self.write_csv(p,'LINE',40,start=0xfffffff0)
   self.assertEqual(analyze(p)['clock_wraps'],1)
   s=p.read_text().splitlines();s[2]=s[1];p.write_text('\n'.join(s)+'\n')
   with self.assertRaises(ValueError):load(p)

if __name__=='__main__':unittest.main()
