"""Persist simulated missions in MySQL with one fenced database session.

한글: 하나의 DB 세션으로 모의 임무를 MySQL에 영구 저장한다.
"""
from contextlib import contextmanager
import sqlite3
import threading

import pymysql
from pymysql.cursors import DictCursor

from mission_contract import ContractError
from mission_simulator import SimulationManager


class _Connection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, args=()):
        cursor = self.connection.cursor()
        cursor.execute(query.replace('?', '%s'), args)
        return cursor


class MySQLMissionManager(SimulationManager):
    """Own the DB lock and serialize mission transactions on its session.

    한글: DB 잠금을 소유하고 동일 세션에서 임무 트랜잭션을 직렬화한다.
    """
    def __init__(self, socket, database='jetinspect', legacy_path=None):
        self._mutex = threading.RLock()
        self._closed = False
        self._connection = pymysql.connect(user='root', unix_socket=str(socket), database=database,
                                           cursorclass=DictCursor, connect_timeout=3,
                                           read_timeout=5, write_timeout=5, autocommit=False,
                                           charset='utf8mb4')
        self._lock_name = 'jetinspect.mission.manager.' + database
        try:
            with self._connection.cursor() as cur:
                cur.execute('SELECT GET_LOCK(%s, 0) AS acquired', (self._lock_name,))
                if cur.fetchone()['acquired'] != 1:
                    raise ContractError('manager_unavailable')
                for query in (
                    '''CREATE TABLE IF NOT EXISTS missions (
                    id VARCHAR(36) PRIMARY KEY, request_id VARCHAR(36) NOT NULL UNIQUE,
                    mode VARCHAR(32) NOT NULL, kind VARCHAR(64) NOT NULL, parameters TEXT NOT NULL,
                    state VARCHAR(32) NOT NULL, stage VARCHAR(64), version INT NOT NULL,
                    created_at VARCHAR(40) NOT NULL, started_at VARCHAR(40), finished_at VARCHAR(40),
                    result TEXT, reason VARCHAR(128), INDEX mission_created (created_at, id)) ENGINE=InnoDB''',
                    '''CREATE TABLE IF NOT EXISTS mission_events (
                    mission_id VARCHAR(36) NOT NULL, version INT NOT NULL, previous_state VARCHAR(32),
                    state VARCHAR(32) NOT NULL, stage VARCHAR(64), recorded_at VARCHAR(40) NOT NULL,
                    source VARCHAR(32) NOT NULL, reason VARCHAR(128), details TEXT,
                    PRIMARY KEY (mission_id, version), FOREIGN KEY (mission_id) REFERENCES missions(id)) ENGINE=InnoDB''',
                    '''CREATE TABLE IF NOT EXISTS mission_execution_slot (
                    id INT PRIMARY KEY, mission_id VARCHAR(36),
                    FOREIGN KEY (mission_id) REFERENCES missions(id)) ENGINE=InnoDB''',
                    '''CREATE TABLE IF NOT EXISTS mission_migrations (
                    name VARCHAR(100) PRIMARY KEY, completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB''',
                ):
                    cur.execute(query)
                cur.execute('INSERT IGNORE INTO mission_execution_slot (id, mission_id) VALUES (1, NULL)')
            self._connection.commit()
            if legacy_path and legacy_path.is_file():
                self._import_legacy(legacy_path)
            with self._transaction() as conn:
                for row in conn.execute("SELECT * FROM missions WHERE state IN ('queued','running','cancel_requested')").fetchall():
                    self._transition(conn, row, 'interrupted', reason='manager_restarted', source='recovery')
                conn.execute('UPDATE mission_execution_slot SET mission_id = NULL WHERE id = 1')
        except Exception:
            self.close()
            raise

    def _import_legacy(self, path):
        # The old database remains untouched; insertion and the migration marker commit together.
        # 한글: 기존 DB는 보존하며 복사와 이전 완료 표시는 한 트랜잭션으로 처리한다.
        uri = path.resolve().as_uri() + '?mode=ro'
        with sqlite3.connect(uri, uri=True) as source:
            source.row_factory = sqlite3.Row
            source.execute('BEGIN')
            missions = source.execute('SELECT * FROM missions ORDER BY rowid').fetchall()
            events = source.execute('SELECT * FROM mission_events ORDER BY mission_id, version').fetchall()
        with self._transaction() as conn:
            if conn.execute("SELECT name FROM mission_migrations WHERE name = 'sqlite-v1'").fetchone():
                return
            if conn.execute('SELECT id FROM missions LIMIT 1').fetchone():
                raise ContractError('migration_conflict')
            for row in missions:
                conn.execute('''INSERT INTO missions (id, request_id, mode, kind, parameters, state, stage, version,
                    created_at, started_at, finished_at, result, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', tuple(row))
            for row in events:
                conn.execute('''INSERT INTO mission_events (mission_id, version, previous_state, state, stage, recorded_at,
                    source, reason, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', tuple(row))
            conn.execute("INSERT INTO mission_migrations (name) VALUES ('sqlite-v1')")

    @contextmanager
    def _transaction(self):
        with self._mutex:
            if self._closed:
                raise ContractError('manager_unavailable')
            try:
                # Reconnection would silently lose GET_LOCK and is deliberately forbidden.
                # 한글: 재연결하면 GET_LOCK이 사라지므로 자동 재연결을 금지한다.
                self._connection.ping(reconnect=False)
                self._connection.begin()
                yield _Connection(self._connection)
                self._connection.commit()
            except Exception:
                try:
                    self._connection.rollback()
                except pymysql.Error:
                    pass
                raise

    def list_recent(self, limit=50, offset=0, before=None):
        """Read a bounded mission page. / 제한된 임무 목록 페이지를 읽는다."""
        if not 1 <= limit <= 101 or not 0 <= offset <= 100000:
            raise ContractError('invalid_request')
        with self._transaction() as conn:
            if before:
                return conn.execute('SELECT * FROM missions WHERE (created_at < ? OR (created_at = ? AND id < ?)) ORDER BY created_at DESC, id DESC LIMIT ?',
                                    (before[0], before[0], before[1], limit)).fetchall()
            return conn.execute('SELECT * FROM missions ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?',
                                (limit, offset)).fetchall()

    def close(self):
        """Release the database session and lock. / DB 세션과 소유권 잠금을 반환한다."""
        with self._mutex:
            if not self._closed:
                self._closed = True
                try:
                    self._connection.close()
                except pymysql.Error:
                    pass
