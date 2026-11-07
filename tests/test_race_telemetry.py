"""Telemetry framing and decoder checks. Host evidence only, not a hardware rate."""
import contextlib
import csv
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import decode_race_telemetry as t  # noqa: E402

HEADER = ROOT / 'firmware/race_two_marker/telemetry.h'
SAMPLE = t.Frame(seq=0x0102, dropped=0x0304, scan_start_us=0x05060708, loop_gap_us=0x090A0B0C,
                 max_loop_gap_us=0x0D0E0F10, scan_us=0x1112, max_scan_us=0x1314, scan_count=0x1516,
                 raw=(1, 2, 3, 4, 1023), left_pwm=-100, right_pwm=230, mask=0x1F, phase=2, fault=0,
                 events=1, flags=1, motion=0x21)
# Layout written out by hand so a format-string change cannot pass unnoticed.
SAMPLE_BODY = bytes.fromhex(
    'a55a0130' '0201' '0403' '08070605' '0c0b0a09' '100f0e0d' '1211' '1413' '1615'
    '0100' '0200' '0300' '0400' 'ff03' '9cff' 'e600' '1f' '02' '00' '01' '01' '21')


def frame(**fields):
    return t.encode_frame(t.Frame(**fields))


class Crc(unittest.TestCase):
    def test_published_check_vector(self):
        self.assertEqual(t.crc16(b'123456789'), 0x29B1)

    def test_other_known_vectors(self):
        self.assertEqual(t.crc16(b''), 0xFFFF)
        self.assertEqual(t.crc16(b'A'), 0xB915)


class Layout(unittest.TestCase):
    def test_exact_little_endian_layout(self):
        data = t.encode_frame(SAMPLE)
        self.assertEqual(len(data), 48)
        self.assertEqual(len(SAMPLE_BODY), 46)
        self.assertEqual(data[:46], SAMPLE_BODY)
        self.assertEqual(data[46] | data[47] << 8, t.crc16(SAMPLE_BODY))

    def test_round_trip_and_motion_nibbles(self):
        decoded = t.decode_frame(t.encode_frame(SAMPLE))
        self.assertEqual(decoded, SAMPLE)
        self.assertEqual((decoded.motion_mode, decoded.motion_fault), (1, 2))


class Parser(unittest.TestCase):
    def test_noise_then_frame(self):
        p = t.FrameParser()
        self.assertEqual(p.feed(b'\x00\x11\xa5\x22' + frame(seq=7)), [t.Frame(seq=7)])
        self.assertEqual(p.skipped_bytes, 4)

    def test_corrupt_frame_does_not_lose_neighbours(self):
        bad = bytearray(frame(seq=2))
        bad[30] ^= 0x40
        p = t.FrameParser()
        got = p.feed(frame(seq=1) + bytes(bad) + frame(seq=3))
        self.assertEqual([f.seq for f in got], [1, 3])
        self.assertEqual(p.crc_errors, 1)
        self.assertEqual(p.skipped_bytes, 48)
        self.assertEqual(p.pending_bytes, 0)

    def test_corrupt_length_is_a_header_reject(self):
        bad = bytearray(frame(seq=2))
        bad[3] = 47
        p = t.FrameParser()
        self.assertEqual([f.seq for f in p.feed(bytes(bad) + frame(seq=3))], [3])
        self.assertEqual((p.header_rejects, p.crc_errors), (1, 0))

    def test_sync_bytes_inside_payload_are_data(self):
        data = t.Frame(seq=0x5AA5, dropped=0x5AA5, raw=(0x5AA5, 0, 0x5AA5, 0, 0))
        p = t.FrameParser()
        self.assertEqual(p.feed(t.encode_frame(data)), [data])

    def test_false_sync_before_real_frame(self):
        p = t.FrameParser()
        self.assertEqual([f.seq for f in p.feed(b'\xa5\x5a\x01\x30' + frame(seq=9))], [9])
        self.assertEqual(p.pending_bytes, 0)

    def test_one_byte_feeds_and_truncated_tail(self):
        p = t.FrameParser()
        got = []
        for byte in frame(seq=4) + frame(seq=5)[:20]:
            got += p.feed(bytes([byte]))
        self.assertEqual([f.seq for f in got], [4])
        self.assertEqual(p.pending_bytes, 20)
        self.assertEqual(p.skipped_bytes, 0)


class Rollover(unittest.TestCase):
    def test_sequence_dropped_and_time_rollover(self):
        a = t.Analyzer()
        start = 2 ** 32 - 10000
        rows = [a.add(t.Frame(seq=s, dropped=d, scan_start_us=u)) for s, d, u in [
            (0xFFFE, 0xFFFF, start), (0xFFFF, 0xFFFF, 10000), (0, 1, 30000), (2, 1, 50000)]]
        self.assertEqual([r.seq_unwrapped for r in rows], [65534, 65535, 65536, 65538])
        self.assertEqual([r.dropped_unwrapped for r in rows], [65535, 65535, 65537, 65537])
        self.assertEqual([r.time_us_unwrapped - start for r in rows], [0, 20000, 40000, 60000])
        self.assertEqual({r.segment for r in rows}, {1})
        s = a.summary()
        self.assertEqual((s['missing_sequence_frames'], s['device_dropped_frames']), (1, 2))
        self.assertEqual(s['duration_s'], 0.06)

    def test_restart_opens_a_segment_without_counting_a_gap(self):
        a = t.Analyzer()
        a.add(t.Frame(seq=100, dropped=5, scan_start_us=5000000))
        r = a.add(t.Frame(seq=0, dropped=0, scan_start_us=1000))
        self.assertEqual((r.segment, r.seq_unwrapped, r.dropped_unwrapped, r.time_us_unwrapped), (2, 0, 0, 1000))
        self.assertEqual((a.summary()['missing_sequence_frames'], a.summary()['device_dropped_frames']), (0, 0))

    def test_backward_time_with_advancing_sequence_is_a_restart(self):
        a = t.Analyzer()
        a.add(t.Frame(seq=0, scan_start_us=900000))
        self.assertEqual(a.add(t.Frame(seq=1, scan_start_us=1000)).segment, 2)


class Cli(unittest.TestCase):
    def capture(self):
        return b''.join(frame(seq=i, scan_start_us=20000 * i, scan_us=100 + i, max_scan_us=200 + i, loop_gap_us=150,
                              max_loop_gap_us=400 + i, scan_count=100, raw=(35, 500, 35, 500, 1023), mask=0b10100,
                              left_pwm=-1, phase=3, flags=1) for i in range(3))

    def run_decode(self, data):
        with tempfile.TemporaryDirectory() as d:
            source, target, report = Path(d, 'c.bin'), Path(d, 'c.csv'), Path(d, 'c.json')
            source.write_bytes(data)
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = t.main(['decode', str(source), '--csv', str(target), '--summary', str(report)])
            with target.open(newline='', encoding='utf-8') as stream:
                rows = list(csv.DictReader(stream))
            return code, rows, json.loads(report.read_text(encoding='utf-8')), json.loads(out.getvalue())

    def test_binary_to_csv_and_timing(self):
        code, rows, summary, printed = self.run_decode(self.capture())
        self.assertEqual(code, 0)
        self.assertEqual(summary, printed)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['raw_a5'], '35')
        self.assertEqual(rows[0]['raw_a1'], '1023')
        self.assertEqual(rows[0]['mask_bits'], '10100')
        self.assertEqual(rows[0]['phase_name'], 'AfterLift')
        self.assertEqual(rows[0]['left_pwm'], '-1')
        self.assertAlmostEqual(summary['frame_rate_hz'], 50.0)
        self.assertAlmostEqual(summary['mean_scan_hz'], 5000.0)  # First window reaches back to boot.
        self.assertEqual(summary['peak_scan_us'], 202)
        self.assertEqual(summary['peak_loop_gap_us'], 402)
        self.assertEqual(summary['sampled_scan_us']['count'], 3)

    def test_no_frames_is_an_error_not_an_empty_success(self):
        code, rows, summary, _ = self.run_decode(b'\x00' * 100)
        self.assertEqual((code, rows, summary['skipped_bytes']), (1, [], 100))

    def test_decode_needs_no_pyserial_and_record_explains_it(self):
        with mock.patch.dict(sys.modules, {'serial': None}):
            self.assertEqual(self.run_decode(self.capture())[0], 0)
            with tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(SystemExit, 'pyserial'):
                t.record('COM0', Path(d, 'c.bin'), 0.0)


class HeaderContract(unittest.TestCase):
    def test_write_only_no_heap(self):
        code = re.sub(r'//.*', '', HEADER.read_text(encoding='utf-8'))
        for banned in (r'Serial\.print', r'Serial\.flush', r'Serial\.read', r'Serial\.available\b', r'Serial\.peek',
                       r'\bmalloc\b', r'\bnew\b', r'\bString\b', r'analogWrite', r'digitalWrite', r'delay'):
            self.assertIsNone(re.search(banned, code), banned)
        self.assertLess(code.index('availableForWrite'), code.index('Serial.write'))


MOCK_ARDUINO = r'''#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
// Exposes only what telemetry.h may use: read, print, flush and motor calls cannot compile.
struct MockSerial {
    unsigned long baud = 0;
    int room = 63;
    void begin(unsigned long value) { baud = value; }
    int availableForWrite() { return room; }
    size_t write(const uint8_t* data, size_t length) {
        for (size_t i = 0; i < length; i++) printf("%02x", data[i]);
        printf("\n");
        return length;
    }
};
static MockSerial Serial;
'''

DRIVER = r'''#include <Arduino.h>
#include "telemetry.h"
int main() {
    using race_telemetry::emit;
    uint16_t white[5] = {35, 35, 35, 35, 35}, raw[5] = {1, 2, 3, 4, 1023};
    race::Controller c;
    c.tick(0, white);
    race_telemetry::begin();
    printf("baud %lu\n", Serial.baud);
    race::Wheels w(-100, 230), none;
    emit(1000, 100, 50, white, c, w, true, false);
    emit(1100, 300, 70, raw, c, w, true, false);
    emit(21000, 200, 60, raw, c, w, true, false);
    Serial.room = 47;
    emit(41000, 900, 80, raw, c, w, true, false);
    Serial.room = 48;
    emit(61000, 100, 40, raw, c, w, true, false);
    Serial.room = 63;
    emit(200000, 10, 20, raw, c, w, true, false);
    emit(219000, 10, 20, raw, c, w, true, false);
    emit(220000, 10, 20, raw, c, none, false, false);
    race::Controller s;
    s.tick(1, raw, true);
    emit(240000, 10, 20, raw, s, none, true, true);
    race_telemetry::begin();
    emit(0xFFFFF000UL, 10, 20, raw, c, w, true, false);
    emit(0xFFFFF100UL, 10, 20, raw, c, w, true, false);
    emit(0x00004000UL, 10, 20, raw, c, w, true, false);
    return 0;
}
'''


def compiler(out, source, exe):
    """Return (command, environment), or None if this host has no C++ compiler."""
    env = os.environ.copy()
    env['PATH'] = os.environ.get('PATH', '').replace('"', '')
    includes = [str(out), str(HEADER.parent)]
    if sys.platform == 'win32':
        if not shutil.which('cl'):
            paths = sorted(Path('C:/Program Files/Microsoft Visual Studio').glob('*/*/VC/Auxiliary/Build/vcvars64.bat'))
            if paths:
                r = subprocess.run('cmd /d /s /c ""%s" >nul && set"' % paths[-1], env=env, capture_output=True, text=True, check=True)
                for line in r.stdout.splitlines():
                    if '=' in line and not line.startswith('='):
                        k, v = line.split('=', 1)
                        env[k.upper()] = v
        cl = shutil.which('cl', path=env.get('PATH'))
        if cl:
            return [cl, '/nologo', '/EHsc', '/std:c++14'] + ['/I' + i for i in includes] + [
                str(source), '/Fe:' + str(exe), '/Fo:' + str(out / 'driver.obj')], env
    gcc = shutil.which('g++', path=env.get('PATH'))
    if gcc:
        return [gcc, '-std=c++11', '-Wall', '-Wextra', '-pedantic'] + ['-I' + i for i in includes] + [str(source), '-o', str(exe)], env
    return None


class FirmwareCrossCheck(unittest.TestCase):
    """Compile the actual header against a minimal mock and decode its bytes in Python."""

    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            (out / 'Arduino.h').write_text(MOCK_ARDUINO, encoding='utf-8')
            source, exe = out / 'driver.cpp', out / ('driver.exe' if sys.platform == 'win32' else 'driver')
            source.write_text(DRIVER, encoding='utf-8')
            found = compiler(out, source, exe)
            if found is None:
                raise unittest.SkipTest('no C++ compiler on this host')
            r = subprocess.run(found[0], env=found[1], cwd=out, capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(r.stdout + r.stderr)
            lines = subprocess.run([str(exe)], capture_output=True, text=True, check=True).stdout.splitlines()
        cls.baud = lines[0]
        parser = t.FrameParser()
        cls.frames = parser.feed(bytes.fromhex(''.join(lines[1:])))
        cls.parser = parser
        cls.raw_lines = lines[1:]

    def test_baud(self):
        self.assertEqual(self.baud, 'baud 115200')

    def test_every_written_frame_is_valid_and_fixed_size(self):
        self.assertTrue(all(len(line) == 96 for line in self.raw_lines))
        self.assertEqual((self.parser.crc_errors, self.parser.header_rejects, self.parser.skipped_bytes), (0, 0, 0))

    def test_decimation_backpressure_and_counters(self):
        f = self.frames
        self.assertEqual([x.seq for x in f], [0, 1, 2, 3, 4, 5, 0, 1])
        self.assertEqual([x.dropped for x in f], [0, 0, 1, 1, 1, 1, 0, 0])
        self.assertEqual([x.scan_start_us for x in f],
                         [1000, 21000, 61000, 200000, 220000, 240000, 0xFFFFF000, 0x4000])
        self.assertEqual([x.scan_count for x in f], [1, 2, 2, 1, 2, 1, 1, 2])

    def test_window_peaks_span_the_dropped_slot(self):
        f = self.frames
        self.assertEqual((f[1].loop_gap_us, f[1].max_loop_gap_us, f[1].scan_us, f[1].max_scan_us), (200, 300, 60, 70))
        self.assertEqual((f[2].loop_gap_us, f[2].max_loop_gap_us, f[2].scan_us, f[2].max_scan_us), (100, 900, 40, 80))

    def test_fields_and_flags(self):
        first, idle, stopped = self.frames[0], self.frames[4], self.frames[5]
        self.assertEqual(first.raw, (35, 35, 35, 35, 35))
        self.assertEqual(self.frames[1].raw, (1, 2, 3, 4, 1023))
        self.assertEqual((first.left_pwm, first.right_pwm, first.mask, first.phase, first.events, first.flags),
                         (-100, 230, 31, 0, 0, t.FLAG_RUNNING))
        self.assertEqual(idle.flags, t.FLAG_MASK_STALE)
        self.assertEqual((stopped.phase, stopped.fault, stopped.left_pwm, stopped.right_pwm),
                         (t.PHASES.index('Fault'), t.FAULTS.index('Manual'), 0, 0))
        self.assertEqual(stopped.flags, t.FLAG_RUNNING | t.FLAG_STOPPED | t.FLAG_MASK_STALE)


if __name__ == '__main__':
    unittest.main()
