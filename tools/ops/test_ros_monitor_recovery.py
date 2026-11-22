"""Test recovery from interrupted ROS parameter requests.

한글: 중단된 ROS 파라미터 조회의 복구를 검증한다.
"""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from ros_monitor import SensorMonitor


class MappingRecoveryTests(unittest.TestCase):
    def test_expired_request_is_cancelled_and_retried(self):
        old = Mock()
        old.done.return_value = False
        new = Mock()
        client = Mock()
        client.services_are_ready.return_value = True
        client.get_parameters.return_value = new
        node = SimpleNamespace(arm_parameter_future=old, arm_parameter_started=10., arm_parameters=client,
                               arm_mapping={'joint3': 3}, arm_mapping_at=1., arm_offsets={'joint3': 0.},
                               arm_mapping_received=Mock())
        with patch('ros_monitor.time.monotonic', return_value=16.):
            SensorMonitor.request_arm_mapping(node)
        old.cancel.assert_called_once()
        self.assertIs(node.arm_parameter_future, new)
        self.assertEqual(node.arm_mapping, {})
        SensorMonitor.arm_mapping_received(node, old)
        old.result.assert_not_called()

    def test_pending_request_is_not_cancelled_early(self):
        future = Mock()
        future.done.return_value = False
        node = SimpleNamespace(arm_parameter_future=future, arm_parameter_started=10., arm_parameters=Mock())
        with patch('ros_monitor.time.monotonic', return_value=14.):
            SensorMonitor.request_arm_mapping(node)
        future.cancel.assert_not_called()
        node.arm_parameters.get_parameters.assert_not_called()


if __name__ == '__main__':
    unittest.main()
