"""Exercise MySQL mission storage in a disposable schema. / 격리 스키마에서 MySQL 임무 저장소를 시험한다."""
from pathlib import Path
import sys
import tempfile
import unittest
from uuid import uuid4

import pymysql

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from mission_contract import ContractError
from mission_mysql import MySQLMissionManager
from mission_simulator import SimulationManager


class MySQLMissionTests(unittest.TestCase):
    def setUp(self):
        self.socket = Path.home() / '.local/share/jetinspect-ops/mysql-run/mysql.sock'
        self.db = 'jetinspect_test_' + uuid4().hex[:12]
        self.admin = pymysql.connect(user='root', unix_socket=str(self.socket), autocommit=True)
        with self.admin.cursor() as cur:
            cur.execute(f'CREATE DATABASE `{self.db}` CHARACTER SET utf8mb4')
        self.manager = None

    def tearDown(self):
        if self.manager:
            self.manager.close()
        with self.admin.cursor() as cur:
            cur.execute(f'DROP DATABASE `{self.db}`')
        self.admin.close()

    def test_migration_owner_and_restart(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as folder:
            legacy = Path(folder) / 'old.sqlite3'
            old = SimulationManager(legacy)
            payload = {'request_id': str(uuid4()), 'mode': 'simulation', 'kind': 'inspection_demo', 'parameters': {}}
            row, _ = old.create(payload)
            old.start(row['id'])
            old.close()
            self.manager = MySQLMissionManager(self.socket, self.db, legacy)
            self.assertEqual(self.manager.get(row['id'])['state'], 'interrupted')
            self.assertEqual(self.manager.events(row['id'])[-1]['reason'], 'manager_restarted')
            self.assertEqual(self.manager.create(payload)[0]['id'], row['id'])
            with self.assertRaises(ContractError):
                MySQLMissionManager(self.socket, self.db)
            self.manager.close()
            self.manager = MySQLMissionManager(self.socket, self.db, legacy)
            self.assertEqual(len(self.manager.list_recent()), 1)
            self.assertTrue(legacy.exists())

    def test_atomic_rollback_and_page(self):
        self.manager = MySQLMissionManager(self.socket, self.db)
        items = []
        for _ in range(3):
            row, _ = self.manager.create({'request_id': str(uuid4()), 'mode': 'simulation',
                                          'kind': 'inspection_demo', 'parameters': {}})
            items.append(row)
        self.assertEqual(len(self.manager.list_recent(limit=2)), 2)
        self.assertEqual(len(self.manager.list_recent(limit=2, offset=2)), 1)
        with self.manager._connection.cursor() as cur:
            cur.execute("CREATE TRIGGER fail_mission_event BEFORE INSERT ON mission_events FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='test failure'")
        with self.assertRaises(pymysql.Error):
            self.manager.start(items[0]['id'])
        self.assertEqual(self.manager.get(items[0]['id'])['state'], 'created')

    def test_lost_lock_session_does_not_reconnect(self):
        self.manager = MySQLMissionManager(self.socket, self.db)
        self.manager._connection.close()
        with self.assertRaises(pymysql.Error):
            self.manager.list_recent()
        replacement = MySQLMissionManager(self.socket, self.db)
        replacement.close()

    def test_success_and_events_persist_across_restart(self):
        self.manager = MySQLMissionManager(self.socket, self.db)
        row, _ = self.manager.create({'request_id': str(uuid4()), 'mode': 'simulation',
                                      'kind': 'inspection_demo', 'parameters': {}})
        queued = self.manager.start(row['id'])
        running = self.manager.step(row['id'], queued['version'])
        self.manager.step(row['id'], running['version'])
        self.manager.close()
        self.manager = MySQLMissionManager(self.socket, self.db)
        self.assertEqual(self.manager.get(row['id'])['state'], 'succeeded')
        self.assertEqual([event['state'] for event in self.manager.events(row['id'])],
                         ['created', 'queued', 'running', 'succeeded'])

    def test_cursor_ignores_newer_insertions(self):
        self.manager = MySQLMissionManager(self.socket, self.db)
        for _ in range(4):
            self.manager.create({'request_id': str(uuid4()), 'mode': 'simulation',
                                 'kind': 'inspection_demo', 'parameters': {}})
        first = self.manager.list_recent(limit=2)
        self.manager.create({'request_id': str(uuid4()), 'mode': 'simulation',
                             'kind': 'inspection_demo', 'parameters': {}})
        second = self.manager.list_recent(limit=2, before=[first[-1]['created_at'], first[-1]['id']])
        self.assertEqual(len(second), 2)
        self.assertTrue({row['id'] for row in first}.isdisjoint(row['id'] for row in second))


if __name__ == '__main__':
    unittest.main()
