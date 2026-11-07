"""Authenticated, idempotent TIRT telemetry ingestion. Python standard library only."""
import argparse
import csv
from contextlib import contextmanager
import hashlib
import hmac
import io
import json
from pathlib import Path
import re
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import UUID

VERSION = '0.3.0-rc.1'
HEADER = ['host_ms', 'label', 'millis', 'tick', 'dt', 'rawA5', 'rawA4', 'rawA3', 'rawA2', 'rawA1',
          'mask', 'state', 'reason', 'position', 'accepted_position', 'contrast',
          'left_pwm', 'right_pwm', 'rejected', 'timing_faults']
LABELS = {'UNLABELLED', 'LINE', 'BACKGROUND', 'TEXT', 'TRACK', 'MARKER'}
MAX_BODY = 256 * 1024


class Problem(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)


def integer(value, lo, hi):
    return type(value) is int and lo <= value <= hi


def valid_record(row):
    if not isinstance(row, list) or len(row) != len(HEADER) or not isinstance(row[1], str) or row[1] not in LABELS:
        return False
    if any(type(v) is not int for i, v in enumerate(row) if i != 1):
        return False
    return (integer(row[0], 0, 2**53-1) and all(integer(row[i], 0, 2**32-1) for i in (2, 3, 4, 18, 19))
            and all(integer(row[i], 0, 1023) for i in range(5, 10))
            and row[10] in range(0, 15, 2) and integer(row[11], 0, 6) and integer(row[12], 0, 16)
            and all(integer(row[i], -1000, 1000) for i in (13, 14))
            and integer(row[15], 0, 1000) and all(integer(row[i], 0, 255) for i in (16, 17)))


class Store:
    def __init__(self, path, max_bytes=2*1024**3):
        self.path = str(path)
        self.max_bytes = max_bytes
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, metadata TEXT NOT NULL, created INTEGER NOT NULL,
                    next_seq INTEGER NOT NULL DEFAULT 0, records INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS batches (
                    session TEXT NOT NULL REFERENCES sessions(id), seq INTEGER NOT NULL,
                    digest TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(session, seq));
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    def room(self, extra):
        size = sum(p.stat().st_size for p in (Path(self.path), Path(self.path+'-wal')) if p.exists())
        if size + extra > self.max_bytes:
            raise Problem(507, 'storage_quota_reached')

    def session(self, value):
        if set(value) != {'id', 'metadata', 'header'} or value['header'] != HEADER:
            raise Problem(400, 'invalid_session_contract')
        try:
            sid = str(UUID(value['id']))
        except (ValueError, TypeError, AttributeError):
            raise Problem(400, 'invalid_session_id')
        meta = value['metadata']
        if not isinstance(meta, dict) or set(meta) - {'file', 'firmware', 'source_commit', 'experiment'}:
            raise Problem(400, 'invalid_metadata')
        if any(not isinstance(v, str) or len(v) > 200 or any(ord(c) < 32 for c in v) for v in meta.values()):
            raise Problem(400, 'invalid_metadata')
        payload = canonical(meta)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT metadata,next_seq,records FROM sessions WHERE id=?', (sid,)).fetchone()
            if old:
                if old[0] != payload:
                    raise Problem(409, 'session_metadata_conflict')
                return {'id': sid, 'next_sequence': old[1], 'records': old[2]}
            self.room(len(payload) + 4096)
            db.execute('INSERT INTO sessions(id,metadata,created) VALUES(?,?,?)', (sid, payload, int(time.time())))
        return {'id': sid, 'next_sequence': 0, 'records': 0}

    def batch(self, sid, value):
        if set(value) != {'sequence', 'records'} or not integer(value['sequence'], 0, 1000000):
            raise Problem(400, 'invalid_batch')
        rows = value['records']
        if not isinstance(rows, list) or not 1 <= len(rows) <= 200 or not all(valid_record(r) for r in rows):
            raise Problem(400, 'invalid_records')
        seq = value['sequence']
        payload = canonical(rows)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT next_seq,records FROM sessions WHERE id=?', (sid,)).fetchone()
            if current is None:
                raise Problem(404, 'session_not_found')
            old = db.execute('SELECT digest FROM batches WHERE session=? AND seq=?', (sid, seq)).fetchone()
            if old:
                if not hmac.compare_digest(old[0], digest):
                    raise Problem(409, 'sequence_content_conflict')
                return {'sequence': seq, 'sha256': digest, 'duplicate': True, 'accepted': len(rows)}
            if seq != current[0]:
                raise Problem(409, 'sequence_gap')
            if current[1] + len(rows) > 1000000:
                raise Problem(413, 'session_record_limit')
            self.room(len(payload.encode()) + 8192)
            db.execute('INSERT INTO batches VALUES(?,?,?,?)', (sid, seq, digest, payload))
            db.execute('UPDATE sessions SET next_seq=next_seq+1,records=records+? WHERE id=?', (len(rows), sid))
        return {'sequence': seq, 'sha256': digest, 'duplicate': False, 'accepted': len(rows)}


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store, config):
        for key in ('ingest_token', 'read_token'):
            if not isinstance(config.get(key), str) or len(config[key]) < 32:
                raise ValueError('A strong '+key+' is required')
        if config['ingest_token'] == config['read_token']:
            raise ValueError('Read and ingest tokens must differ')
        self.store, self.config = store, config
        self.slots = threading.BoundedSemaphore(12)
        super().__init__(address, Handler)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    server_version = 'TirtData'
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *args):
        pass  # Do not log credentials, request URLs or telemetry.

    def reply(self, code, value):
        data = canonical(value).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self, role):
        actual = self.headers.get('Authorization', '')
        return hmac.compare_digest(actual.encode(), ('Bearer '+self.server.config[role+'_token']).encode())

    def body(self):
        if self.headers.get('Transfer-Encoding'):
            raise Problem(400, 'content_length_required')
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            raise Problem(415, 'application_json_required')
        try:
            n = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise Problem(400, 'invalid_content_length')
        if not 0 < n <= MAX_BODY:
            raise Problem(413, 'body_limit')
        data = self.rfile.read(n)
        try:
            value = json.loads(data)
        except (ValueError, UnicodeError):
            raise Problem(400, 'invalid_json')
        if not isinstance(value, dict):
            raise Problem(400, 'object_required')
        return value

    def do_POST(self):
        try:
            if not self.authorized('ingest'):
                raise Problem(401, 'unauthorized')
            value = self.body()
            if self.path == '/api/v1/sessions':
                return self.reply(200, self.server.store.session(value))
            match = re.fullmatch(r'/api/v1/sessions/([0-9a-f-]{36})/batches', self.path)
            if match:
                return self.reply(200, self.server.store.batch(match[1], value))
            raise Problem(404, 'not_found')
        except Problem as e:
            self.reply(e.code, {'error': e.message})
        except (sqlite3.Error, OSError):
            self.reply(503, {'error': 'storage_unavailable'})

    def do_GET(self):
        try:
            if self.path == '/health':
                with self.server.store.connect() as db:
                    db.execute('SELECT 1').fetchone()
                return self.reply(200, {'status': 'ok', 'version': VERSION})
            if not self.authorized('read'):
                raise Problem(401, 'unauthorized')
            if self.path == '/api/v1/sessions':
                with self.server.store.connect() as db:
                    rows = db.execute('SELECT id,created,records,metadata FROM sessions ORDER BY created DESC LIMIT 100').fetchall()
                return self.reply(200, {'sessions': [{'id': r[0], 'created': r[1], 'records': r[2], 'metadata': json.loads(r[3])} for r in rows]})
            match = re.fullmatch(r'/api/v1/sessions/([0-9a-f-]{36})/export.csv', self.path)
            if not match:
                raise Problem(404, 'not_found')
            with self.server.store.connect() as db:
                if not db.execute('SELECT 1 FROM sessions WHERE id=?', (match[1],)).fetchone():
                    raise Problem(404, 'session_not_found')
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="'+match[1]+'.csv"')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                def write_row(row):
                    output = io.StringIO(newline='')
                    csv.writer(output).writerow(row)
                    self.wfile.write(output.getvalue().encode())
                write_row(HEADER)
                for (payload,) in db.execute('SELECT payload FROM batches WHERE session=? ORDER BY seq', (match[1],)):
                    for row in json.loads(payload):
                        write_row(row)
        except Problem as e:
            self.reply(e.code, {'error': e.message})
        except (sqlite3.Error, OSError):
            self.close_connection = True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=Path('/data/telemetry.sqlite3'))
    parser.add_argument('--config', type=Path, default=Path('/run/tirt-config.json'))
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8212)
    args = parser.parse_args()
    Server((args.host, args.port), Store(args.database), json.loads(args.config.read_text())).serve_forever()
