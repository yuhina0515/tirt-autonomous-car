"""Compile the actual independent cores once; directed cases are not race laps."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PrepracticePriority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = ROOT / 'build-output/prepractice-priority'
        out.mkdir(parents=True, exist_ok=True)
        cls.exe = out / ('prepractice-priority.exe' if sys.platform == 'win32' else 'prepractice-priority')
        source = ROOT / 'tests/prepractice_priority.cpp'
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
            cmd = [shutil.which('cl', path=env.get('PATH')), '/nologo', '/EHsc', '/O2', '/std:c++14', '/I' + str(ROOT / 'tests/layered_arduino'), str(source), '/Fe:' + str(cls.exe), '/Fo:' + str(out / 'prepractice-priority.obj')]
        else:
            cmd = ['g++', '-std=c++11', '-Wall', '-Wextra', '-pedantic', '-I' + str(ROOT / 'tests/layered_arduino'), str(source), '-o', str(cls.exe)]
        r = subprocess.run(cmd, env=env, cwd=out, capture_output=True, text=True)
        (out / 'compile.log').write_text(r.stdout+r.stderr, encoding='utf-8')
        if r.returncode:
            raise RuntimeError(r.stdout+r.stderr)


    def test_priority_invariants(self):
        r=subprocess.run([str(self.exe)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
