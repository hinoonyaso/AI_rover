"""Local read-only operations dashboard and bounded metrics recording.

한글: 로컬 읽기 전용 관제 화면과 시스템 지표 기록을 제공한다.
"""
import asyncio
import json
import math
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
import stat
import sqlite3
import pymysql

from mission_contract import ContractError
from mission_mysql import MySQLMissionManager
from gazebo_worker import GazeboWorker
from mission_routes import router as mission_router
from calibration_routes import router as calibration_router
from sensor_services import router as sensor_services_router
from knowledge_routes import router as knowledge_router
from page_cursor import decode_cursor, encode_cursor
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from access_control import access_guard, login, logout, change_password, session_role
import psutil
from sqlalchemy import create_engine, text

ROOT = Path.home() / '.local/share/jetinspect-ops'
SOCKET = ROOT / 'mysql-run/mysql.sock'
DIST = Path(__file__).resolve().parents[1] / 'frontend/dist'
# The server has no network listener; the private Unix socket controls DB access.
# 한글: DB 네트워크 포트는 열지 않으며 사용자 전용 유닉스 소켓으로 접근을 제한한다.
DB_URL = f'mysql+pymysql://root@localhost/jetinspect?unix_socket={SOCKET}&connect_timeout=2'
engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300)


def metrics():
    """Read host resource usage; unavailable values remain null. / 호스트 자원을 읽고 미확인 값은 null로 둔다."""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(Path.home()))
    temperatures = []
    try:
        temperatures = [x.current for entries in psutil.sensors_temperatures().values() for x in entries if x.current is not None]
    except (AttributeError, OSError):
        pass
    return {'timestamp': datetime.now(timezone.utc).isoformat(), 'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': memory.percent, 'memory_used_gb': round(memory.used / 1024**3, 2),
            'memory_total_gb': round(memory.total / 1024**3, 2), 'disk_percent': disk.percent,
            'disk_free_gb': round(disk.free / 1024**3, 1),
            'temperature_c': max(temperatures) if temperatures else None}


def db_status():
    """Check the database without exposing connection details. / 연결 정보를 노출하지 않고 DB 상태를 확인한다."""
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        return 'connected'
    except Exception:
        return 'unavailable'


def record_sample():
    """Persist one resource sample, returning false when DB is unavailable.

    한글: 자원 지표 한 건을 저장하고 DB 오류 시 false를 반환한다.
    """
    data = metrics()
    try:
        with engine.begin() as conn:
            conn.execute(text('DELETE FROM system_metrics WHERE recorded_at < NOW() - INTERVAL 7 DAY'))
            conn.execute(text('INSERT INTO system_metrics (cpu_percent, memory_percent, disk_percent, temperature_c) VALUES (:cpu_percent, :memory_percent, :disk_percent, :temperature_c)'), data)
        return True
    except Exception:
        return False


def record_start():
    """Record a dashboard start event when the database is ready.

    한글: DB가 준비된 경우 관제 서버 시작 이벤트를 저장한다.
    """
    try:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO robot_events (severity, source, message) VALUES ('info', 'dashboard', 'dashboard started')"))
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app):
    """Run the low-rate recorder with the application lifecycle. / 앱 실행 중 저빈도 기록기를 유지한다."""
    async def loop():
        while True:
            await asyncio.to_thread(record_sample)
            await asyncio.sleep(60)
    await asyncio.to_thread(record_start)
    app.state.mission_manager = None
    directory = Path('/tmp') / f'jetinspect-mission-{os.getuid()}'
    try:
        directory.mkdir(mode=0o700, exist_ok=True)
        info = directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise OSError('invalid simulation directory')
        app.state.mission_manager = await asyncio.to_thread(MySQLMissionManager, SOCKET, legacy_path=directory / 'missions.sqlite3')
    except (OSError, ValueError, ContractError, sqlite3.Error, pymysql.Error):
        pass

    gazebo = GazeboWorker(app.state.mission_manager) if app.state.mission_manager is not None else None

    async def simulate():
        nonlocal gazebo
        while True:
            await asyncio.sleep(3)
            if app.state.mission_manager is None:
                try:
                    app.state.mission_manager = await asyncio.to_thread(MySQLMissionManager, SOCKET, legacy_path=directory / 'missions.sqlite3')
                    gazebo = GazeboWorker(app.state.mission_manager)
                except (OSError, ValueError, ContractError, sqlite3.Error, pymysql.Error):
                    continue
            if app.state.mission_manager is not None:
                try:
                    await asyncio.to_thread(app.state.mission_manager.advance_active)
                    await asyncio.to_thread(gazebo.tick)
                except (sqlite3.Error, pymysql.Error, ContractError):
                    # An active simulation must not continue unobserved when storage fails.
                    # 한글: 저장소 장애로 상태를 확인할 수 없으면 진행 중인 시뮬레이션에 취소를 요청한다.
                    await asyncio.to_thread(gazebo.close)
                    await asyncio.to_thread(app.state.mission_manager.close)
                    app.state.mission_manager = None
                    gazebo = None

    task = asyncio.create_task(loop())
    simulation_task = asyncio.create_task(simulate())
    yield
    simulation_task.cancel()
    try:
        await simulation_task
    except asyncio.CancelledError:
        pass
    if gazebo is not None:
        await asyncio.to_thread(gazebo.close)
    if app.state.mission_manager is not None:
        await asyncio.to_thread(app.state.mission_manager.close)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    engine.dispose()


app = FastAPI(title='JetInspect-M Operations', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.middleware('http')(access_guard)


@app.get('/api/session')
def current_session(request: Request):
    """Report the current session role. / 현재 세션 권한을 반환한다."""
    role = session_role(request)
    return JSONResponse({'role': role}, status_code=200 if role else 401)


app.add_api_route('/api/session/login', login, methods=['POST'])
app.add_api_route('/api/session/logout', logout, methods=['POST'])
app.add_api_route('/api/session/password', change_password, methods=['POST'])
app.include_router(mission_router)
app.include_router(calibration_router)
app.include_router(sensor_services_router)
app.include_router(knowledge_router)


import battery_settings


def ros_status():
    """Read fresh snapshots and validate each observation. / 최신 스냅샷과 개별 측정의 유효 시간을 확인한다."""
    try:
        data = json.loads((ROOT / 'run/ros-status.json').read_text())
        now = time.time()
        snapshot_at = data['timestamp']
        if not isinstance(snapshot_at, (int, float)) or not math.isfinite(snapshot_at) or not 0 <= now - snapshot_at < 8:
            raise ValueError('stale')

        def observation_age(stamp):
            # Recheck at API time: a fresh snapshot may contain an expired reading.
            # 한글: 최신 스냅샷에도 만료된 측정이 있을 수 있어 API 조회 시 재검사한다.
            if isinstance(stamp, (int, float)) and math.isfinite(stamp) and 0 <= now - stamp < 10 and stamp <= snapshot_at:
                return round(now - stamp, 1)
            return None

        battery_at = data.get('battery_received_at')
        battery_age = observation_age(battery_at)
        voltage = data.get('battery_voltage')
        if not isinstance(voltage, (int, float)) or not math.isfinite(voltage) or voltage <= 0:
            battery_age = None
        streams = {}
        for name in ('imu', 'scan', 'camera'):
            sample = data.get('streams', {}).get(name, {})
            stamp = sample.get('received_at')
            age = observation_age(stamp)
            hz = sample.get('hz')
            streams[name] = {'hz': hz if age is not None and isinstance(hz, (int, float)) and math.isfinite(hz) and hz >= 0 else None,
                             'age_seconds': age, 'received_at': stamp if age is not None else None}
        return {'status': 'monitoring', 'snapshot_at': snapshot_at, 'snapshot_age_seconds': now - snapshot_at,
                'battery_voltage': voltage if battery_age is not None else None,
                'battery_display_calibrated_v': battery_settings.corrected(ROOT / 'calibration/battery-active.json', voltage) if battery_age is not None else None,
                'battery_received_at': battery_at if battery_age is not None else None,
                'battery_age_seconds': battery_age, 'streams': streams, 'mission': None}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {'status': 'monitor_unavailable', 'snapshot_at': None, 'snapshot_age_seconds': None, 'battery_voltage': None,
                'battery_received_at': None, 'battery_age_seconds': None, 'streams': {}, 'mission': None}


@app.get('/api/status')
def status():
    """Report measured host status and explicitly unknown robot data. / 측정값과 미연결 로봇 상태를 표시한다."""
    return {'host': metrics(), 'database': db_status(), 'robot': ros_status(),
            'capabilities': {'robot_control': False, 'ros_bridge': 'read_only'}}


@app.get('/api/camera/preview')
def camera_preview():
    """Return only a recent local preview. / 최신 로컬 카메라 미리보기만 반환한다."""
    path = ROOT / 'run/camera-preview.jpg'
    try:
        modified_age = time.time() - path.stat().st_mtime
        if not 0 <= modified_age < 5 or ros_status()['status'] != 'monitoring':
            raise ValueError('stale preview')
        return FileResponse(path, media_type='image/jpeg', headers={'Cache-Control': 'no-store'})
    except (OSError, ValueError):
        raise HTTPException(status_code=503, detail='Camera preview unavailable') from None


@app.get('/api/gazebo/pose')
def gazebo_pose():
    """Return only a fresh isolated simulation pose. / 최신 격리 시뮬레이션 위치만 반환한다."""
    try:
        data = json.loads((ROOT / 'run/gazebo-pose.json').read_text())
        if (data['source'] != 'gazebo' or data['frame'] != 'map' or
                not 0 <= time.time() - data['timestamp'] < 5 or
                not all(isinstance(data[k], (int, float)) and math.isfinite(data[k]) for k in ('x', 'y', 'yaw'))):
            raise ValueError('invalid pose')
        return data
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(status_code=503, detail='Gazebo pose unavailable') from None


@app.get('/api/metrics')
def history():
    """Return the newest 120 samples or an explicit unavailable status. / 최근 120개 지표나 DB 오류를 반환한다."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(text('SELECT recorded_at, cpu_percent, memory_percent, disk_percent, temperature_c FROM system_metrics ORDER BY id DESC LIMIT 120')).mappings().all()
        return {'database': 'connected', 'samples': [dict(row) for row in rows]}
    except Exception:
        return {'database': 'unavailable', 'samples': []}


@app.get('/api/events')
def events():
    """Return recent operational events. / 최근 운영 이벤트를 반환한다."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(text('SELECT recorded_at, severity, source, message FROM robot_events ORDER BY id DESC LIMIT 50')).mappings().all()
        return {'database': 'connected', 'events': [dict(row) for row in rows]}
    except Exception:
        return {'database': 'unavailable', 'events': []}


# Only reviewed table names become SQL identifiers; no user input is interpolated.
# 한글: 검토한 테이블 이름만 SQL 식별자로 사용하며 사용자 입력을 직접 삽입하지 않는다.
DATABASE_TABLES = {
    'system_metrics': ('id', 'recorded_at', 'cpu_percent', 'memory_percent', 'disk_percent', 'temperature_c'),
    'robot_events': ('id', 'recorded_at', 'severity', 'source', 'message'),
    'missions': ('id', 'mode', 'kind', 'state', 'stage', 'created_at', 'finished_at', 'result', 'reason'),
    'mission_events': ('mission_id', 'version', 'previous_state', 'state', 'stage', 'recorded_at', 'source', 'reason'),
}


@app.get('/api/database/tables')
def database_tables():
    """List the explicitly supported read-only tables. / 조회를 허용한 읽기 전용 테이블을 나열한다."""
    return {'database': 'jetinspect', 'tables': [{'name': name, 'columns': columns} for name, columns in DATABASE_TABLES.items()]}


@app.get('/api/database/tables/{table_name}/rows')
def database_rows(table_name: str, before: int | None = Query(default=None, ge=1), limit: int = Query(default=50, ge=1, le=100),
                  offset: int = Query(default=0, ge=0, le=100000), cursor: str | None = Query(default=None, max_length=256)):
    """Read a bounded page ordered by ID. / ID 역순으로 제한된 페이지를 조회한다."""
    if table_name not in DATABASE_TABLES:
        raise HTTPException(status_code=404, detail='Unknown table')
    columns = DATABASE_TABLES[table_name]
    # Identifiers are taken exclusively from the fixed allowlist above.
    # 한글: 식별자는 위 고정 허용 목록에서만 가져온다.
    query = f"SELECT {', '.join(columns)} FROM {table_name}"
    mission_table = table_name in ('missions', 'mission_events')
    # Direct unit calls may omit FastAPI's injected query default.
    # 한글: 단위 시험에서 직접 호출하면 FastAPI의 기본값 주입이 생략된다.
    if not isinstance(cursor, str):
        cursor = None
    try:
        key = decode_cursor(cursor, event=table_name == 'mission_events') if cursor else None
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid cursor') from None
    if key and not mission_table:
        raise HTTPException(status_code=400, detail='Unsupported cursor')
    if before is not None and mission_table:
        raise HTTPException(status_code=400, detail='Unsupported cursor')
    if before is not None:
        query += ' WHERE id < :before'
    if mission_table:
        if key and table_name == 'missions':
            query += ' WHERE (created_at < :stamp OR (created_at = :stamp AND id < :key_id))'
        elif key:
            query += ' WHERE (recorded_at < :stamp OR (recorded_at = :stamp AND (mission_id < :key_id OR (mission_id = :key_id AND version < :version))))'
        query += (' ORDER BY created_at DESC, id DESC' if table_name == 'missions'
                  else ' ORDER BY recorded_at DESC, mission_id DESC, version DESC')
        query += ' LIMIT :limit' + ('' if key else ' OFFSET :offset')
    else:
        query += ' ORDER BY id DESC LIMIT :limit'
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(query), {'before': before, 'offset': offset, 'limit': limit + 1,
                                             'stamp': key[0] if key else None, 'key_id': key[1] if key else None,
                                             'version': key[2] if key and len(key) == 3 else None}).mappings().all()
        has_more = len(rows) > limit
        rows = [dict(row) for row in rows[:limit]]
        next_cursor = None
        if mission_table and has_more and rows:
            last = rows[-1]
            next_cursor = encode_cursor([last['created_at'], last['id']] if table_name == 'missions' else
                                        [last['recorded_at'], last['mission_id'], last['version']])
        return {'table': table_name, 'columns': columns, 'rows': rows, 'next_cursor': next_cursor,
                'next_before': rows[-1]['id'] if has_more and rows and not mission_table else None,
                'next_offset': offset + limit if mission_table and has_more else None}
    except Exception:
        raise HTTPException(status_code=503, detail='Database unavailable') from None


if DIST.is_dir():
    app.mount('/', StaticFiles(directory=DIST, html=True), name='dashboard')
