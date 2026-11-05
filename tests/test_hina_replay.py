import csv
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from export_hina_replay import COLUMNS, verified_rows


class ReplayExportTests(unittest.TestCase):
    def test_decimation_preserves_off_grid_final_failure_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trace.csv'
            with path.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNS)
                writer.writeheader()
                for i in range(14):
                    row = dict.fromkeys(COLUMNS, 0)
                    row.update(ms=i * 5, turnFault=int(i == 13))
                    writer.writerow(row)
            rows = verified_rows(path, hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual([r[0] for r in rows], [0, 50, 65])
            self.assertEqual(rows[-1][COLUMNS.index('turnFault')], 1)

    def test_modified_trace_is_rejected_before_export(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trace.csv'
            path.write_text('altered data')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                verified_rows(path, '0' * 64)


if __name__ == '__main__':
    unittest.main()
