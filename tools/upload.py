"""Tail locally durable capture CSVs and upload exact retryable batches over HTTPS."""
import argparse
import csv
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from uuid import uuid4

HEADER = ['host_ms', 'label', 'millis', 'tick', 'dt', 'rawA5', 'rawA4', 'rawA3', 'rawA2', 'rawA1',
          'mask', 'state', 'reason', 'position', 'accepted_position', 'contrast',
          'left_pwm', 'right_pwm', 'rejected', 'timing_faults']


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)


def save(path, value):
    temp = path.with_suffix(path.suffix+'.tmp')
    with temp.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(canonical(value)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # Never forward the credential to a redirected origin.


class Client:
    def __init__(self, origin, token, allow_local=False):
        target = urlsplit(origin)
        local = allow_local and target.scheme == 'http' and target.hostname in ('127.0.0.1', 'localhost')
        if (target.scheme != 'https' and not local) or not target.hostname or target.username or target.password or target.query or target.fragment:
            raise ValueError('An HTTPS API origin without embedded credentials is required')
        if not token or len(token) < 32:
            raise ValueError('TIRT_UPLOAD_TOKEN must contain the private upload token')
        self.origin, self.token = origin.rstrip('/'), token
        self.opener = build_opener(NoRedirect())

    def post(self, path, value):
        request = Request(self.origin+path, data=canonical(value).encode(), method='POST',
                          headers={'Authorization': 'Bearer '+self.token, 'Content-Type': 'application/json'})
        with self.opener.open(request, timeout=5) as response:
            return json.loads(response.read(16384))


def sync_file(path, client, metadata=None, batch_limit=20):
    state_path = path.with_suffix('.upload-state.json')
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding='utf-8'))
        if state['origin'] != client.origin:
            raise ValueError('API origin differs from the saved upload state')
    else:
        state = {'id': str(uuid4()), 'origin': client.origin, 'offset': 0,
                 'prefix_sha256': hashlib.sha256(b'').hexdigest(), 'next_sequence': 0,
                 'records': 0, 'pending': None, 'metadata': {'file': path.name, **(metadata or {})}}
        save(state_path, state)
    client.post('/api/v1/sessions', {'id': state['id'], 'metadata': state['metadata'], 'header': HEADER})
    uploaded = 0
    # Bound one pass so another session is not starved by a growing file.
    for index in itertools.count():
        if batch_limit is not None and index >= batch_limit:
            break
        with path.open('rb') as stream:
            prefix = stream.read(state['offset'])
            if len(prefix) != state['offset'] or hashlib.sha256(prefix).hexdigest() != state['prefix_sha256']:
                raise ValueError('Capture was edited/truncated after acknowledgement; preserve it as a separate run')
            if not state['pending']:
                if state['offset'] == 0:
                    header = stream.readline()
                    if not header.endswith(b'\n'):
                        return uploaded
                    if next(csv.reader([header.decode('utf-8-sig')])) != HEADER:
                        raise ValueError('Capture CSV header does not match this firmware contract')
                    prefix += header
                rows = []
                for _ in range(100):
                    raw = stream.readline()
                    if not raw.endswith(b'\n'):
                        break  # Writer has not completed this row; do not acknowledge it.
                    values = next(csv.reader([raw.decode('utf-8')]))
                    if len(values) != len(HEADER):
                        raise ValueError('Invalid capture CSV row')
                    row = [v if i == 1 else int(v) for i, v in enumerate(values)]
                    rows.append(row)
                    prefix += raw
                if not rows:
                    return uploaded
                state['pending'] = {'sequence': state['next_sequence'], 'records': rows,
                                    'end_offset': len(prefix), 'prefix_sha256': hashlib.sha256(prefix).hexdigest()}
                save(state_path, state)  # Exact batch survives a lost server response while CSV grows.
            pending = state['pending']
            # Verify the pending bytes too; the collector's contract is append-only.
            stream.seek(0)
            pending_bytes = stream.read(pending['end_offset'])
            if hashlib.sha256(pending_bytes).hexdigest() != pending['prefix_sha256']:
                raise ValueError('Capture changed while a batch was awaiting acknowledgement')
        response = client.post('/api/v1/sessions/'+state['id']+'/batches',
                               {'sequence': pending['sequence'], 'records': pending['records']})
        digest = hashlib.sha256(canonical(pending['records']).encode()).hexdigest()
        if (response.get('sha256') != digest or response.get('sequence') != pending['sequence']
                or response.get('accepted') != len(pending['records'])):
            raise ValueError('Server acknowledgement does not match the pending batch')
        state['offset'] = pending['end_offset']
        state['prefix_sha256'] = pending['prefix_sha256']
        state['next_sequence'] += 1
        state['records'] += len(pending['records'])
        uploaded += len(pending['records'])
        state['pending'] = None
        save(state_path, state)
        print('UPLOADED file='+path.name+' session='+state['id']+' rows='+str(state['records']), flush=True)
    return uploaded


class Lock:
    def __init__(self, directory):
        self.path = directory / '.upload.lock'

    def __enter__(self):
        self.stream = self.path.open('a+b')
        self.stream.seek(0)
        self.stream.write(b'0')
        self.stream.flush()
        self.stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception:
            self.stream.close()
            raise
        return self

    def __exit__(self, *args):
        self.stream.close()  # OS releases the lock even after process termination.


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parents[1]/'captures')
    parser.add_argument('--api', default='https://hina-tw.ddns.net/tirt-data')
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--stop-file', type=Path)
    parser.add_argument('--firmware', default='UNVERIFIED')
    parser.add_argument('--experiment', default='FIELD_CAPTURE')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error('Python 3.10 or later is required')
    client = Client(args.api, os.environ.get('TIRT_UPLOAD_TOKEN', ''))
    args.directory.mkdir(parents=True, exist_ok=True)
    with Lock(args.directory):
        while True:
            failed = False
            finishing = not args.watch or (args.stop_file and args.stop_file.exists())
            for path in sorted(args.directory.glob('run-*.csv')):
                try:
                    sync_file(path, client, {'firmware': args.firmware, 'experiment': args.experiment},
                              batch_limit=None if finishing else 20)
                except HTTPError as error:
                    failed = True
                    print('PENDING file='+path.name+' HTTP='+str(error.code), flush=True)
                except (URLError, TimeoutError, OSError, ValueError, KeyError) as error:
                    failed = True
                    print('PENDING file='+path.name+' error='+type(error).__name__, flush=True)
            if finishing:
                return int(failed)
            time.sleep(2)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print('Uploader could not start: '+type(error).__name__, file=sys.stderr)
        sys.exit(1)
