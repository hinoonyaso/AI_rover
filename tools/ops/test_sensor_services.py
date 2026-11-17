"""Check camera ownership and command boundaries. / 카메라 소유 및 명령 경계를 확인한다."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from fastapi import HTTPException
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
import sensor_services as service

class SensorServicesTests(unittest.TestCase):
    def test_only_start_and_stop_are_allowed(self):
        with patch.object(service.subprocess, 'run') as run:
            with self.assertRaises(HTTPException): service.sensor_action('camera', 'restart;anything')
            run.assert_not_called()

    def test_refuses_existing_external_camera(self):
        with patch.object(service, 'status', return_value={'active':'inactive'}), \
             patch.object(service.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='/depth_cam/depth_cam\n')) as run:
            with self.assertRaises(HTTPException) as error: service.sensor_action('camera', 'start')
            self.assertEqual(error.exception.detail, 'camera_already_running')
            self.assertEqual(run.call_count, 1)

    def test_start_uses_fixed_unit_after_probe(self):
        with patch.object(service, 'status', return_value={'active':'inactive'}), \
             patch.object(service.subprocess, 'run', side_effect=[SimpleNamespace(returncode=0,stdout=''), SimpleNamespace(returncode=0)]) as run:
            service.sensor_action('camera', 'start')
            self.assertEqual(run.call_args_list[-1].args[0], ['systemctl','--user','start','jetinspect-camera.service'])

    def test_refuses_existing_base_process_before_ros_probe(self):
        with patch.object(service, 'status', return_value={'active':'inactive'}), \
             patch.object(service.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
            with self.assertRaises(HTTPException) as error: service.sensor_action('base', 'start')
            self.assertEqual(error.exception.detail, 'base_already_running')
            self.assertEqual(run.call_count, 1)

    def test_arm_observation_does_not_compete_with_existing_base(self):
        with patch.object(service, 'status', return_value={'active':'inactive'}), \
             patch.object(service.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
            with self.assertRaises(HTTPException) as error: service.sensor_action('arm', 'start')
            self.assertEqual(error.exception.detail, 'base_already_running')
            self.assertEqual(run.call_count, 1)

    def test_refuses_existing_robot_state_publisher(self):
        with patch.object(service, 'status', return_value={'active':'inactive'}), \
             patch.object(service.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='/robot_state_publisher\n')):
            with self.assertRaises(HTTPException) as error: service.sensor_action('tf', 'start')
            self.assertEqual(error.exception.detail, 'tf_already_running')

    def test_stop_never_targets_external_processes(self):
        with patch.object(service, 'status', return_value={'active':'inactive'}), \
             patch.object(service.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
            service.sensor_action('camera', 'stop')
            self.assertEqual(run.call_args.args[0], ['systemctl','--user','stop','jetinspect-camera.service'])

if __name__ == '__main__': unittest.main()
