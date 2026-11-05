"""Export verified, downsampled telemetry for the Hina Web project player."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ['ms', 'x', 'y', 'z', 'yaw', 'pitch', 'left', 'right', 'vl', 'vr',
           'a5', 'a4', 'a3', 'a2', 'a1', 'sensorF', 'turnFault', 'liftState',
           'lift_phase', 'seesaw_theta']


def verified_rows(path, expected_hash):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
        raise ValueError('Trace hash mismatch: ' + path.name)
    with path.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    # Display at50ms; retain the exact final frame even off this grid.
    sampled = rows[::10]
    if (len(rows) - 1) % 10:
        sampled.append(rows[-1])
    return [[round(float(row[key]), 6) for key in COLUMNS] for row in sampled]


def export(base, output):
    spec = json.loads((base / 'reference-711/course.json').read_text())
    catalogue = json.loads((ROOT / 'docs/start-finish-2026-11-05/scenarios.json').read_text())
    if hashlib.sha256((base / 'reference-711/course.json').read_bytes()).hexdigest() != catalogue['course_sha256']:
        raise ValueError('Catalogue and reference course differ')
    runs = []
    for folder, label in [('reference-711', '既有賽道策略 · 完整圈'), ('layered-711', '新兩層控制 · 空路線基準')]:
        directory = base / folder
        if json.loads((directory / 'course.json').read_text()) != spec:
            raise ValueError('Comparison courses differ')
        result = json.loads((directory / 'results.json').read_text())['attempts'][0]
        if not result['native_trace_replay_verified'] or not result['physical_sensor_origin_verified']:
            raise ValueError('Replay lacks actual-core or physical-sensor verification')
        rows = verified_rows(directory / result['trace_file'], result['trace_sha256'])
        phase_times = [0]
        for phase in catalogue['phases'][1:]:
            station = catalogue['segments_analysis'][phase['start']]['model_start_m']
            phase_times.append(next((g['ms'] for g in result['gate_events'] if g['station_m'] >= station - .0001), None))
        runs.append(dict(id=folder, label=label, rows=rows, phaseTimes=phase_times,
                         result={k: result[k] for k in ['outcome', 'elapsed_s', 'simulation_seconds',
                             'gates_crossed', 'gates_required', 'gate_events', 'trace_sha256',
                             'independent_checks', 'first_violation', 'first_violation_ms',
                             'native_trace_replay_verified', 'physical_sensor_origin_verified']}))
    import fitz
    document = fitz.open(ROOT / spec['source_pdf'])
    embedded = document.extract_image(spec['source_map']['pdf_image_xref'])
    output.mkdir(parents=True, exist_ok=True)
    image_name = 'course.' + embedded['ext']
    (output / image_name).write_bytes(embedded['image'])
    payload = dict(schema=1, kind='verified_simulation_replay_not_live_solver', date='2026-11-05',
                   columns=COLUMNS, image=image_name, runs=runs, points=spec['points_px'],
                   raised=spec['raised_occurrences'], dimensions=spec['source_map'],
                   assumptions=spec['assumptions'], seed=2026110711,
                   courseHash=catalogue['course_sha256'], phases=catalogue['phases'])
    (output / 'replay.json').write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    (output / 'scenarios.json').write_text(json.dumps(catalogue, ensure_ascii=False), encoding='utf-8')
    (output / 'manifest.json').write_text(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(output.iterdir()) if p.name != 'manifest.json'}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(output), 'frames': [len(r['rows']) for r in runs],
                      'json_bytes': (output / 'replay.json').stat().st_size}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'build-output/start-finish-20261105')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    export(args.source, args.output)
