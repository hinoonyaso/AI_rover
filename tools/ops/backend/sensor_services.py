"""Manage only the dashboard-owned camera service.

한글: 대시보드 소유 카메라 서비스만 관리한다.
"""
import os
from pathlib import Path
import subprocess
import threading

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix='/api/sensor-services')
lock = threading.Lock()
SERVICES = {'camera': 'jetinspect-camera.service', 'base': 'jetinspect-base-sensors.service', 'arm': 'jetinspect-arm-observation.service', 'lidar': 'jetinspect-lidar.service', 'tf': 'jetinspect-robot-tf.service', 'rgbd': 'jetinspect-rgbd-reprojection.service'}


def status(kind='camera'):
    """Report service status without interpreting it as received video.

    한글: 서비스 상태만 보고하며 영상 수신과 구분한다.
    """
    try:
        result = subprocess.run(['systemctl', '--user', 'show', SERVICES[kind], '--property=LoadState,ActiveState,SubState', '--value'],
                                capture_output=True, text=True, timeout=5, check=True)
        values = result.stdout.splitlines()
        if len(values) != 3:
            raise ValueError('invalid status')
        return {'load': values[0], 'active': values[1], 'sub': values[2]}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {'load': 'unknown', 'active': 'unknown', 'sub': 'unknown'}


@router.get('')
def get_status():
    """Report the managed camera state. / 관리되는 카메라 상태를 반환한다."""
    return {'camera': status('camera'), 'base': status('base'), 'arm': status('arm'), 'lidar': status('lidar'), 'tf': status('tf'), 'rgbd': status('rgbd')}


@router.post('/{kind}/{action}')
def sensor_action(kind: str, action: str):
    """Start or stop only the fixed camera unit. / 고정된 카메라 서비스만 시작·중지한다."""
    if kind not in SERVICES or action not in ('start', 'stop'):
        raise HTTPException(400, 'invalid_action')
    with lock:
        if action == 'start' and status(kind)['active'] != 'active':
            if kind == 'rgbd':
                path = Path.home()/'.local/share/jetinspect-ops/calibration/rgbd-extrinsic-active.json'
                if path.is_symlink() or not path.is_file():raise HTTPException(409, 'rgbd_candidate_unavailable')
            if kind in ('base', 'arm'):
                try:
                    existing = subprocess.run(['pgrep', '-x', 'base_node'], capture_output=True, timeout=5)
                except (OSError, subprocess.SubprocessError):
                    raise HTTPException(503, 'ros_unavailable') from None
                if existing.returncode == 0:
                    raise HTTPException(409, 'base_already_running')
                if existing.returncode != 1:
                    raise HTTPException(503, 'ros_unavailable')
            # Refuse to compete with an existing camera driver in ROS domain 25.
            # 한글: ROS 도메인 25에 기존 카메라가 있으면 중복 실행하지 않는다.
            env = os.environ.copy()
            env['ROS_DOMAIN_ID'] = '25'
            for key in ('PYTHONPATH', 'ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER', 'FASTRTPS_DEFAULT_PROFILES_FILE',
                        'FASTDDS_DEFAULT_PROFILES_FILE', 'CYCLONEDDS_URI', 'ROS_LOCALHOST_ONLY',
                        'FASTDDS_BUILTIN_TRANSPORTS', 'ROS_AUTOMATIC_DISCOVERY_RANGE'):
                env.pop(key, None)
            try:
                probe = subprocess.run(['/bin/bash', '-c', 'source /opt/ros/jazzy/setup.bash && source "$1" && ros2 node list --no-daemon --spin-time 2',
                                        'camera-probe', str(Path.home() / 'jetrover_ws/install/setup.bash')],
                                       capture_output=True, text=True, timeout=10, env=env)
            except (OSError, subprocess.SubprocessError):
                raise HTTPException(503, 'ros_unavailable') from None
            if probe.returncode:
                raise HTTPException(503, 'ros_unavailable')
            nodes = probe.stdout.splitlines()
            existing = ('/jetinspect_rgbd_reproject' in nodes if kind == 'rgbd' else any(name.startswith('/depth_cam/') or name == '/depth_cam' for name in nodes) if kind == 'camera'
                        else '/base_node' in nodes if kind in ('base', 'arm') else '/robot_state_publisher' in nodes if kind == 'tf' else '/rplidar_composition' in nodes)
            if existing:
                raise HTTPException(409, f'{kind}_already_running')
        try:
            result = subprocess.run(['systemctl', '--user', action, SERVICES[kind]], capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            raise HTTPException(503, 'service_unavailable') from None
        if result.returncode:
            raise HTTPException(503, 'service_failed')
    return {kind: status(kind)}
