"""Test Gazebo supervision with inert child processes. / 비활성 하위 프로세스로 Gazebo 감독을 시험한다."""
from pathlib import Path
import subprocess
import sqlite3
import json
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from gazebo_worker import GazeboWorker
from mission_contract import ContractError
from mission_simulator import SimulationManager


class GazeboWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/tmp')
        self.manager = SimulationManager(Path(self.tmp.name) / 'test.db')
        self.worker = GazeboWorker(self.manager, auto_start=False)

    def tearDown(self):
        self.worker.close()
        self.manager.close()
        self.tmp.cleanup()

    def create(self):
        return self.manager.create({'request_id': str(uuid4()), 'mode': 'gazebo', 'kind': 'navigate_demo', 'parameters': {}})[0]

    def test_launch_uses_isolated_udp_profile(self):
        with patch.dict(os.environ, {'ROS_STATIC_PEERS': '192.0.2.1',
                                     'FASTDDS_BUILTIN_TRANSPORTS': 'SHM'}), \
                patch('gazebo_worker.subprocess.Popen') as spawn:
            self.worker.kind = 'navigate_demo'
            self.worker._launch()
            env = spawn.call_args.kwargs['env']
            self.assertEqual(env['ROS_DOMAIN_ID'], '31')
            self.assertEqual(env['ROS_AUTOMATIC_DISCOVERY_RANGE'], 'SUBNET')
            self.assertEqual(env['GZ_IP'], '127.0.0.1')
            self.assertEqual(Path(env['FASTRTPS_DEFAULT_PROFILES_FILE']).name, 'fastdds-loopback.xml')
            self.assertNotIn('ROS_STATIC_PEERS', env)
            self.assertNotIn('FASTDDS_BUILTIN_TRANSPORTS', env)
            self.worker.output.close()
            self.worker.output = None
            self.worker.process = None

    def test_auto_launch_owns_unique_partition(self):
        self.worker.auto_start = True
        self.worker.kind = 'inspect_stack_light'
        with patch('gazebo_worker.subprocess.Popen') as spawn:
            self.worker._launch()
            args = spawn.call_args.args[0]
            env = spawn.call_args.kwargs['env']
            self.assertTrue(env['GZ_PARTITION'].startswith('jetinspect_dashboard_'))
            self.assertTrue(args[-2].endswith('gazebo_managed_session.py'))
            self.assertEqual(args[-1], 'inspect_stack_light')
            self.worker.output.close()
            self.worker.output = None
            self.worker.process = None

    def launch_dummy(self, output):
        self.worker.output = tempfile.TemporaryFile(mode='w+t', encoding='utf-8')
        self.worker.process = subprocess.Popen([sys.executable, '-c', 'print(' + repr(output) + ')'], stdin=subprocess.PIPE, stdout=self.worker.output, stderr=subprocess.STDOUT, text=True)

    def finish(self):
        self.worker.process.wait(timeout=5)
        self.worker.tick()

    def test_inspection_diagnostic_is_retained_in_service_log(self):
        item = self.create()
        self.manager.start(item['id'])
        self.worker._launch = lambda: self.launch_dummy(
            'INSPECTION_DIAGNOSTIC received=0 invalid_format=0\n'
            'MISSION_RESULT {"state":"failed","reason":"inspection_unconfirmed"}')
        self.worker.tick()
        with patch('builtins.print') as log:
            self.finish()
        self.assertTrue(any(item['id'] in str(call) and 'received=0' in str(call) for call in log.call_args_list))
        self.assertEqual(self.manager.get(item['id'])['reason'], 'inspection_unconfirmed')

    def test_gazebo_not_advanced_by_mock_worker(self):
        item = self.create()
        queued = self.manager.start(item['id'])
        self.assertIsNone(self.manager.advance_active())
        self.assertEqual(self.manager.get(item['id'])['state'], 'queued')
        with self.assertRaises(ContractError):
            self.manager.step(item['id'], queued['version'])

    def test_auto_preparation_and_navigation_stages(self):
        self.worker.auto_start = True
        item = self.create()
        self.manager.start(item['id'])
        self.worker._launch = lambda: self.launch_dummy('MISSION_STAGE gazebo_navigation\nMISSION_RESULT {"state":"succeeded","reason":"nav2_succeeded"}')
        self.worker.tick()
        self.assertEqual(self.manager.get(item['id'])['stage'], 'gazebo_preparing')
        self.finish()
        stages = [event['stage'] for event in self.manager.events(item['id'])]
        self.assertIn('gazebo_preparing', stages)
        self.assertIn('gazebo_navigation', stages)
        self.assertEqual(self.manager.get(item['id'])['state'], 'succeeded')

    def test_confirmed_success_and_missing_result(self):
        for output, state in [('MISSION_RESULT {"state":"succeeded","reason":"nav2_succeeded"}', 'succeeded'), ('unexpected exit', 'interrupted')]:
            item = self.create()
            self.manager.start(item['id'])
            self.worker._launch = lambda: self.launch_dummy(output)
            self.worker.tick()
            self.assertEqual(self.manager.get(item['id'])['state'], 'running')
            self.finish()
            self.assertEqual(self.manager.get(item['id'])['state'], state)

    def test_result_is_retained_until_database_recovers(self):
        item = self.create()
        self.manager.start(item['id'])
        self.worker._launch = lambda: self.launch_dummy('MISSION_RESULT {"state":"succeeded","reason":"nav2_succeeded"}')
        self.worker.tick()
        self.worker.process.wait(timeout=5)
        with patch.object(self.manager, 'finish_gazebo', side_effect=sqlite3.OperationalError('offline')):
            with self.assertRaises(sqlite3.OperationalError):
                self.worker.tick()
        self.assertIsNotNone(self.worker.pending_result)
        self.assertEqual(self.manager.get(item['id'])['state'], 'running')
        self.worker.tick()
        self.assertEqual(self.manager.get(item['id'])['state'], 'succeeded')
        self.assertIsNone(self.worker.pending_result)

    def test_canceled_before_launch(self):
        item = self.create()
        self.manager.start(item['id'])
        self.manager.cancel(item['id'])
        self.worker.tick()
        self.assertEqual(self.manager.get(item['id'])['state'], 'canceled')
        self.assertIsNone(self.worker.process)

    def test_running_cancel_waits_for_confirmed_child_result(self):
        item = self.create()
        self.manager.start(item['id'])
        def launch():
            self.worker.output = tempfile.TemporaryFile(mode='w+t', encoding='utf-8')
            code = 'import sys; sys.stdin.readline(); print(' + repr('MISSION_RESULT {"state":"canceled","reason":"cancel_confirmed"}') + ', flush=True)'
            self.worker.process = subprocess.Popen([sys.executable, '-c', code], stdin=subprocess.PIPE, stdout=self.worker.output, stderr=subprocess.STDOUT, text=True)
        self.worker._launch = launch
        self.worker.tick()
        pending = self.manager.cancel(item['id'])
        self.assertEqual(pending['state'], 'cancel_requested')
        self.worker.tick()
        self.worker.process.wait(timeout=5)
        self.worker.tick()
        self.assertEqual(self.manager.get(item['id'])['state'], 'canceled')

    def test_actual_robot_mode_remains_forbidden(self):
        with self.assertRaises(ContractError):
            self.manager.create({'request_id': str(uuid4()), 'mode': 'robot', 'kind': 'navigate_demo', 'parameters': {}})

    def test_inspection_success_requires_observed_colors(self):
        colors = {name: {'state': state, 'reason': None, 'samples': 7, 'duration_s': 2.2}
                  for name, state in [('red', 'on'), ('yellow', 'off'), ('green', 'blinking')]}
        for output, expected in [
                ({'state': 'succeeded', 'reason': 'nav2_succeeded'}, 'interrupted'),
                ({'state': 'succeeded', 'reason': 'inspection_observed', 'colors': colors}, 'succeeded'),
                ({'state': 'failed', 'reason': 'inspection_unconfirmed'}, 'failed')]:
            item = self.manager.create({'request_id': str(uuid4()), 'mode': 'gazebo',
                                        'kind': 'inspect_stack_light', 'parameters': {}})[0]
            self.manager.start(item['id'])
            self.worker._launch = lambda: self.launch_dummy('MISSION_RESULT ' + json.dumps(output))
            self.worker.tick()
            self.finish()
            item = self.manager.get(item['id'])
            self.assertEqual(item['state'], expected)
            if expected == 'succeeded':
                self.assertEqual(json.loads(item['result'])['colors'], colors)
            else:
                self.assertIsNone(item['result'])

    def test_inspection_stage_is_persisted_before_terminal_result(self):
        item = self.manager.create({'request_id': str(uuid4()), 'mode': 'gazebo',
                                    'kind': 'inspect_stack_light', 'parameters': {}})[0]
        self.manager.start(item['id'])
        self.worker._launch = lambda: self.launch_dummy(
            'MISSION_STAGE gazebo_inspection\nMISSION_RESULT {"state":"failed","reason":"inspection_unconfirmed"}')
        self.worker.tick()
        self.finish()
        events = self.manager.events(item['id'])
        self.assertEqual([event['stage'] for event in events[-3:]],
                         ['gazebo_navigation', 'gazebo_inspection', 'gazebo_inspection'])
        self.assertEqual([event['state'] for event in events[-3:]], ['running', 'running', 'failed'])

    def test_stage_does_not_reverse_cancel_request(self):
        item = self.manager.create({'request_id': str(uuid4()), 'mode': 'gazebo',
                                    'kind': 'inspect_stack_light', 'parameters': {}})[0]
        queued = self.manager.start(item['id'])
        self.manager.begin_gazebo(item['id'], queued['version'])
        self.manager.cancel(item['id'])
        self.manager.mark_gazebo_inspection(item['id'])
        self.assertEqual(self.manager.get(item['id'])['state'], 'cancel_requested')
        self.assertEqual(self.manager.get(item['id'])['stage'], None)

    def test_inspection_stage_is_retried_after_database_error(self):
        item = self.manager.create({'request_id': str(uuid4()), 'mode': 'gazebo',
                                    'kind': 'inspect_stack_light', 'parameters': {}})[0]
        self.manager.start(item['id'])
        self.worker._launch = lambda: self.launch_dummy(
            'MISSION_STAGE gazebo_inspection\nMISSION_RESULT {"state":"failed","reason":"inspection_unconfirmed"}')
        self.worker.tick()
        self.worker.process.wait(timeout=5)
        with patch.object(self.manager, 'mark_gazebo_inspection', side_effect=sqlite3.OperationalError('offline')):
            with self.assertRaises(sqlite3.OperationalError):
                self.worker.tick()
        self.worker.tick()
        self.assertIn('gazebo_inspection', [event['stage'] for event in self.manager.events(item['id'])])


if __name__ == '__main__':
    unittest.main()
