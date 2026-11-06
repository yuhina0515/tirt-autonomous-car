"""Compile the actual independent cores once; directed cases are not race laps."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
UNUSED_CASES = 'normal_exit normal_exit_guards normal_exit_continuity patterns transitions complete noise stuck deadline rollover stop runlimit timing adapter exit_patterns blips exit_steering exit_curved_rearm exit_loss exit_rearm_noise exit_outer_and_split exit_seeded'.split()


class RaceTelemetryAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = ROOT / 'build-output/race-telemetry-adapter'
        out.mkdir(parents=True, exist_ok=True)
        cls.exe = out / ('race-telemetry.exe' if sys.platform == 'win32' else 'race-telemetry')
        source = ROOT / 'tests/race_telemetry_adapter.cpp'
        env = os.environ.copy()
        # Quoted PATH entries break vcvars batch parsing on some Windows hosts.
        env['PATH'] = os.environ.get('PATH', '').replace('"', '')
        if sys.platform == 'win32':
            if not shutil.which('cl'):
                paths = sorted(Path('C:/Program Files/Microsoft Visual Studio').glob('*/Community/VC/Auxiliary/Build/vcvars64.bat'))
                if not paths:
                    raise RuntimeError('MSVC environment missing')
                r = subprocess.run('cmd /d /s /c ""%s" >nul && set"' % paths[-1], env=env, capture_output=True, text=True, check=True)
                for line in r.stdout.splitlines():
                    if '=' in line and not line.startswith('='):
                        k, v = line.split('=', 1)
                        env[k.upper()] = v
            cmd = [shutil.which('cl', path=env.get('PATH')), '/nologo', '/EHsc', '/O2', '/std:c++14', '/I' + str(ROOT / 'tests/telemetry_arduino'), str(source), '/Fe:' + str(cls.exe), '/Fo:' + str(out / 'race-telemetry.obj')]
        else:
            cmd = ['g++', '-std=c++11', '-Wall', '-Wextra', '-pedantic', '-I' + str(ROOT / 'tests/telemetry_arduino'), str(source), '-o', str(cls.exe)]
        r = subprocess.run(cmd, env=env, cwd=out, capture_output=True, text=True)
        (out / 'compile.log').write_text(r.stdout+r.stderr, encoding='utf-8')
        if r.returncode:
            raise RuntimeError(r.stdout+r.stderr)


    def test_running_and_backpressure(self):
        capture=ROOT/'build-output/race-telemetry-adapter/capture.bin'
        result=subprocess.run([str(self.exe),str(capture)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertGreater(capture.stat().st_size,0)

    def test_summary_integrity(self):
        from tools.decode_race_telemetry import Analyzer, Frame, decode_file
        a=Analyzer();a.add(Frame(max_scan_us=900,max_loop_gap_us=1800))
        self.assertEqual(a.summary()['peak_scan_us'],900)
        self.assertEqual(a.summary()['peak_loop_gap_us'],1800)
        a.add(Frame(seq=2,scan_start_us=40000,scan_count=20))
        self.assertIsNone(a.summary()['mean_scan_hz'])
        with self.assertRaises(ValueError):
            decode_file(ROOT/'build-output/same.bin',ROOT/'build-output/same.bin')
