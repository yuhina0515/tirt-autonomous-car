#!/usr/bin/env python3
"""Decode race_two_marker binary telemetry to CSV, or record it from a serial port.

Protocol: docs/race-two-marker-2026-11-06/TELEMETRY.md. Timing statistics describe
one capture on the device clock; they are not a hardware rate guarantee.
pyserial is imported only by the record command, which never writes to the port.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import struct
import sys
import time
from typing import Dict, Iterable, List, Optional, Tuple

SYNC = b'\xa5\x5a'
VERSION = 1
FRAME_SIZE = 48
CRC_OFFSET = FRAME_SIZE - 2
BAUD = 115200
_FRAME = struct.Struct('<4B2H3I3H5H2h6BH')
assert _FRAME.size == FRAME_SIZE

FLAG_RUNNING, FLAG_STOPPED, FLAG_MASK_STALE = 1, 2, 4
PHASES = ('BeforeLift', 'WaitLift', 'ExitLift', 'AfterLift', 'Finished', 'Fault')
FAULTS = ('None', 'Manual', 'Timing', 'RunLimit', 'ExitTimeout', 'Motion', 'Uncertain')
MOTION_MODES = ('Follow', 'Search', 'Gap')
MOTION_FAULTS = ('None', 'SearchDeadline', 'CapturePattern', 'GapDeadline', 'SplitPattern',
                 'LiftExitDeadline', 'RunDeadline', 'UnexpectedPattern')
CSV_COLUMNS = (
    'segment', 'seq', 'seq_unwrapped', 'dropped', 'dropped_unwrapped', 'scan_start_us', 'time_us_unwrapped',
    'loop_gap_us', 'max_loop_gap_us', 'scan_us', 'max_scan_us', 'scan_count',
    'raw_a5', 'raw_a4', 'raw_a3', 'raw_a2', 'raw_a1', 'mask', 'mask_bits', 'left_pwm', 'right_pwm',
    'phase', 'phase_name', 'fault', 'fault_name', 'events', 'flags', 'running', 'stopped', 'mask_stale',
    'motion_mode', 'motion_mode_name', 'motion_fault', 'motion_fault_name',
)


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE, written bitwise so it cross-checks the firmware's byte form."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


@dataclass(frozen=True)
class Frame:
    seq: int = 0
    dropped: int = 0
    scan_start_us: int = 0
    loop_gap_us: int = 0
    max_loop_gap_us: int = 0
    scan_us: int = 0
    max_scan_us: int = 0
    scan_count: int = 0
    raw: Tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)  # A5, A4, A3, A2, A1.
    left_pwm: int = 0
    right_pwm: int = 0
    mask: int = 0
    phase: int = 0
    fault: int = 0
    events: int = 0
    flags: int = 0
    motion: int = 0

    @property
    def running(self) -> bool:
        return bool(self.flags & FLAG_RUNNING)

    @property
    def stopped(self) -> bool:
        return bool(self.flags & FLAG_STOPPED)

    @property
    def mask_stale(self) -> bool:
        return bool(self.flags & FLAG_MASK_STALE)

    @property
    def motion_mode(self) -> int:
        return self.motion & 0x0F

    @property
    def motion_fault(self) -> int:
        return self.motion >> 4


def encode_frame(frame: Frame) -> bytes:
    """Build a valid frame. The firmware is the producer; this serves tests and fixtures."""
    body = _FRAME.pack(SYNC[0], SYNC[1], VERSION, FRAME_SIZE, frame.seq, frame.dropped, frame.scan_start_us,
                       frame.loop_gap_us, frame.max_loop_gap_us, frame.scan_us, frame.max_scan_us, frame.scan_count,
                       *frame.raw, frame.left_pwm, frame.right_pwm, frame.mask, frame.phase, frame.fault,
                       frame.events, frame.flags, frame.motion, 0)[:CRC_OFFSET]
    return body + crc16(body).to_bytes(2, 'little')


def decode_frame(data: bytes) -> Frame:
    """Decode exactly one frame whose header and CRC the caller has already validated."""
    v = _FRAME.unpack(data)
    return Frame(seq=v[4], dropped=v[5], scan_start_us=v[6], loop_gap_us=v[7], max_loop_gap_us=v[8], scan_us=v[9],
                 max_scan_us=v[10], scan_count=v[11], raw=tuple(v[12:17]), left_pwm=v[17], right_pwm=v[18], mask=v[19],
                 phase=v[20], fault=v[21], events=v[22], flags=v[23], motion=v[24])


class FrameParser:
    """Incremental parser. Any rejected candidate resumes one byte later, so a valid
    frame straight after a corrupt one is not lost."""

    def __init__(self) -> None:
        self._buffer = bytearray()
        self.crc_errors = 0
        self.header_rejects = 0
        self.skipped_bytes = 0

    @property
    def pending_bytes(self) -> int:
        """Bytes still waiting for a complete frame; at end of input, a truncated tail."""
        return len(self._buffer)

    def feed(self, data: bytes) -> List[Frame]:
        buf = self._buffer
        buf.extend(data)
        frames: List[Frame] = []
        pos = 0
        while True:
            start = buf.find(SYNC, pos)
            if start < 0:
                # A final first-sync byte may pair with the next chunk.
                keep = len(buf) - 1 if pos < len(buf) and buf[-1] == SYNC[0] else len(buf)
                self.skipped_bytes += keep - pos
                pos = keep
                break
            self.skipped_bytes += start - pos
            pos = start
            if len(buf) - pos < FRAME_SIZE:
                break
            candidate = bytes(buf[pos:pos + FRAME_SIZE])
            if candidate[2] != VERSION or candidate[3] != FRAME_SIZE:
                self.header_rejects += 1
            elif crc16(candidate[:CRC_OFFSET]) != int.from_bytes(candidate[CRC_OFFSET:], 'little'):
                self.crc_errors += 1
            else:
                frames.append(decode_frame(candidate))
                pos += FRAME_SIZE
                continue
            self.skipped_bytes += 1
            pos += 1
        del buf[:pos]
        return frames


@dataclass(frozen=True)
class Track:
    segment: int
    seq_unwrapped: int
    dropped_unwrapped: int
    time_us_unwrapped: int


def _describe(values: List[int]) -> Optional[Dict[str, float]]:
    if not values:
        return None
    ordered = sorted(values)

    def rank(p: int) -> int:  # Nearest-rank percentile.
        return ordered[max(0, (p * len(ordered) + 99) // 100 - 1)]

    return dict(count=len(ordered), min=ordered[0], mean=sum(ordered) / len(ordered),
                p50=rank(50), p95=rank(95), max=ordered[-1])


class Analyzer:
    """Unwraps counters and gathers timing. A non-advancing sequence or backward device
    time starts a new segment (usually a board reset); segments are not bridged."""

    def __init__(self) -> None:
        self.frames = 0
        self.segment = 0
        self.missing_sequence_frames = 0
        self.device_dropped_frames = 0
        self.duration_us = 0
        self.window_scans = 0
        self.saturated_windows = 0
        self.frame_intervals: List[int] = []
        self.scan_us: List[int] = []
        self.loop_gap_us: List[int] = []
        self.peak_scan_us = 0
        self.peak_loop_gap_us = 0
        self._last: Optional[Frame] = None
        self._seq = self._dropped = self._time = 0

    def add(self, frame: Frame) -> Track:
        self.frames += 1
        self.peak_scan_us = max(self.peak_scan_us, frame.max_scan_us)
        self.peak_loop_gap_us = max(self.peak_loop_gap_us, frame.max_loop_gap_us)
        last = self._last
        self._last = frame
        seq_delta = (frame.seq - last.seq) & 0xFFFF if last else 0
        time_delta = (frame.scan_start_us - last.scan_start_us) & 0xFFFFFFFF if last else 0
        if last is None or seq_delta == 0 or seq_delta >= 0x8000 or time_delta >= 0x80000000:
            self.segment += 1
            self._seq, self._dropped, self._time = frame.seq, frame.dropped, frame.scan_start_us
            # The first window reaches back to boot, so only its sampled scan time counts.
            self.scan_us.append(frame.scan_us)
            return Track(self.segment, self._seq, self._dropped, self._time)
        dropped_delta = (frame.dropped - last.dropped) & 0xFFFF
        self._seq += seq_delta
        self._dropped += dropped_delta
        self._time += time_delta
        self.missing_sequence_frames += seq_delta - 1
        self.device_dropped_frames += dropped_delta
        self.duration_us += time_delta
        self.window_scans += frame.scan_count
        self.saturated_windows += frame.scan_count == 0xFFFF
        self.frame_intervals.append(time_delta)
        self.scan_us.append(frame.scan_us)
        self.loop_gap_us.append(frame.loop_gap_us)
        self.peak_scan_us = max(self.peak_scan_us, frame.max_scan_us)
        self.peak_loop_gap_us = max(self.peak_loop_gap_us, frame.max_loop_gap_us)
        return Track(self.segment, self._seq, self._dropped, self._time)

    def summary(self) -> Dict[str, object]:
        seconds = self.duration_us / 1e6
        return dict(
            frames=self.frames,
            segments=self.segment,
            missing_sequence_frames=self.missing_sequence_frames,
            device_dropped_frames=self.device_dropped_frames,
            duration_s=seconds,
            frame_rate_hz=len(self.frame_intervals) / seconds if seconds else None,
            mean_scan_hz=self.window_scans / seconds if seconds and not self.missing_sequence_frames and not self.saturated_windows else None,
            saturated_scan_windows=self.saturated_windows,
            frame_interval_us=_describe(self.frame_intervals),
            sampled_scan_us=_describe(self.scan_us),
            sampled_loop_gap_us=_describe(self.loop_gap_us),
            peak_scan_us=self.peak_scan_us,
            peak_loop_gap_us=self.peak_loop_gap_us,
            scope='this capture only; not a hardware rate guarantee',
        )


def _name(names: Tuple[str, ...], value: int) -> str:
    return names[value] if value < len(names) else 'unknown(%d)' % value


def csv_row(frame: Frame, track: Track) -> Tuple[object, ...]:
    return (track.segment, frame.seq, track.seq_unwrapped, frame.dropped, track.dropped_unwrapped, frame.scan_start_us,
            track.time_us_unwrapped, frame.loop_gap_us, frame.max_loop_gap_us, frame.scan_us, frame.max_scan_us,
            frame.scan_count, *frame.raw, frame.mask, format(frame.mask, '05b'), frame.left_pwm, frame.right_pwm,
            frame.phase, _name(PHASES, frame.phase), frame.fault, _name(FAULTS, frame.fault), frame.events, frame.flags,
            int(frame.running), int(frame.stopped), int(frame.mask_stale),
            frame.motion_mode, _name(MOTION_MODES, frame.motion_mode),
            frame.motion_fault, _name(MOTION_FAULTS, frame.motion_fault))


def decode_stream(chunks: Iterable[bytes], writer) -> Dict[str, object]:
    """Decode chunks into a csv.writer and return the capture summary."""
    parser = FrameParser()
    analyzer = Analyzer()
    input_bytes = 0
    writer.writerow(CSV_COLUMNS)
    for chunk in chunks:
        input_bytes += len(chunk)
        for frame in parser.feed(chunk):
            writer.writerow(csv_row(frame, analyzer.add(frame)))
    summary: Dict[str, object] = dict(input_bytes=input_bytes, crc_errors=parser.crc_errors,
                                      header_rejects=parser.header_rejects, skipped_bytes=parser.skipped_bytes,
                                      truncated_tail_bytes=parser.pending_bytes)
    summary.update(analyzer.summary())
    return summary


def decode_file(source: Path, target: Path) -> Dict[str, object]:
    if source.resolve() == target.resolve():
        raise ValueError("input and CSV output must be different files")
    def chunks():
        with source.open('rb') as stream:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    return
                yield chunk

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w', newline='', encoding='utf-8') as stream:
        return decode_stream(chunks(), csv.writer(stream))


def record(port: str, output: Path, seconds: Optional[float], baud: int = BAUD) -> int:
    """Save raw port bytes to a new file. Refuses to overwrite an existing capture."""
    try:
        import serial  # Optional: decoding must work without pyserial.
    except ImportError as exc:
        raise SystemExit('record requires pyserial: python -m pip install pyserial') from exc
    link = serial.Serial()
    link.port = port
    link.baudrate = baud
    link.timeout = 0.2
    # Reduces, but cannot guarantee against, the auto-reset many Nano boards do on open.
    link.dtr = False
    link.rts = False
    output.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with output.open('xb') as stream:
        try:
            link.open()
        except serial.SerialException as exc:
            stream.close()
            output.unlink()  # An empty file would make the retry refuse to overwrite.
            raise SystemExit('cannot open %s: %s' % (port, exc)) from exc
        try:
            deadline = None if seconds is None else time.monotonic() + seconds
            while deadline is None or time.monotonic() < deadline:
                data = link.read(4096)
                if data:
                    stream.write(data)
                    stream.flush()  # Keep what arrived if the cable is pulled.
                    total += len(data)
        except KeyboardInterrupt:
            pass
        finally:
            link.close()
    return total


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    decode = commands.add_parser('decode', help='convert a binary capture to CSV and print a JSON summary')
    decode.add_argument('input', type=Path)
    decode.add_argument('--csv', type=Path, required=True, help='CSV output path')
    decode.add_argument('--summary', type=Path, help='also write the JSON summary here')
    capture = commands.add_parser('record', help='save raw serial bytes (requires pyserial)')
    capture.add_argument('--port', required=True, help='for example COM5')
    capture.add_argument('--output', type=Path, required=True, help='new binary file; existing files are refused')
    capture.add_argument('--seconds', type=float, help='stop after this long; default is until Ctrl+C')
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == 'record':
        try:
            total = record(args.port, args.output, args.seconds)
        except FileExistsError:
            print('refusing to overwrite %s' % args.output, file=sys.stderr)
            return 2
        print('saved %d bytes to %s' % (total, args.output), file=sys.stderr)
        return 0
    summary = decode_file(args.input, args.csv)
    text = json.dumps(summary, indent=2)
    print(text)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(text + '\n', encoding='utf-8')
    if not summary['frames']:
        print('no valid frames in %s' % args.input, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
