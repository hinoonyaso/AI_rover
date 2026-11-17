"""Exercise the mock manager with isolated databases. / 격리 DB에서 모의 관리자를 시험한다."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from mission_contract import ContractError
from mission_simulator import SimulationManager


def request():
    return {'request_id': str(uuid4()), 'mode': 'simulation', 'kind': 'inspection_demo', 'parameters': {}}


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/tmp')
        self.path = Path(self.tmp.name) / 'missions.db'
        self.manager = SimulationManager(self.path)

    def tearDown(self):
        self.manager.close()
        self.tmp.cleanup()

    def test_success_and_idempotent_create(self):
        payload = request()
        mission, created = self.manager.create(payload)
        again, duplicate_created = self.manager.create(payload)
        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(mission['id'], again['id'])
        queued = self.manager.start(mission['id'])
        running = self.manager.step(mission['id'], queued['version'])
        done = self.manager.step(mission['id'], running['version'])
        self.assertEqual(done['state'], 'succeeded')
        self.assertEqual([e['state'] for e in self.manager.events(mission['id'])], ['created', 'queued', 'running', 'succeeded'])
        self.assertIn('simulated', done['result'])

    def test_concurrent_duplicate_create(self):
        payload = request()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(self.manager.create, [payload, payload]))
        self.assertEqual(results[0][0]['id'], results[1][0]['id'])
        self.assertCountEqual([item[1] for item in results], [True, False])
        self.assertEqual(len(self.manager.events(results[0][0]['id'])), 1)

    def test_failure_timeout_and_cancellation(self):
        for outcome in ('failure', 'timeout'):
            item, _ = self.manager.create(request())
            queued = self.manager.start(item['id'])
            running = self.manager.step(item['id'], queued['version'])
            result = self.manager.step(item['id'], running['version'], outcome)
            self.assertEqual((result['state'], result['reason']), ('failed', 'simulation_' + outcome))
        item, _ = self.manager.create(request())
        queued = self.manager.start(item['id'])
        pending = self.manager.cancel(item['id'])
        self.assertEqual(pending['state'], 'cancel_requested')
        with self.assertRaises(ContractError):
            self.manager.step(item['id'], queued['version'])
        self.assertEqual(self.manager.step(item['id'], pending['version'])['state'], 'canceled')

    def test_concurrent_start_and_single_owner(self):
        first, _ = self.manager.create(request())
        second, _ = self.manager.create(request())
        def attempt(item):
            try:
                return self.manager.start(item['id'])['state']
            except ContractError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, [first, second]))
        self.assertCountEqual(results, ['queued', 'mission_busy'])
        with self.assertRaises(ContractError) as error:
            SimulationManager(self.path)
        self.assertEqual(error.exception.code, 'manager_unavailable')

    def test_restart_interrupts_and_fences_old_result(self):
        item, _ = self.manager.create(request())
        queued = self.manager.start(item['id'])
        self.manager.close()
        self.manager = SimulationManager(self.path)
        recovered = self.manager.get(item['id'])
        self.assertEqual((recovered['state'], recovered['reason']), ('interrupted', 'manager_restarted'))
        with self.assertRaises(ContractError) as error:
            self.manager.step(item['id'], queued['version'])
        self.assertEqual(error.exception.code, 'stale_result')
        other, _ = self.manager.create(request())
        self.assertEqual(self.manager.start(other['id'])['state'], 'queued')

    def test_history_failure_rolls_back_state_and_slot(self):
        item, _ = self.manager.create(request())
        with sqlite3.connect(self.path) as conn:
            conn.execute("CREATE TRIGGER fail_queued BEFORE INSERT ON mission_events WHEN NEW.state = 'queued' BEGIN SELECT RAISE(ABORT, 'simulated failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.manager.start(item['id'])
        self.assertEqual(self.manager.get(item['id'])['state'], 'created')
        with sqlite3.connect(self.path) as conn:
            self.assertIsNone(conn.execute('SELECT mission_id FROM mission_execution_slot').fetchone()[0])
        self.assertEqual(len(self.manager.events(item['id'])), 1)

    def test_reject_outside_tmp(self):
        with self.assertRaises(ValueError):
            SimulationManager('/home/sang/not-an-isolated-db')


if __name__ == '__main__':
    unittest.main()
