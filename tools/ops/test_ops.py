"""Check status handling without robot or database access.

한글: 로봇이나 DB 접근 없이 상태 처리 경로를 검증한다.
"""
import importlib.util
import json
import tempfile
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
spec = importlib.util.spec_from_file_location('ops_app', Path(__file__).parent / 'backend/app.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OperationsTests(unittest.TestCase):
    def test_simulation_clock_reset_requires_new_advancement(self):
        from gazebo_pose_monitor import track_clock
        old, seen = track_clock(100, 10.0, 5, 11.0)
        self.assertEqual((old, seen), (5, 0.0))
        self.assertEqual(track_clock(old, seen, 6, 12.0), (6, 12.0))

    def test_gazebo_pose_rejects_stale_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(module, 'ROOT', Path(tmp)), patch.object(module.time, 'time', return_value=100.0):
            run = Path(tmp) / 'run'
            run.mkdir()
            path = run / 'gazebo-pose.json'
            data = {'timestamp': 99.0, 'source': 'gazebo', 'frame': 'map', 'x': 1.0, 'y': 0.5, 'yaw': 0.1}
            path.write_text(json.dumps(data))
            self.assertEqual(module.gazebo_pose()['x'], 1.0)
            for field, value in (('timestamp', 95.0), ('x', float('nan')), ('source', 'robot')):
                invalid = dict(data, **{field: value})
                path.write_text(json.dumps(invalid))
                with self.assertRaises(HTTPException):
                    module.gazebo_pose()

    def test_status_exposes_disconnected_robot(self):
        with patch.object(module, 'db_status', return_value='unavailable'), patch.object(module, 'ros_status', return_value={'status': 'monitor_unavailable'}):
            result = module.status()
        self.assertEqual(result['database'], 'unavailable')
        self.assertEqual(result['robot']['status'], 'monitor_unavailable')
        self.assertFalse(result['capabilities']['robot_control'])
        self.assertIn('memory_percent', result['host'])

    def test_sensor_freshness_and_missing_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(module, 'ROOT', Path(tmp)), patch.object(module.time, 'time', return_value=100.0):
            run = Path(tmp) / 'run'
            run.mkdir()
            snapshot = {'timestamp': 99.0, 'battery_voltage': 12.3, 'battery_received_at': 94.0,
                        'streams': {'imu': {'hz': 10.0, 'received_at': 98.0},
                                    'scan': {'hz': 5.0, 'received_at': 90.0},
                                    'camera': {'hz': None, 'received_at': 99.0}}}
            path = run / 'ros-status.json'
            path.write_text(json.dumps(snapshot))
            result = module.ros_status()
            self.assertEqual(result['battery_age_seconds'], 6.0)
            self.assertEqual(result['streams']['imu']['hz'], 10.0)
            self.assertIsNone(result['streams']['scan']['age_seconds'])
            self.assertEqual(result['streams']['camera']['age_seconds'], 1.0)
            self.assertIsNone(result['streams']['camera']['hz'])
            snapshot['battery_received_at'] = 101.0
            snapshot['streams']['imu'].pop('received_at')
            path.write_text(json.dumps(snapshot))
            result = module.ros_status()
            self.assertIsNone(result['battery_voltage'])
            self.assertIsNone(result['streams']['imu']['hz'])
            snapshot['timestamp'] = 92.0
            path.write_text(json.dumps(snapshot))
            self.assertEqual(module.ros_status()['status'], 'monitor_unavailable')

    def test_battery_display_correction_never_replaces_raw_voltage(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(module, 'ROOT', Path(tmp)), patch.object(module.time, 'time', return_value=100.):
            root=Path(tmp);(root/'run').mkdir();(root/'calibration').mkdir()
            (root/'calibration/battery-active.json').write_text(json.dumps({'slope':1.,'intercept_v':.2,'sensor_min_v':10.,'sensor_max_v':12.}))
            (root/'run/ros-status.json').write_text(json.dumps({'timestamp':99.,'battery_received_at':98.,'battery_voltage':11.,'streams':{}}))
            result=module.ros_status()
            self.assertEqual(result['battery_voltage'],11.)
            self.assertAlmostEqual(result['battery_display_calibrated_v'],11.2)
            (root/'run/ros-status.json').write_text(json.dumps({'timestamp':99.,'battery_received_at':98.,'battery_voltage':13.,'streams':{}}))
            result=module.ros_status()
            self.assertEqual(result['battery_voltage'],13.)
            self.assertIsNone(result['battery_display_calibrated_v'])

    def test_database_browser_pagination_and_allowlist(self):
        engine = create_engine('sqlite:///:memory:')
        with engine.begin() as conn:
            conn.execute(text('CREATE TABLE robot_events (id INTEGER PRIMARY KEY, recorded_at TEXT, severity TEXT, source TEXT, message TEXT)'))
            for identifier in range(1, 5):
                conn.execute(text("INSERT INTO robot_events VALUES (:id, 'time', 'info', 'test', 'message')"), {'id': identifier})
        with patch.object(module, 'engine', engine):
            first = module.database_rows('robot_events', before=None, limit=2)
            self.assertEqual([row['id'] for row in first['rows']], [4, 3])
            self.assertEqual(first['next_before'], 3)
            second = module.database_rows('robot_events', before=3, limit=2)
            self.assertEqual([row['id'] for row in second['rows']], [2, 1])
            self.assertIsNone(second['next_before'])
            with self.assertRaises(HTTPException) as unknown:
                module.database_rows('robot_events; DROP TABLE robot_events', before=None, limit=2)
            self.assertEqual(unknown.exception.status_code, 404)
        engine.dispose()

    def test_database_browser_hides_connection_error(self):
        with patch.object(module.engine, 'connect', side_effect=OSError('private detail')):
            with self.assertRaises(HTTPException) as failure:
                module.database_rows('robot_events', before=None, limit=50)
        self.assertEqual(failure.exception.status_code, 503)
        self.assertNotIn('private detail', failure.exception.detail)

    def test_mission_event_browser_pages(self):
        engine = create_engine('sqlite:///:memory:')
        with engine.begin() as conn:
            conn.execute(text('CREATE TABLE mission_events (mission_id TEXT, version INTEGER, previous_state TEXT, state TEXT, stage TEXT, recorded_at TEXT, source TEXT, reason TEXT)'))
            for version in range(1, 4):
                conn.execute(text("INSERT INTO mission_events VALUES ('00000000-0000-4000-8000-000000000001', :v, NULL, 'running', NULL, 'time', 'test', NULL)"), {'v': version})
        with patch.object(module, 'engine', engine):
            first = module.database_rows('mission_events', before=None, limit=2, offset=0, cursor=None)
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO mission_events VALUES ('00000000-0000-4000-8000-000000000001', 4, NULL, 'running', NULL, 'time', 'test', NULL)"))
            second = module.database_rows('mission_events', before=None, limit=2, offset=0, cursor=first['next_cursor'])
            self.assertEqual([row['version'] for row in first['rows']], [3, 2])
            self.assertEqual([row['version'] for row in second['rows']], [1])
            self.assertIsNone(second['next_cursor'])
        engine.dispose()

    def test_camera_preview_requires_fresh_file_and_monitor(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(module, 'ROOT', Path(tmp)):
            run = Path(tmp) / 'run'
            run.mkdir()
            path = run / 'camera-preview.jpg'
            path.write_bytes(b'jpeg fixture')
            with patch.object(module, 'ros_status', return_value={'status': 'monitoring'}):
                self.assertEqual(module.camera_preview().path, path)
            with patch.object(module, 'ros_status', return_value={'status': 'monitor_unavailable'}):
                with self.assertRaises(HTTPException) as failure:
                    module.camera_preview()
                self.assertEqual(failure.exception.status_code, 503)
            with patch.object(module.time, 'time', return_value=path.stat().st_mtime + 5):
                with self.assertRaises(HTTPException):
                    module.camera_preview()

    def test_history_reports_database_failure(self):
        with patch.object(module.engine, 'connect', side_effect=OSError('private detail')):
            self.assertEqual(module.history(), {'database': 'unavailable', 'samples': []})

    def test_recorder_handles_database_failure(self):
        with patch.object(module.engine, 'begin', side_effect=OSError('private detail')):
            self.assertFalse(module.record_sample())


if __name__ == '__main__':
    unittest.main()
