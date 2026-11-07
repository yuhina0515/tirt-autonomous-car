import csv
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.ingest import Store, Server, HEADER, Problem
from tools.upload import Client, sync_file, HEADER as CLIENT_HEADER, Lock


def record(tick=1):
    return [tick*20, 'LINE', tick*20, tick, 20, 40, 800, 40, 800, 40,
            4, 6, 0, 0, 0, 1000, 0, 0, 0, 0]


class IngestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root/'data.sqlite3')
        self.config = {'ingest_token': 'test-ingest-'+'a'*40, 'read_token': 'test-read-'+'b'*40}
        self.server = Server(('127.0.0.1', 0), self.store, self.config)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = 'http://127.0.0.1:'+str(self.server.server_port)
        self.client = Client(self.origin, self.config['ingest_token'], allow_local=True)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def session(self):
        sid = str(uuid4())
        self.client.post('/api/v1/sessions', {'id': sid, 'metadata': {}, 'header': HEADER})
        return sid

    def read(self, path, role='read'):
        request = Request(self.origin+path, headers={'Authorization': 'Bearer '+self.config[role+'_token']})
        return urlopen(request, timeout=5)

    def csv_file(self, rows):
        path = self.root/'run-test.csv'
        with path.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(HEADER)
            writer.writerows(rows)
        return path

    def test_auth_and_export(self):
        self.assertEqual(HEADER, CLIENT_HEADER)
        with urlopen(self.origin+'/health') as response:
            self.assertEqual(json.load(response)['status'], 'ok')
        with self.assertRaises(HTTPError) as error:
            urlopen(self.origin+'/api/v1/sessions')
        self.assertEqual(error.exception.code, 401)
        sid = self.session()
        self.client.post('/api/v1/sessions/'+sid+'/batches', {'sequence': 0, 'records': [record()]})
        with self.assertRaises(HTTPError) as error:
            self.read('/api/v1/sessions/'+sid+'/export.csv', role='ingest')
        self.assertEqual(error.exception.code, 401)
        with self.read('/api/v1/sessions/'+sid+'/export.csv') as response:
            rows = list(csv.reader(io.StringIO(response.read().decode())))
        self.assertEqual(rows, [HEADER, [str(v) for v in record()]])
        with self.read('/api/v1/sessions') as response:
            self.assertEqual(json.load(response)['sessions'][0]['records'], 1)
        with self.assertRaises(HTTPError) as error:
            Client(self.origin, self.config['read_token'], allow_local=True).post('/api/v1/sessions', {})
        self.assertEqual(error.exception.code, 401)

    def test_duplicate_conflict_gap_and_restart(self):
        sid = self.session()
        payload = {'sequence': 0, 'records': [record()]}
        path = '/api/v1/sessions/'+sid+'/batches'
        first = self.client.post(path, payload)
        again = self.client.post(path, payload)
        self.assertFalse(first['duplicate'])
        self.assertTrue(again['duplicate'])
        self.assertEqual(first['sha256'], again['sha256'])
        for bad in ({'sequence': 0, 'records': [record(2)]}, {'sequence': 2, 'records': [record(2)]}):
            with self.assertRaises(HTTPError) as error:
                self.client.post(path, bad)
            self.assertEqual(error.exception.code, 409)
        restored = Store(self.root/'data.sqlite3')
        result = restored.session({'id': sid, 'metadata': {}, 'header': HEADER})
        self.assertEqual((result['next_sequence'], result['records']), (1, 1))

    def test_parallel_retry_is_exactly_once(self):
        sid = self.session()
        def send(_):
            return self.client.post('/api/v1/sessions/'+sid+'/batches', {'sequence': 0, 'records': [record()]})
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(send, range(6)))
        self.assertEqual(sum(not r['duplicate'] for r in results), 1)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT records FROM sessions WHERE id=?', (sid,)).fetchone()[0], 1)

    def test_malformed_inputs_and_quota(self):
        sid = self.session()
        for bad in ([], [None]*20, record()[:-1], [record()[0], []]+record()[2:], record()[:5]+[1024]+record()[6:]):
            with self.assertRaises(HTTPError) as error:
                self.client.post('/api/v1/sessions/'+sid+'/batches', {'sequence': 0, 'records': [bad]})
            self.assertEqual(error.exception.code, 400)
        self.store.max_bytes = 1
        with self.assertRaises(HTTPError) as error:
            self.client.post('/api/v1/sessions/'+sid+'/batches', {'sequence': 0, 'records': [record()]})
        self.assertEqual(error.exception.code, 507)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT records FROM sessions WHERE id=?', (sid,)).fetchone()[0], 0)

    def test_lost_ack_while_file_grows(self):
        path = self.csv_file([record()])
        real_post = self.client.post
        def drop_ack(endpoint, payload):
            result = real_post(endpoint, payload)
            if endpoint.endswith('/batches'):
                raise URLError('simulated lost response')
            return result
        self.client.post = drop_ack
        with self.assertRaises(URLError):
            sync_file(path, self.client)
        with path.open('a', newline='') as stream:
            csv.writer(stream).writerow(record(2))
        # A new process loads its pending exact one-row batch, even though CSV now has two rows.
        fresh = Client(self.origin, self.config['ingest_token'], allow_local=True)
        self.assertEqual(sync_file(path, fresh), 2)
        self.assertEqual(sync_file(path, fresh), 0)
        state = json.loads(path.with_suffix('.upload-state.json').read_text())
        self.assertEqual((state['records'], state['next_sequence']), (2, 2))
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT records FROM sessions WHERE id=?', (state['id'],)).fetchone()[0], 2)

    def test_partial_row_and_edited_acknowledged_file(self):
        path = self.csv_file([record()])
        with path.open('ab') as stream:
            stream.write(b'40,LINE,40')
        self.assertEqual(sync_file(path, self.client), 1)
        self.assertEqual(sync_file(path, self.client), 0)
        old = path.read_bytes()
        path.write_bytes(old.replace(b'20,LINE', b'21,LINE', 1))
        with self.assertRaises(ValueError):
            sync_file(path, self.client)

    def test_retry_only_drains_more_than_one_live_pass(self):
        path = self.csv_file([record(i) for i in range(1, 2106)])
        self.assertEqual(sync_file(path, self.client, batch_limit=None), 2105)
        self.assertEqual(sync_file(path, self.client), 0)
        state = json.loads(path.with_suffix('.upload-state.json').read_text())
        self.assertEqual(state['records'], 2105)

    def test_origin_and_single_worker_guards(self):
        for origin in ('http://example.com', 'https://user:secret@example.com', 'https://example.com/?token=x'):
            with self.assertRaises(ValueError):
                Client(origin, self.config['ingest_token'])
        path = self.csv_file([record()])
        sync_file(path, self.client)
        other = Client('https://example.com', self.config['ingest_token'])
        with self.assertRaises(ValueError):
            sync_file(path, other)
        with Lock(self.root):
            with self.assertRaises(OSError):
                with Lock(self.root):
                    pass


if __name__ == '__main__':
    unittest.main()
