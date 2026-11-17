"""Isolated SQLite simulation manager; never connect to ROS or production DB.

한글: 격리된 SQLite 모의 관리자이며 ROS와 운영 DB에 연결하지 않는다.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import sqlite3
import threading
from uuid import uuid4

from mission_contract import ContractError, validate_create_request, validate_transition, valid_inspection_result


TERMINAL = frozenset(('succeeded', 'failed', 'canceled', 'interrupted'))


def utc_now():
    """Return a UTC timestamp. / UTC 시각을 반환한다."""
    return datetime.now(timezone.utc).isoformat()


class SimulationManager:
    """Own one isolated simulation database and execute explicit mock steps.

    한글: 격리 DB를 독점하고 명시적인 모의 단계만 실행한다.
    """
    def __init__(self, path):
        self.path = Path(path).resolve()
        # This prototype must not be attached to the operational database.
        # 한글: 이 시제품은 운영 DB에 연결되지 않도록 임시 디렉터리만 허용한다.
        if not self.path.is_relative_to(Path('/tmp').resolve()) or self.path.name in ('', '.', '..'):
            raise ValueError('simulation database must be under /tmp')
        self._mutex = threading.RLock()
        self._lock = open(str(self.path) + '.lock', 'a+b')
        try:
            fcntl.flock(self._lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock.close()
            raise ContractError('manager_unavailable') from None
        self._closed = False
        try:
            with self._transaction() as conn:
                conn.execute('''CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY, request_id TEXT NOT NULL UNIQUE,
                    mode TEXT NOT NULL, kind TEXT NOT NULL, parameters TEXT NOT NULL,
                    state TEXT NOT NULL, stage TEXT, version INTEGER NOT NULL,
                    created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT,
                    result TEXT, reason TEXT)''')
                conn.execute('''CREATE TABLE IF NOT EXISTS mission_events (
                    mission_id TEXT NOT NULL REFERENCES missions(id), version INTEGER NOT NULL,
                    previous_state TEXT, state TEXT NOT NULL, stage TEXT,
                    recorded_at TEXT NOT NULL, source TEXT NOT NULL, reason TEXT, details TEXT,
                    PRIMARY KEY (mission_id, version))''')
                conn.execute('''CREATE TABLE IF NOT EXISTS mission_execution_slot (
                    id INTEGER PRIMARY KEY CHECK (id = 1), mission_id TEXT REFERENCES missions(id))''')
                conn.execute('INSERT OR IGNORE INTO mission_execution_slot (id, mission_id) VALUES (1, NULL)')
                for row in conn.execute("SELECT * FROM missions WHERE state IN ('queued','running','cancel_requested')").fetchall():
                    self._transition(conn, row, 'interrupted', reason='manager_restarted', source='recovery')
                conn.execute('UPDATE mission_execution_slot SET mission_id = NULL WHERE id = 1')
        except Exception:
            self.close()
            raise

    @contextmanager
    def _transaction(self):
        with self._mutex:
            if self._closed:
                raise ContractError('manager_unavailable')
            conn = sqlite3.connect(self.path, timeout=5, isolation_level=None)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute('PRAGMA foreign_keys = ON')
                conn.execute('BEGIN IMMEDIATE')
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def _row(self, conn, mission_id):
        row = conn.execute('SELECT * FROM missions WHERE id = ?', (mission_id,)).fetchone()
        if row is None:
            raise ContractError('mission_not_found')
        return row

    def _transition(self, conn, row, state, *, stage=None, reason=None, result=None, source='manager'):
        validate_transition(row['state'], state)
        version = row['version'] + 1
        now = utc_now()
        started_at = now if state == 'running' and row['started_at'] is None else row['started_at']
        finished_at = now if state in TERMINAL else None
        updated = conn.execute('''UPDATE missions SET state = ?, stage = ?, version = ?, started_at = ?,
            finished_at = ?, reason = ?, result = ? WHERE id = ? AND version = ?''',
            (state, stage, version, started_at, finished_at, reason, json.dumps(result) if result is not None else None,
             row['id'], row['version']))
        if updated.rowcount != 1:
            raise ContractError('stale_result')
        conn.execute('''INSERT INTO mission_events (mission_id, version, previous_state, state, stage, recorded_at, source, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (row['id'], version, row['state'], state, stage, now, source, reason))
        if state in TERMINAL:
            conn.execute('UPDATE mission_execution_slot SET mission_id = NULL WHERE id = 1 AND mission_id = ?', (row['id'],))
        return self._row(conn, row['id'])

    def create(self, payload):
        """Create once per request key. / 요청 키별 임무를 한 번 생성한다."""
        request = validate_create_request(payload)
        with self._transaction() as conn:
            existing = conn.execute('SELECT * FROM missions WHERE request_id = ?', (request['request_id'],)).fetchone()
            if existing:
                if (existing['mode'], existing['kind'], json.loads(existing['parameters'])) != (request['mode'], request['kind'], request['parameters']):
                    raise ContractError('idempotency_conflict')
                return dict(existing), False
            mission_id, now = str(uuid4()), utc_now()
            conn.execute('''INSERT INTO missions (id, request_id, mode, kind, parameters, state, version, created_at)
                VALUES (?, ?, ?, ?, ?, 'created', 1, ?)''',
                (mission_id, request['request_id'], request['mode'], request['kind'], json.dumps(request['parameters']), now))
            conn.execute('''INSERT INTO mission_events (mission_id, version, state, recorded_at, source)
                VALUES (?, 1, 'created', ?, 'request')''', (mission_id, now))
            return dict(self._row(conn, mission_id)), True

    def start(self, mission_id, *, include_changed=False):
        """Reserve the only mock execution slot. / 유일한 모의 실행 슬롯을 점유한다."""
        with self._transaction() as conn:
            row = self._row(conn, mission_id)
            if row['state'] in ('queued', 'running'):
                return (dict(row), False) if include_changed else dict(row)
            validate_transition(row['state'], 'queued')
            updated = conn.execute('UPDATE mission_execution_slot SET mission_id = ? WHERE id = 1 AND mission_id IS NULL', (mission_id,))
            if updated.rowcount != 1:
                raise ContractError('mission_busy')
            result = dict(self._transition(conn, row, 'queued'))
            return (result, True) if include_changed else result

    def cancel(self, mission_id, *, include_changed=False):
        """Request cancellation without assuming a running task stopped.

        한글: 실행 중 작업의 정지를 가정하지 않고 취소를 요청한다.
        """
        with self._transaction() as conn:
            row = self._row(conn, mission_id)
            if row['state'] == 'cancel_requested':
                return (dict(row), False) if include_changed else dict(row)
            target = 'canceled' if row['state'] == 'created' else 'cancel_requested'
            result = dict(self._transition(conn, row, target, reason='user_requested'))
            return (result, True) if include_changed else result

    def step(self, mission_id, expected_version, outcome='success'):
        """Advance one mock step if its version is current. / 현재 버전의 모의 작업을 한 단계 진행한다."""
        if outcome not in ('success', 'failure', 'timeout'):
            raise ContractError('invalid_outcome')
        with self._transaction() as conn:
            row = self._row(conn, mission_id)
            if row['mode'] != 'simulation':
                raise ContractError('mode_unavailable')
            if row['version'] != expected_version:
                raise ContractError('stale_result')
            if row['state'] == 'cancel_requested':
                return dict(self._transition(conn, row, 'canceled', reason='simulation_cancel_ack', source='simulator'))
            if row['state'] == 'queued':
                return dict(self._transition(conn, row, 'running', stage='simulated_inspection', source='simulator'))
            if row['state'] != 'running':
                raise ContractError('invalid_transition')
            if outcome == 'success':
                return dict(self._transition(conn, row, 'succeeded', result={'simulated': True}, source='simulator'))
            return dict(self._transition(conn, row, 'failed', reason=f'simulation_{outcome}', source='simulator'))

    def list_recent(self, limit=50, offset=0, before=None):
        """Read recent mock missions. / 최근 모의 임무를 조회한다."""
        if not 1 <= limit <= 101 or not 0 <= offset <= 100000:
            raise ContractError('invalid_request')
        with self._transaction() as conn:
            if before:
                return [dict(row) for row in conn.execute('SELECT * FROM missions WHERE (created_at < ? OR (created_at = ? AND id < ?)) ORDER BY created_at DESC, id DESC LIMIT ?', (before[0], before[0], before[1], limit))]
            return [dict(row) for row in conn.execute('SELECT * FROM missions ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?', (limit, offset))]

    def advance_active(self):
        """Advance the active mock task once. / 진행 중인 모의 작업을 한 단계 진행한다."""
        with self._transaction() as conn:
            row = conn.execute('SELECT m.* FROM missions m JOIN mission_execution_slot s ON s.mission_id = m.id WHERE s.id = 1').fetchone()
            if row is None:
                return None
            if row['mode'] != 'simulation':
                return None
            mission_id, version = row['id'], row['version']
        try:
            return self.step(mission_id, version)
        except ContractError as exc:
            if exc.code in ('stale_result', 'invalid_transition'):
                return None
            raise

    def active_gazebo(self):
        """Read the active Gazebo task, if any. / 활성 Gazebo 임무를 조회한다."""
        with self._transaction() as conn:
            row = conn.execute("SELECT m.* FROM missions m JOIN mission_execution_slot s ON s.mission_id=m.id WHERE s.id=1 AND m.mode='gazebo'").fetchone()
            return dict(row) if row else None

    def begin_gazebo(self, mission_id, version, *, preparing=False):
        """Record Gazebo startup before launching the child. / 하위 실행 전에 Gazebo 시작을 기록한다."""
        with self._transaction() as conn:
            row = self._row(conn, mission_id)
            if row['mode'] != 'gazebo' or row['version'] != version or row['state'] != 'queued':
                raise ContractError('stale_result')
            return dict(self._transition(conn, row, 'running', stage='gazebo_preparing' if preparing else 'gazebo_navigation', source='gazebo'))

    def mark_gazebo_navigation(self, mission_id):
        """Record completed Gazebo preparation. / Gazebo 준비 완료를 기록한다."""
        with self._transaction() as conn:
            row = self._row(conn, mission_id)
            if row['mode'] != 'gazebo' or row['state'] != 'running' or row['stage'] != 'gazebo_preparing':
                return
            version = row['version'] + 1
            conn.execute('UPDATE missions SET stage=?, version=? WHERE id=?', ('gazebo_navigation', version, mission_id))
            conn.execute('''INSERT INTO mission_events (mission_id, version, previous_state, state, stage, recorded_at, source)
                            VALUES (?, ?, 'running', 'running', 'gazebo_navigation', ?, 'gazebo')''',
                         (mission_id, version, utc_now()))

    def mark_gazebo_inspection(self, mission_id):
        """Record the confirmed inspection stage once. / 확인된 점검 단계 진입을 한 번 기록한다."""
        with self._transaction() as conn:
            row = self._row(conn, mission_id)
            if row['mode'] != 'gazebo' or row['kind'] != 'inspect_stack_light' or row['state'] != 'running':
                return
            if row['stage'] != 'gazebo_navigation':
                return
            version = row['version'] + 1
            conn.execute('UPDATE missions SET stage=?, version=? WHERE id=?', ('gazebo_inspection', version, mission_id))
            conn.execute('''INSERT INTO mission_events (mission_id, version, previous_state, state, stage, recorded_at, source)
                            VALUES (?, ?, 'running', 'running', 'gazebo_inspection', ?, 'gazebo')''',
                         (mission_id, version, utc_now()))

    def finish_gazebo(self, mission_id, outcome, reason, colors=None):
        """Record a confirmed Gazebo result or interruption. / Gazebo 결과 또는 확인 불가 중단을 기록한다."""
        if outcome not in ('succeeded', 'failed', 'canceled', 'interrupted'):
            raise ContractError('invalid_outcome')
        with self._transaction() as conn:
            row = self._row(conn, mission_id)
            if row['mode'] != 'gazebo' or row['state'] not in ('running', 'cancel_requested'):
                raise ContractError('stale_result')
            if outcome == 'canceled' and row['state'] != 'cancel_requested':
                outcome, reason = 'interrupted', 'unexpected_cancellation'
            if row['kind'] == 'inspect_stack_light' and outcome == 'succeeded' and (
                    reason != 'inspection_observed' or not valid_inspection_result(colors)):
                outcome, reason = 'interrupted', 'inspection_result_unconfirmed'
            result = {'source': 'gazebo', 'simulated': True} if outcome == 'succeeded' else None
            if result is not None and row['kind'] == 'inspect_stack_light':
                result['colors'] = colors
            return dict(self._transition(conn, row, outcome, stage=row['stage'], reason=reason, result=result, source='gazebo'))

    def get(self, mission_id):
        """Read a mission. / 임무를 조회한다."""
        with self._transaction() as conn:
            return dict(self._row(conn, mission_id))

    def events(self, mission_id):
        """Read ordered mission events. / 임무 이력을 순서대로 조회한다."""
        with self._transaction() as conn:
            self._row(conn, mission_id)
            return [dict(row) for row in conn.execute('SELECT * FROM mission_events WHERE mission_id = ? ORDER BY version', (mission_id,))]

    def close(self):
        """Release ownership without changing persisted state. / 저장 상태를 바꾸지 않고 소유권을 반환한다."""
        with self._mutex:
            if not self._closed:
                self._closed = True
                fcntl.flock(self._lock.fileno(), fcntl.LOCK_UN)
                self._lock.close()
