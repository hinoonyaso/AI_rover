"""Test Gazebo start-pose checks without ROS. / ROS 없이 Gazebo 시작 자세 검사를 시험한다."""
import json
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gazebo_nav_trial import verify_gazebo_pose


def message(x, y, yaw):
    return json.dumps({'pose': [{'name': 'jetrover', 'position': {'x': x, 'y': y},
                                  'orientation': {'z': math.sin(yaw / 2), 'w': math.cos(yaw / 2)}}]})


class PoseTests(unittest.TestCase):
    def test_start_and_resume_checks(self):
        with patch('gazebo_nav_trial.subprocess.run', return_value=SimpleNamespace(stdout=message(1.02, .37, 1.45))):
            verify_gazebo_pose()
            with self.assertRaisesRegex(RuntimeError, 'gazebo_start_pose_mismatch'):
                verify_gazebo_pose(True)
        with patch('gazebo_nav_trial.subprocess.run', return_value=SimpleNamespace(stdout=message(.84, 1.48, 0))):
            verify_gazebo_pose(True)
            with self.assertRaisesRegex(RuntimeError, 'gazebo_start_pose_mismatch'):
                verify_gazebo_pose()

    def test_unavailable_pose_fails_closed(self):
        with patch('gazebo_nav_trial.subprocess.run', return_value=SimpleNamespace(stdout='{}')):
            with self.assertRaisesRegex(RuntimeError, 'gazebo_pose_unavailable'):
                verify_gazebo_pose()


if __name__ == '__main__':
    unittest.main()
