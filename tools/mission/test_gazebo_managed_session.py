"""Check isolated startup guard behavior. / 격리 기동 보호 조건을 확인한다."""
from contextlib import redirect_stdout
import io
import os
from types import SimpleNamespace
import unittest
import tempfile
from pathlib import Path
import yaml
from unittest.mock import patch

import gazebo_managed_session as session


class ManagedSessionTests(unittest.TestCase):
    def test_inspection_uses_isolated_camera_pose_tolerance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = session.inspection_nav_params(Path(tmp))
            config = yaml.safe_load(path.read_text())
            goal = config['controller_server']['ros__parameters']['general_goal_checker']
            self.assertEqual(goal['xy_goal_tolerance'], 0.03)
            self.assertEqual(goal['yaw_goal_tolerance'], 0.08)
            original = yaml.safe_load((session.ROOT / 'tools/nav/ab_params/nav2_params_mppi.yaml').read_text())
            original_goal = original['controller_server']['ros__parameters']['general_goal_checker']
            self.assertEqual(original_goal['xy_goal_tolerance'], 0.1)
            self.assertEqual(original_goal['yaw_goal_tolerance'], 0.4)

    def test_existing_simulator_is_not_started_or_stopped(self):
        output = io.StringIO()
        with patch.dict(os.environ, {'GZ_PARTITION': 'jetinspect_dashboard_test'}), \
                patch.object(session, 'require_simulation'), patch.object(session.signal, 'signal'), \
                patch.object(session.subprocess, 'run', return_value=SimpleNamespace(stdout='/controller_manager\n')), \
                patch.object(session.subprocess, 'Popen') as spawn, \
                patch.object(session.sys, 'argv', ['gazebo_managed_session.py', 'inspect_stack_light']), \
                redirect_stdout(output):
            session.main()
        spawn.assert_not_called()
        self.assertIn('gazebo_environment_busy', output.getvalue())


if __name__ == '__main__':
    unittest.main()
