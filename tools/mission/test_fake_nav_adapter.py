"""Exercise a fake ROS action server without robot or Gazebo.

한글: 로봇이나 Gazebo 없이 가짜 ROS Action 서버를 시험한다.
"""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

from fake_nav_adapter import require_isolated_environment, run_fake_navigation


class FakeNavigationTests(unittest.TestCase):
    def test_rejects_real_names_and_unsafe_environment(self):
        safe = {'ROS_DOMAIN_ID': '31', 'ROS_AUTOMATIC_DISCOVERY_RANGE': 'LOCALHOST', 'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp'}
        with patch.dict(os.environ, safe, clear=True):
            for name in ('/navigate_to_pose', '/mission_test_invalid/navigate_to_pose'):
                with self.assertRaises(ValueError):
                    require_isolated_environment(name)
            action = '/mission_test_' + uuid4().hex + '/navigate_to_pose'
            require_isolated_environment(action)
            with patch.dict(os.environ, {'ROS_DOMAIN_ID': '25'}):
                with self.assertRaises(RuntimeError):
                    require_isolated_environment(action)
            with patch.dict(os.environ, {'ROS_STATIC_PEERS': '192.0.2.1'}):
                with self.assertRaises(RuntimeError):
                    require_isolated_environment(action)

    def test_fake_action_outcomes(self):
        for behavior, expected in [('success', 'succeeded'), ('abort', 'failed'), ('reject', 'failed'), ('cancel', 'canceled'), ('unresponsive', 'unknown')]:
            with self.subTest(behavior=behavior):
                name = '/mission_test_' + uuid4().hex + '/navigate_to_pose'
                process = subprocess.Popen([sys.executable, str(Path(__file__).with_name('fake_nav_server.py')), name, behavior], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                try:
                    self.assertEqual(process.stdout.readline().strip(), 'ready')
                    result = run_fake_navigation(name, 1.0, 1.45, 0.0, available_timeout=4, result_timeout=.5, cancel_timeout=1)
                    self.assertEqual(result['state'], expected, result)
                finally:
                    process.terminate()
                    try:
                        process.communicate(timeout=4)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()

    def test_missing_server_is_unavailable(self):
        name = '/mission_test_' + uuid4().hex + '/navigate_to_pose'
        self.assertEqual(run_fake_navigation(name, 1.0, 1.45, 0, available_timeout=.3)['state'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
