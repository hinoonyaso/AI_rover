"""Bounded read-only sensor calibration workflows for the dashboard.

한글: 대시보드용 제한된 읽기 전용 센서 보정 작업이다.
"""
import atexit
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
from uuid import uuid4
from typing import Annotated, Literal

from calibration_catalog import calibration_catalog
from camera_info_status import fresh_camera_info
from arm_observation import fresh_arm_observation
import gyro_settings
import accel_settings
import camera_settings
import footprint_settings
import lidar_settings
import odom_settings
import joint_settings
import battery_settings
import tcp_settings
import hand_eye_settings
import gripper_settings
import rgbd_settings
import rgbd_extrinsic_settings
from wheel_observation import fresh_wheel_feedback
from odom_observation import fresh_odom, odom_displacement

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix='/api/calibration')
ROOT = Path.home() / '.local/share/jetinspect-ops'
PROJECT = Path(__file__).resolve().parents[3]
executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='sensor-calibration')
lock = threading.RLock()
state = {'running': None, 'error': None, 'imu': None, 'camera': None, 'captures': []}
spec = importlib.util.spec_from_file_location('imu_calibration_math', PROJECT / 'tools/imu_calibration/calibration_math.py')
imu_math = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imu_math)
capture_dir = Path(tempfile.mkdtemp(prefix='jetinspect-calibration-'))
atexit.register(shutil.rmtree, capture_dir, ignore_errors=True)


class Board(BaseModel):
    columns: int = Field(ge=3, le=20)
    rows: int = Field(ge=3, le=20)
    square_mm: float = Field(ge=1, le=500, allow_inf_nan=False)



class BatteryReference(BaseModel):
    reference_v: float = Field(ge=1, le=60, allow_inf_nan=False, strict=True)


class RegistrationApply(BaseModel):
    mode: Literal['OFF', 'HW_D2C', 'SW_D2C']
    config_hash: str = Field(min_length=64, max_length=64)
    candidate_hash: str = Field(min_length=64, max_length=64)


class DepthSourceSelection(BaseModel):
    source: Literal['default','corrected']
    background_id: str | None = Field(default=None, pattern=r'^[0-9a-f]{32}$')


class FootprintMeasurement(BaseModel):
    front_cm: float = Field(gt=0, le=300, allow_inf_nan=False, strict=True)
    rear_cm: float = Field(gt=0, le=300, allow_inf_nan=False, strict=True)
    left_cm: float = Field(gt=0, le=300, allow_inf_nan=False, strict=True)
    right_cm: float = Field(gt=0, le=300, allow_inf_nan=False, strict=True)



class LidarPositionMeasurement(BaseModel):
    x_cm: float = Field(ge=-300, le=300, allow_inf_nan=False, strict=True)
    y_cm: float = Field(ge=-300, le=300, allow_inf_nan=False, strict=True)
    z_cm: float = Field(ge=-300, le=300, allow_inf_nan=False, strict=True)


class LidarYawMeasurement(BaseModel):
    yaw_deg: float = Field(ge=-180, le=180, allow_inf_nan=False, strict=True)



class OdometryComparison(BaseModel):
    motion: Literal['forward', 'lateral', 'rotation']
    source: Literal['command', 'encoder', 'ekf']
    reference: float = Field(ge=-10000, le=10000, allow_inf_nan=False, strict=True)
    recorded: float = Field(ge=-10000, le=10000, allow_inf_nan=False, strict=True)



class WheelObservation(BaseModel):
    environment: Literal['simulation', 'physical']
    front_left: Literal['forward', 'backward', 'stopped', 'unknown']
    front_right: Literal['forward', 'backward', 'stopped', 'unknown']
    rear_left: Literal['forward', 'backward', 'stopped', 'unknown']
    rear_right: Literal['forward', 'backward', 'stopped', 'unknown']



class AlignmentPoint(BaseModel):
    color_x: float = Field(ge=0, le=10000, allow_inf_nan=False, strict=True)
    color_y: float = Field(ge=0, le=10000, allow_inf_nan=False, strict=True)
    depth_x: float = Field(ge=0, le=10000, allow_inf_nan=False, strict=True)
    depth_y: float = Field(ge=0, le=10000, allow_inf_nan=False, strict=True)


class AlignmentMeasurement(BaseModel):
    points: list[AlignmentPoint] = Field(min_length=3, max_length=10)
    pair_id: str | None = Field(default=None, pattern=r'^[0-9a-f]{32}$')



class JointReference(BaseModel):
    joint: Literal['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'r_joint']
    reference_rad: float = Field(ge=-6.3, le=6.3, allow_inf_nan=False, strict=True)



class Point3(BaseModel):
    x: float = Field(ge=-10, le=10, allow_inf_nan=False, strict=True)
    y: float = Field(ge=-10, le=10, allow_inf_nan=False, strict=True)
    z: float = Field(ge=-10, le=10, allow_inf_nan=False, strict=True)


class ExtrinsicPair(BaseModel):
    camera: Point3
    reference: Point3


class ExtrinsicMeasurement(BaseModel):
    reference_frame: Literal['base_link', 'gripper_link']
    pairs: list[ExtrinsicPair] = Field(min_length=4, max_length=30)


class RgbdExtrinsicMeasurement(BaseModel):
    pairs: list[ExtrinsicPair] = Field(min_length=4, max_length=30)



class GyroApply(BaseModel):
    config_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    candidate_hash: str = Field(pattern=r'^[0-9a-f]{64}$')


class GyroRestore(BaseModel):
    backup_id: str = Field(pattern=r'^[0-9a-f]{32}$')



FiniteMatrixNumber = Annotated[float, Field(ge=-10, le=10, allow_inf_nan=False, strict=True)]
MatrixRow = Annotated[list[FiniteMatrixNumber], Field(min_length=4, max_length=4)]
Matrix4 = Annotated[list[MatrixRow], Field(min_length=4, max_length=4)]


class HandEyePair(BaseModel):
    base_T_link4: Matrix4
    camera_T_target: Matrix4


class HandEyeMeasurement(BaseModel):
    pairs: list[HandEyePair] = Field(min_length=5, max_length=30)


class TcpPivotMeasurement(BaseModel):
    poses: list[Matrix4] = Field(min_length=5, max_length=30)



class GripperWidthSample(BaseModel):
    phase: Literal['open', 'closed']
    width_mm: float = Field(ge=0, le=300, allow_inf_nan=False, strict=True)



class WheelSpeedReference(BaseModel):
    port: int = Field(ge=1, le=4, strict=True)
    reference_rps: float = Field(ge=-100, le=100, allow_inf_nan=False, strict=True)



class LidarDirectionRequest(BaseModel):
    expected_deg: float = Field(ge=-180, le=180, allow_inf_nan=False, strict=True)
    max_range_m: float = Field(ge=0.1, le=5, allow_inf_nan=False, strict=True)



class OdomCaptureStart(BaseModel):
    motion: Literal['forward', 'lateral', 'rotation']
    source: Literal['raw', 'ekf']


class OdomCaptureFinish(BaseModel):
    reference: float = Field(ge=-10000, le=10000, allow_inf_nan=False, strict=True)



class OdomFitRequest(BaseModel):
    motion: Literal['forward','lateral','rotation']
    record_ids: list[Annotated[str, Field(pattern=r'^[0-9a-f]{32}$')]] = Field(min_length=3,max_length=10)


def stored_results():
    """Load saved candidate results, excluding images. / 영상 없이 저장된 후보 결과만 읽는다."""
    try:
        values = json.loads((ROOT / 'calibration/candidates.json').read_text())
        return values if isinstance(values, dict) else {}
    except (OSError, ValueError):
        return {}


def public_state():
    """Return bounded status without filesystem details. / 경로를 제외한 제한된 상태를 반환한다."""
    results = stored_results()
    history = results.get('_history', [])
    if not isinstance(history, list): history = []
    records = results.get('_records', {})
    if not isinstance(records, dict): records = {}
    history = [{**item, 'details_available': item.get('id') in records} for item in history if isinstance(item, dict) and item.get('kind') != 'gripper_force_fit']
    try:
        snapshot = json.loads((ROOT / 'run/ros-status.json').read_text())
        camera_info = fresh_camera_info(snapshot, time.time())
        arm_info = fresh_arm_observation(snapshot, time.time())
        wheel_info = fresh_wheel_feedback(snapshot, time.time())
    except (OSError, ValueError):
        camera_info = {}
        arm_info = {'mapping_confirmed': False, 'joints': {}}
        wheel_info = None
    gripper = arm_info.get('joints', {}).get('r_joint', {})
    gripper_width_display = gripper_settings.width(ROOT/'calibration/gripper-active.json', gripper.get('position_rad'), gripper.get('servo_id')) if arm_info.get('source_confirmed') and gripper.get('fresh') else None
    return {'gripper_width_display_mm':gripper_width_display, 'wheel_info': wheel_info, 'arm_info': arm_info, 'camera_info': camera_info, 'running': state['running'], 'error': state['error'], 'captures': len(state['captures']),
            'imu': state['imu'] or results.get('imu'), 'camera': state['camera'] or results.get('camera'),
            'accel_poses': sorted(state.get('accel_poses', {})), 'accel': state.get('accel') or results.get('accel'),
            'footprint': state.get('footprint') or results.get('footprint'),
            'battery': state.get('battery') or results.get('battery'),
            'battery_fit': state.get('battery_fit') or results.get('battery_fit'),
            'battery_samples': state.get('battery_samples', []),
            'lidar': state.get('lidar') or results.get('lidar'),
            'lidar_yaw': state.get('lidar_yaw') or results.get('lidar_yaw'),
            'lidar_scan': state.get('lidar_scan') or results.get('lidar_scan'),
            'odometry': state.get('odometry') or results.get('odometry'),
            'odom_fit': state.get('odom_fit') or results.get('odom_fit'),
            'odom_capture': state.get('odom_capture'),
            'wheel': state.get('wheel') or results.get('wheel'),
            'wheel_speed': state.get('wheel_speed') or results.get('wheel_speed'),
            'wheel_speed_samples': state.get('wheel_speed_samples', []),
            'wheel_speed_fit': state.get('wheel_speed_fit') or results.get('wheel_speed_fit'),
            'rgb_depth': state.get('rgb_depth') or results.get('rgb_depth'),
            'rgbd_extrinsic': state.get('rgbd_extrinsic') or results.get('rgbd_extrinsic'),
            'arm': state.get('arm') or results.get('arm'),
            'gripper': state.get('gripper') or results.get('gripper'),
            'joint_candidate': state.get('joint_candidate') or results.get('joint_candidate'),
            'tcp': state.get('tcp') or results.get('tcp'),
            'hand_eye': state.get('hand_eye') or results.get('hand_eye'),
            'tcp_pivot': state.get('tcp_pivot') or results.get('tcp_pivot'),
            'gripper_width': state.get('gripper_width') or results.get('gripper_width'),
            'gripper_width_samples': state.get('gripper_width_samples', {}),
            'catalog': calibration_catalog(), 'history': list(reversed(history[-50:]))}


def save_result(kind, result):
    """Atomically save candidates outside active configuration. / 활성 설정 외부에 후보를 원자 저장한다."""
    with lock:
        directory = ROOT / 'calibration'
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        values = stored_results()
        entry = {'measured_at': datetime.now(timezone.utc).isoformat(), **result}
        values[kind] = entry
        history = values.get('_history', [])
        if not isinstance(history, list):
            raise ValueError('invalid_history')
        record_id = uuid4().hex
        history = history + [{'id': record_id, 'kind': kind, 'measured_at': entry['measured_at'], 'status': 'candidate'}]
        values['_history'] = history[-500:]
        records = values.get('_records', {})
        if not isinstance(records, dict):
            raise ValueError('invalid_history')
        records[record_id] = {'kind': kind, 'result': entry}
        retained = {item['id'] for item in history[-100:] if isinstance(item, dict) and item.get('id') in records}
        values['_records'] = {key: value for key, value in records.items() if key in retained}
        # The new history and latest candidate are one transaction in the same file.
        # 한글: 새 이력과 최신 후보를 같은 파일에 원자적으로 저장한다.
        fd, temporary = tempfile.mkstemp(prefix='.candidates-', dir=directory)
        try:
            with os.fdopen(fd, 'w') as output:
                json.dump(values, output, allow_nan=False)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, directory / 'candidates.json')
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
        return entry


def run_job(kind, board=None):
    """Run one bounded worker and keep failures explicit. / 제한된 작업을 실행하고 실패를 명시한다."""
    try:
        env = os.environ.copy()
        for key in ('PYTHONPATH', 'ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER', 'FASTRTPS_DEFAULT_PROFILES_FILE',
                    'FASTDDS_DEFAULT_PROFILES_FILE', 'CYCLONEDDS_URI', 'ROS_LOCALHOST_ONLY', 'FASTDDS_BUILTIN_TRANSPORTS',
                    'ROS_AUTOMATIC_DISCOVERY_RANGE'):
            env.pop(key, None)
        env['OPENBLAS_NUM_THREADS'] = '1'
        if kind == 'lidar_scan':
            env['ROS_DOMAIN_ID'] = '25'
            command = ['/bin/bash', '-c', 'source /opt/ros/jazzy/setup.bash && exec /usr/bin/python3 "$1" "$2" "$3"',
                       'lidar-check', str(PROJECT / 'tools/ops/calibration/lidar_orientation.py'),
                       str(board['expected_deg']), str(board['max_range_m'])]
            payload = None
        elif kind in ('imu', 'accel_pose'):
            env['ROS_DOMAIN_ID'] = '25'
            command = ['/bin/bash', '-c', 'source /opt/ros/jazzy/setup.bash && exec /usr/bin/python3 "$1"',
                       'imu-measure', str(PROJECT / ('tools/imu_calibration/dashboard_measure.py' if kind == 'imu' else 'tools/imu_calibration/dashboard_accel_pose.py'))]
            if kind == 'accel_pose':
                command[2] += ' "$2"'
                command.append(board['pose'])
            payload = None
        else:
            command = ['/usr/bin/python3', str(PROJECT / 'tools/camera_calibration/dashboard_compute.py')]
            payload = json.dumps({'paths': [str(p) for p in state['captures']], **board})
        completed = subprocess.run(command, input=payload, text=True, capture_output=True, timeout=90, env=env)
        try:
            data = json.loads(completed.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            raise ValueError('worker_failed') from None
        if completed.returncode or not isinstance(data.get('result'), dict):
            raise ValueError(str(data.get('error', 'worker_failed'))[:80])
        with lock:
            if kind == 'accel_pose':
                poses = state.setdefault('accel_poses', {})
                candidate = data['result']
                if poses and any(value['source_id'] != candidate['source_id'] or value['frame_id'] != candidate['frame_id'] for value in poses.values()):
                    raise ValueError('source_changed')
                poses[board['pose']] = candidate
                if len(poses) == 6:
                    state['accel'] = save_result('accel', imu_math.accel_candidate(poses))
            else:
                state[kind] = save_result(kind, data['result'])
            state['error'] = None
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        error = 'worker_timeout' if isinstance(exc, subprocess.TimeoutExpired) else str(exc)
        with lock:
            state['error'] = error[:80]
    finally:
        with lock:
            state['running'] = None


@router.get('')
def calibration_status():
    """Return calibration state. / 보정 상태를 반환한다."""
    with lock:
        return public_state()


@router.post('/imu')
def start_imu():
    """Start a stationary bias observation. / 정지 bias 관측을 시작한다."""
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        state['error'] = None
        state['running'] = 'imu'
        executor.submit(run_job, 'imu')
        return public_state()


@router.post('/accel/{pose}')
def start_accel_pose(pose: str):
    """Start a single stationary pose measurement. / 정지 자세 하나의 측정을 시작한다."""
    if pose not in ('x_plus', 'x_minus', 'y_plus', 'y_minus', 'z_plus', 'z_minus'):
        raise HTTPException(400, 'invalid_pose')
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        state['error'] = None
        state['running'] = 'accel_pose'
        executor.submit(run_job, 'accel_pose', {'pose': pose})
        return public_state()


@router.post('/accel-reset')
def reset_accel():
    """Discard the current pose set without deleting saved results. / 현재 자세 모음만 초기화한다."""
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        state['accel_poses'] = {}
        state['error'] = None
        return public_state()


@router.post('/battery-compare')
def battery_compare(reference: BatteryReference):
    """Compare external reference voltage with a fresh robot sensor sample.

    한글: 외부 기준 전압과 로봇의 최신 전압 표본을 비교한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        measured, measured_at = read_fresh_battery()
        result = {'reference_v': reference.reference_v, 'sensor_v': measured,
                  'difference_v': measured - reference.reference_v,
                  'relative_error_percent': (measured - reference.reference_v) / reference.reference_v * 100,
                  'sensor_received_at': measured_at, 'source': 'battery_state',
                  'method': 'single_reference_comparison', 'applied': False}
        try:
            state['battery'] = save_result('battery', result)
        except (ValueError, OSError):
            raise HTTPException(503, 'save_failed') from None
        return public_state()


def read_fresh_battery():
    """Read a fresh sensor voltage without changing the safety path.

    한글: 안전 경로를 바꾸지 않고 최신 센서 전압을 읽는다.
    """
    try:
        snapshot = json.loads((ROOT / 'run/ros-status.json').read_text())
        now=time.time();captured=snapshot['timestamp'];measured_at=snapshot['battery_received_at'];measured=snapshot['battery_voltage']
        numbers=(captured, measured_at, measured)
        if (any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) for x in numbers)
                or not 0<=now-captured<8 or not 0<=now-measured_at<10 or measured_at>captured or not 0<measured<=60):
            raise ValueError()
        return measured, measured_at
    except (OSError,ValueError,KeyError,TypeError):
        raise HTTPException(503,'battery_unavailable') from None


@router.post('/battery-sample')
def battery_sample(reference: BatteryReference):
    """Collect distinct fresh battery references without modifying thresholds.

    한글: 배터리 임계값을 바꾸지 않고 서로 다른 최신 기준 표본을 수집한다.
    """
    with lock:
        if state['running']: raise HTTPException(409,'busy')
        sensor, received=read_fresh_battery()
        samples=state.setdefault('battery_samples',[])
        if len(samples)>=10:raise HTTPException(400,'battery_sample_limit')
        if any(item['sensor_received_at']==received for item in samples):raise HTTPException(409,'battery_duplicate_sample')
        samples.append({'reference_v':reference.reference_v,'sensor_v':sensor,'sensor_received_at':received})
        return public_state()


@router.post('/battery-fit')
def battery_fit():
    """Estimate a linear voltage reference mapping from three or more samples.

    한글: 세 개 이상의 표본으로 선형 전압 기준 변환 후보를 계산한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        samples=state.get('battery_samples',[])
        if len(samples)<3:raise HTTPException(400,'battery_insufficient_samples')
        x=[s['sensor_v'] for s in samples];y=[s['reference_v'] for s in samples]
        if max(x)-min(x)<0.2:raise HTTPException(400,'battery_insufficient_range')
        xm=sum(x)/len(x);ym=sum(y)/len(y)
        denominator=sum((v-xm)**2 for v in x)
        slope=sum((a-xm)*(b-ym) for a,b in zip(x,y))/denominator
        intercept=ym-slope*xm
        if not .5<=slope<=2 or abs(intercept)>10:raise HTTPException(400,'battery_fit_invalid')
        residuals=[slope*a+intercept-b for a,b in zip(x,y)]
        result={'samples':samples.copy(),'slope':slope,'intercept_v':intercept,
                'rms_v':math.sqrt(sum(v*v for v in residuals)/len(residuals)),
                'method':'linear_reference_fit','independent_validation':False,'applied':False}
        try:state['battery_fit']=save_result('battery_fit',result)
        except (OSError,ValueError):raise HTTPException(503,'save_failed') from None
        return public_state()


@router.post('/battery-samples-reset')
def battery_samples_reset():
    """Discard unfinished voltage samples only. / 미완료 전압 표본만 초기화한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        state['battery_samples']=[]
        return public_state()


@router.get('/history/{record_id}')
def calibration_history_detail(record_id: str):
    """Return retained candidate details, excluding images and filesystem paths.

    한글: 영상과 파일 경로 없이 보관된 측정 상세를 반환한다.
    """
    if len(record_id) != 32 or any(c not in '0123456789abcdef' for c in record_id):
        raise HTTPException(404, 'record_not_found')
    records = stored_results().get('_records', {})
    item = records.get(record_id) if isinstance(records, dict) else None
    if not isinstance(item, dict) or not isinstance(item.get('result'), dict):
        raise HTTPException(404, 'record_not_found')
    return {'id':record_id, **item}


@router.post('/history/{record_id}/restore-candidate')
def restore_candidate(record_id: str):
    """Restore a saved result as a new candidate without changing active settings.

    한글: 활성 설정 변경 없이 저장 결과를 새 후보로 복원한다.
    """
    allowed = {'imu','accel','camera','footprint','battery','lidar','lidar_yaw','lidar_scan','odometry','wheel',
               'wheel_speed','wheel_speed_fit','rgb_depth','rgbd_extrinsic','arm','gripper','gripper_width','tcp','hand_eye','tcp_pivot','battery_fit','odom_fit','joint_candidate'}
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        item = calibration_history_detail(record_id)
        kind, old = item['kind'], item['result']
        if kind not in allowed or old.get('applied') is not False:
            raise HTTPException(409, 'record_not_restorable')
        new = {**old, 'original_measured_at':old.get('measured_at'), 'restored_from':record_id}
        new.pop('measured_at', None)
        try:
            state[kind] = save_result(kind, new)
        except (OSError, ValueError):
            raise HTTPException(503, 'save_failed') from None
        return public_state()


@router.get('/gripper-settings')
def gripper_settings_status():
    """Preview display-only gripper width and its backups.

    한글: 표시 전용 그리퍼 폭 보정과 백업을 확인한다.
    """
    path=ROOT/'calibration/gripper-active.json';directory=ROOT/'calibration/gripper-settings'
    try:plan,error=gripper_settings.preview(path,state.get('gripper_width') or stored_results().get('gripper_width')),None
    except (OSError,ValueError,UnicodeError) as exc:plan,error=None,str(exc) if isinstance(exc,ValueError) else 'config_unavailable'
    backups=[]
    try:
        for item in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            if item.is_symlink():continue
            data=json.loads(item.read_text());backup_id=data.get('id')
            if isinstance(backup_id,str) and len(backup_id)==32 and item.stem==backup_id:backups.append({'id':backup_id,'created_at':item.stat().st_mtime})
    except (OSError,ValueError,TypeError):backups=[]
    return {'preview':plan,'error':error,'backups':backups}


@router.post('/gripper-settings/apply')
def gripper_settings_apply(request: GyroApply):
    """Activate reviewed gripper width for display only.

    한글: 검토한 그리퍼 폭을 표시 전용으로 활성화한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return gripper_settings.apply(ROOT/'calibration/gripper-active.json',ROOT/'calibration/gripper-settings',
            state.get('gripper_width') or stored_results().get('gripper_width'),request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/gripper-settings/restore')
def gripper_settings_restore(request: GyroRestore):
    """Restore a matching display-only gripper setting.

    한글: 일치하는 표시 전용 그리퍼 설정을 복원한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return gripper_settings.restore(ROOT/'calibration/gripper-active.json',ROOT/'calibration/gripper-settings',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.get('/tcp-settings')
def tcp_settings_status():
    """Preview the installed TCP position and backups.

    한글: 설치된 TCP 위치와 백업을 미리 확인한다.
    """
    path=PROJECT/'install/jetrover_description/share/jetrover_description/urdf/arm.urdf.xacro';directory=ROOT/'calibration/tcp-settings'
    try:plan,error=tcp_settings.preview(path,state.get('tcp_pivot') or stored_results().get('tcp_pivot')),None
    except (OSError,ValueError,UnicodeError) as exc:plan,error=None,str(exc) if isinstance(exc,ValueError) else 'config_unavailable'
    backups=[]
    try:
        for item in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            if item.is_symlink():continue
            data=json.loads(item.read_text());backup_id=data.get('id')
            if isinstance(backup_id,str) and len(backup_id)==32 and item.stem==backup_id:backups.append({'id':backup_id,'created_at':item.stat().st_mtime})
    except (OSError,ValueError,TypeError):backups=[]
    return {'preview':plan,'error':error,'backups':backups}


@router.post('/tcp-settings/apply')
def tcp_settings_apply(request: GyroApply):
    """Apply a reviewed TCP position without commanding the arm.

    한글: 팔을 구동하지 않고 검토한 TCP 위치를 적용한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return tcp_settings.apply(PROJECT/'install/jetrover_description/share/jetrover_description/urdf/arm.urdf.xacro',
            ROOT/'calibration/tcp-settings',state.get('tcp_pivot') or stored_results().get('tcp_pivot'),request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/tcp-settings/restore')
def tcp_settings_restore(request: GyroRestore):
    """Restore a matching installed TCP model backup. / 일치하는 설치 TCP 모델 백업을 복원한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return tcp_settings.restore(PROJECT/'install/jetrover_description/share/jetrover_description/urdf/arm.urdf.xacro',
                                         ROOT/'calibration/tcp-settings',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.get('/battery-settings')
def battery_settings_status():
    """Preview display-only voltage correction and backups.

    한글: 표시 전용 전압 보정과 백업을 미리 확인한다.
    """
    path=ROOT/'calibration/battery-active.json';directory=ROOT/'calibration/battery-settings'
    try:plan,error=battery_settings.preview(path,state.get('battery_fit') or stored_results().get('battery_fit')),None
    except (OSError,ValueError,UnicodeError) as exc:plan,error=None,str(exc) if isinstance(exc,ValueError) else 'config_unavailable'
    backups=[]
    try:
        for item in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            if item.is_symlink():continue
            data=json.loads(item.read_text());backup_id=data.get('id')
            if isinstance(backup_id,str) and len(backup_id)==32 and item.stem==backup_id:backups.append({'id':backup_id,'created_at':item.stat().st_mtime})
    except (OSError,ValueError,TypeError):backups=[]
    return {'preview':plan,'error':error,'backups':backups}


@router.post('/battery-settings/apply')
def battery_settings_apply(request: GyroApply):
    """Activate a reviewed dashboard-only voltage correction.

    한글: 확인된 대시보드 표시 전용 전압 보정을 활성화한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return battery_settings.apply(ROOT/'calibration/battery-active.json',ROOT/'calibration/battery-settings',
            state.get('battery_fit') or stored_results().get('battery_fit'),request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/battery-settings/restore')
def battery_settings_restore(request: GyroRestore):
    """Restore a matching display-only voltage configuration.

    한글: 일치하는 표시 전용 전압 설정을 복원한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return battery_settings.restore(ROOT/'calibration/battery-active.json',ROOT/'calibration/battery-settings',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.get('/joint-settings')
def joint_settings_status():
    """Preview a single installed joint offset and list backups.

    한글: 단일 설치 관절 오프셋과 백업을 미리 확인한다.
    """
    path=PROJECT/'install/jetrover_base/share/jetrover_base/config/base.yaml';directory=ROOT/'calibration/joint-settings'
    try:plan,error=joint_settings.preview(path,state.get('joint_candidate') or stored_results().get('joint_candidate')),None
    except (OSError,ValueError,UnicodeError) as exc:plan,error=None,str(exc) if isinstance(exc,ValueError) else 'config_unavailable'
    backups=[]
    try:
        for item in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            if item.is_symlink():continue
            data=json.loads(item.read_text());backup_id=data.get('id')
            if isinstance(backup_id,str) and len(backup_id)==32 and item.stem==backup_id:backups.append({'id':backup_id,'created_at':item.stat().st_mtime})
    except (OSError,ValueError,TypeError):backups=[]
    return {'preview':plan,'error':error,'backups':backups}


@router.post('/joint-settings/apply')
def joint_settings_apply(request: GyroApply):
    """Apply a reviewed joint offset; do not command a motor.

    한글: 구동 명령 없이 검토된 관절 오프셋을 적용한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return joint_settings.apply(PROJECT/'install/jetrover_base/share/jetrover_base/config/base.yaml',
            ROOT/'calibration/joint-settings',state.get('joint_candidate') or stored_results().get('joint_candidate'),request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/joint-settings/restore')
def joint_settings_restore(request: GyroRestore):
    """Restore a matching joint settings backup. / 일치하는 관절 설정 백업을 복원한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return gyro_settings.restore(PROJECT/'install/jetrover_base/share/jetrover_base/config/base.yaml',
                                          ROOT/'calibration/joint-settings',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/odom-fit')
def odom_fit(request: OdomFitRequest):
    """Fit a candidate from separately selected raw-command trial results.

    한글: 선택한 보정 전 명령 적분 시험 결과들로 후보를 계산한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        if len(set(request.record_ids)) != len(request.record_ids):raise HTTPException(400,'invalid_trials')
        records=stored_results().get('_records',{})
        try:
            selected=[records[record_id] for record_id in request.record_ids]
            result=odom_settings.fit(PROJECT/'install/jetrover_base/share/jetrover_base/config/base.yaml',request.motion,selected)
            result['record_ids']=request.record_ids
            state['odom_fit']=save_result('odom_fit',result)
        except (KeyError,ValueError,TypeError) as exc:raise HTTPException(400,str(exc) if isinstance(exc,ValueError) else 'invalid_trials') from None
        except OSError:raise HTTPException(503,'config_unavailable') from None
        return public_state()


@router.get('/odom-settings')
def odom_settings_status():
    """Preview and list command odometry settings backups.

    한글: 명령 기반 오도메트리 설정과 백업을 미리 확인한다.
    """
    path=PROJECT/'install/jetrover_base/share/jetrover_base/config/base.yaml';directory=ROOT/'calibration/odom-settings'
    try:plan,error=odom_settings.preview(path,state.get('odom_fit') or stored_results().get('odom_fit')),None
    except (OSError,ValueError,UnicodeError) as exc:plan,error=None,str(exc) if isinstance(exc,ValueError) else 'config_unavailable'
    backups=[]
    try:
        for item in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            if item.is_symlink():continue
            data=json.loads(item.read_text());backup_id=data.get('id')
            if isinstance(backup_id,str) and len(backup_id)==32 and item.stem==backup_id:backups.append({'id':backup_id,'created_at':item.stat().st_mtime})
    except (OSError,ValueError,TypeError):backups=[]
    return {'preview':plan,'error':error,'backups':backups}


@router.post('/odom-settings/apply')
def odom_settings_apply(request: GyroApply):
    """Apply reviewed command odometry scale without motion or restart.

    한글: 구동·재시작 없이 검토한 명령 오도메트리 배율을 적용한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return odom_settings.apply(PROJECT/'install/jetrover_base/share/jetrover_base/config/base.yaml',
            ROOT/'calibration/odom-settings',state.get('odom_fit') or stored_results().get('odom_fit'),request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/odom-settings/restore')
def odom_settings_restore(request: GyroRestore):
    """Restore a matching odometry settings backup. / 일치하는 오도메트리 설정 백업을 복원한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return gyro_settings.restore(PROJECT/'install/jetrover_base/share/jetrover_base/config/base.yaml',
                                         ROOT/'calibration/odom-settings',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.get('/lidar-settings')
def lidar_settings_status():
    """Preview installed LiDAR translation and backups.

    한글: 설치된 LiDAR 위치와 백업을 미리 확인한다.
    """
    path=PROJECT/'install/jetrover_description/share/jetrover_description/urdf/lidar.urdf.xacro'
    directory=ROOT/'calibration/lidar-settings'
    try:plan,error=lidar_settings.preview(path,state.get('lidar') or stored_results().get('lidar')),None
    except (OSError,ValueError,UnicodeError) as exc:plan,error=None,str(exc) if isinstance(exc,ValueError) else 'config_unavailable'
    backups=[]
    try:
        for item in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            if item.is_symlink():continue
            data=json.loads(item.read_text());backup_id=data.get('id')
            if isinstance(backup_id,str) and len(backup_id)==32 and item.stem==backup_id:
                backups.append({'id':backup_id,'created_at':item.stat().st_mtime})
    except (OSError,ValueError,TypeError):backups=[]
    return {'preview':plan,'error':error,'backups':backups}


@router.post('/lidar-yaw-candidate')
def lidar_yaw_candidate(measurement: LidarYawMeasurement):
    """Store a manually measured mounting yaw for separate review.

    한글: 수동 측정한 장착 yaw를 별도 검토용 후보로 저장한다.
    """
    with lock:
        if state['running']: raise HTTPException(409, 'busy')
        result = {'parent_frame':'base_link', 'child_frame':'lidar_link', 'yaw_deg':measurement.yaw_deg,
                  'method':'manual_mount_measurement', 'independent_validation':False, 'applied':False}
        try:
            lidar_settings.preview_yaw(PROJECT/'install/jetrover_description/share/jetrover_description/urdf/lidar.urdf.xacro', result)
            state['lidar_yaw'] = save_result('lidar_yaw', result)
        except ValueError as exc: raise HTTPException(400, str(exc)) from None
        except (OSError, UnicodeError): raise HTTPException(503, 'config_unavailable') from None
        return public_state()


@router.get('/lidar-yaw-settings')
def lidar_yaw_settings_status():
    """Preview the mounting yaw and its backups. / 장착 yaw와 백업을 미리 본다."""
    path=PROJECT/'install/jetrover_description/share/jetrover_description/urdf/lidar.urdf.xacro'
    try: plan,error=lidar_settings.preview_yaw(path,state.get('lidar_yaw') or stored_results().get('lidar_yaw')),None
    except (OSError,ValueError,UnicodeError) as exc:plan,error=None,str(exc) if isinstance(exc,ValueError) else 'config_unavailable'
    return {'preview':plan,'error':error,'backups':lidar_settings_status()['backups']}


@router.post('/lidar-yaw-settings/apply')
def lidar_yaw_settings_apply(request: GyroApply):
    """Apply only a reviewed mounting yaw. / 확인한 장착 yaw만 적용한다."""
    with lock:
        if state['running']: raise HTTPException(409, 'busy')
        try:
            return lidar_settings.apply_yaw(PROJECT/'install/jetrover_description/share/jetrover_description/urdf/lidar.urdf.xacro',
                ROOT/'calibration/lidar-settings',state.get('lidar_yaw') or stored_results().get('lidar_yaw'),request.config_hash,request.candidate_hash)
        except ValueError as exc: raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError): raise HTTPException(503,'config_unavailable') from None


@router.post('/lidar-settings/apply')
def lidar_settings_apply(request: GyroApply):
    """Apply the reviewed LiDAR translation only. / 확인한 LiDAR 위치만 적용한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:
            return lidar_settings.apply(PROJECT/'install/jetrover_description/share/jetrover_description/urdf/lidar.urdf.xacro',
                ROOT/'calibration/lidar-settings',state.get('lidar') or stored_results().get('lidar'),
                request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/lidar-settings/restore')
def lidar_settings_restore(request: GyroRestore):
    """Restore an unchanged installed LiDAR model. / 변경되지 않은 설치 LiDAR 모델을 복원한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:
            return lidar_settings.restore(PROJECT/'install/jetrover_description/share/jetrover_description/urdf/lidar.urdf.xacro',
                ROOT/'calibration/lidar-settings',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.get('/footprint-settings')
def footprint_settings_status():
    """Preview conservative default Nav2 footprint and backups.

    한글: 보수적인 기본 Nav2 외형과 백업을 미리 본다.
    """
    path=PROJECT / 'install/jetrover_navigation/share/jetrover_navigation/config/nav2_params.yaml'
    directory=ROOT / 'calibration/footprint-settings'
    try:
        plan,error=footprint_settings.preview(path,state.get('footprint') or stored_results().get('footprint')),None
    except (OSError,ValueError,UnicodeError) as exc:
        plan,error=None,str(exc) if isinstance(exc,ValueError) else 'config_unavailable'
    backups=[]
    try:
        for item in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            if item.is_symlink():continue
            data=json.loads(item.read_text());backup_id=data.get('id')
            if isinstance(backup_id,str) and len(backup_id)==32 and item.stem==backup_id:
                backups.append({'id':backup_id,'created_at':item.stat().st_mtime})
    except (OSError,ValueError,TypeError):backups=[]
    return {'preview':plan,'error':error,'backups':backups}


@router.post('/footprint-settings/apply')
def footprint_settings_apply(request: GyroApply):
    """Apply a reviewed nonshrinking footprint to both default costmaps.

    한글: 검토한 비축소 외형을 기본 두 비용지도에 적용한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:
            return footprint_settings.apply(PROJECT / 'install/jetrover_navigation/share/jetrover_navigation/config/nav2_params.yaml',
                ROOT / 'calibration/footprint-settings',state.get('footprint') or stored_results().get('footprint'),
                request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/footprint-settings/restore')
def footprint_settings_restore(request: GyroRestore):
    """Restore an unchanged default Nav2 configuration. / 변경되지 않은 기본 Nav2 설정을 복원한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:
            return footprint_settings.restore(PROJECT / 'install/jetrover_navigation/share/jetrover_navigation/config/nav2_params.yaml',
                ROOT / 'calibration/footprint-settings',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.get('/camera-settings')
def camera_settings_status():
    """Preview the color CameraInfo override and its backups.

    한글: 컬러 CameraInfo 재정의와 백업을 미리 확인한다.
    """
    path = PROJECT / 'install/jetrover_perception/share/jetrover_perception/config/dabai_dcw.yaml'
    directory = ROOT / 'calibration/camera-settings'
    candidate = state.get('camera') or stored_results().get('camera')
    try:
        plan, error = camera_settings.preview(path, candidate, public_state()['camera_info'].get('color')), None
    except (OSError, ValueError, UnicodeError) as exc:
        plan, error = None, str(exc) if isinstance(exc, ValueError) else 'config_unavailable'
    backups=[]
    try:
        for item in sorted(directory.glob('*.json'), key=lambda p:p.stat().st_mtime, reverse=True)[:50]:
            if item.is_symlink(): continue
            data=json.loads(item.read_text());backup_id=data.get('id')
            if isinstance(backup_id,str) and len(backup_id)==32 and item.stem==backup_id:
                backups.append({'id':backup_id,'created_at':item.stat().st_mtime})
    except (OSError, ValueError, TypeError):
        backups=[]
    return {'preview':plan,'error':error,'backups':backups}


@router.post('/camera-settings/apply')
def camera_settings_apply(request: GyroApply):
    """Configure only the reviewed color CameraInfo override.

    한글: 검토한 컬러 CameraInfo 재정의만 설정한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:
            return camera_settings.apply(PROJECT / 'install/jetrover_perception/share/jetrover_perception/config/dabai_dcw.yaml',
                ROOT / 'calibration/camera-settings', state.get('camera') or stored_results().get('camera'),
                public_state()['camera_info'].get('color'),request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/camera-settings/restore')
def camera_settings_restore(request: GyroRestore):
    """Restore a matching previous color driver configuration.

    한글: 일치하는 이전 컬러 드라이버 설정을 복원한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:
            return camera_settings.restore(PROJECT / 'install/jetrover_perception/share/jetrover_perception/config/dabai_dcw.yaml',
                                           ROOT / 'calibration/camera-settings',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.get('/accel-settings')
def accel_settings_status():
    """Preview accelerometer settings and list reversible backups.

    한글: 가속도 설정을 미리 보고 복원 가능한 백업을 나열한다.
    """
    path = PROJECT / 'install/jetrover_base/share/jetrover_base/config/base.yaml'
    directory = ROOT / 'calibration/accel-backups'
    candidate = state.get('accel') or stored_results().get('accel')
    try:
        plan, error = accel_settings.preview(path, candidate), None
    except (OSError, ValueError, UnicodeError) as exc:
        plan, error = None, str(exc) if isinstance(exc, ValueError) else 'config_unavailable'
    backups = []
    try:
        for item in sorted(directory.glob('*.json'), key=lambda p:p.stat().st_mtime, reverse=True)[:50]:
            if item.is_symlink(): continue
            data = json.loads(item.read_text()); backup_id = data.get('id')
            if isinstance(backup_id,str) and len(backup_id)==32 and item.stem==backup_id:
                backups.append({'id':backup_id, 'created_at':item.stat().st_mtime})
    except (OSError, ValueError, TypeError):
        backups = []
    return {'preview':plan, 'error':error, 'backups':backups}


@router.post('/accel-settings/apply')
def accel_settings_apply(request: GyroApply):
    """Apply a reviewed acceleration candidate without restarting the node.

    한글: 확인된 가속도 후보만 적용하며 노드는 재시작하지 않는다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:
            return accel_settings.apply(PROJECT / 'install/jetrover_base/share/jetrover_base/config/base.yaml',
                ROOT / 'calibration/accel-backups',state.get('accel') or stored_results().get('accel'),
                request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/accel-settings/restore')
def accel_settings_restore(request: GyroRestore):
    """Restore one matching acceleration backup. / 일치하는 가속도 백업을 복원한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:
            return gyro_settings.restore(PROJECT / 'install/jetrover_base/share/jetrover_base/config/base.yaml',
                ROOT / 'calibration/accel-backups',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.get('/gyro-settings')
def gyro_settings_status():
    """Return a setting preview and reversible backups without exposing file paths.

    한글: 파일 경로를 노출하지 않고 설정 미리보기와 복원 목록을 반환한다.
    """
    path = PROJECT / 'install/jetrover_base/share/jetrover_base/config/base.yaml'
    backup_dir = ROOT / 'calibration/gyro-backups'
    candidate = state['imu'] or stored_results().get('imu')
    try:
        plan, error = gyro_settings.preview(path, candidate), None
    except (OSError, ValueError, UnicodeError) as exc:
        plan, error = None, str(exc) if isinstance(exc, ValueError) else 'config_unavailable'
    backups = []
    try:
        paths = sorted(backup_dir.glob('*.json'), key=lambda item: item.stat().st_mtime, reverse=True)[:50]
        for item in paths:
            if item.is_symlink():
                continue
            value = json.loads(item.read_text())
            backup_id = value.get('id')
            if isinstance(backup_id, str) and len(backup_id) == 32 and item.stem == backup_id:
                backups.append({'id': backup_id, 'created_at': item.stat().st_mtime,
                                'after_hash': value.get('after_hash')})
    except (OSError, ValueError, TypeError):
        backups = []
    return {'preview': plan, 'error': error, 'backups': backups}


@router.post('/gyro-settings/apply')
def gyro_settings_apply(request: GyroApply):
    """Apply only the reviewed gyro candidate, leaving restart to the operator.

    한글: 확인된 자이로 후보만 적용하며 재시작은 운영자가 별도 수행한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        try:
            return gyro_settings.apply(PROJECT / 'install/jetrover_base/share/jetrover_base/config/base.yaml',
                                       ROOT / 'calibration/gyro-backups', state['imu'] or stored_results().get('imu'),
                                       request.config_hash, request.candidate_hash)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        except (OSError, UnicodeError):
            raise HTTPException(503, 'config_unavailable') from None


@router.post('/gyro-settings/restore')
def gyro_settings_restore(request: GyroRestore):
    """Restore one matching gyro backup without restarting a device.

    한글: 일치하는 자이로 백업을 장치 재시작 없이 복원한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        try:
            return gyro_settings.restore(PROJECT / 'install/jetrover_base/share/jetrover_base/config/base.yaml',
                                         ROOT / 'calibration/gyro-backups', request.backup_id)
        except (ValueError, KeyError, TypeError):
            raise HTTPException(409, 'restore_conflict') from None
        except (OSError, UnicodeError):
            raise HTTPException(503, 'config_unavailable') from None


@router.post('/odom-capture/start')
def odom_capture_start(request: OdomCaptureStart):
    """Record a starting odometry observation; do not command a movement.

    한글: 주행 명령 없이 시작 오도메트리 관측을 기록한다.
    """
    with lock:
        if state['running'] or state.get('odom_capture'):
            raise HTTPException(409, 'busy')
        try:
            snapshot = json.loads((ROOT / 'run/ros-status.json').read_text())
            current = fresh_odom(snapshot, request.source, time.time())
        except (OSError, ValueError):
            current = None
        if current is None:
            raise HTTPException(503, 'odom_unavailable')
        state['odom_capture'] = {'motion':request.motion, 'source':request.source, 'start':current, 'started_at':time.time()}
        return public_state()


@router.post('/odom-capture/finish')
def odom_capture_finish(request: OdomCaptureFinish):
    """Compare continuous start/end observations with an independent reference.

    한글: 연속된 시작·종료 관측을 독립 기준 실측값과 비교한다.
    """
    if abs(request.reference) < 0.1:
        raise HTTPException(400, 'reference_too_small')
    with lock:
        capture = state.get('odom_capture')
        if not capture:
            raise HTTPException(409, 'odom_not_started')
        if not 0 <= time.time() - capture['started_at'] < 300:
            raise HTTPException(409, 'odom_expired')
        try:
            snapshot = json.loads((ROOT / 'run/ros-status.json').read_text())
            end = fresh_odom(snapshot, capture['source'], time.time())
        except (OSError, ValueError):
            end = None
        if end is None:
            raise HTTPException(503, 'odom_unavailable')
        try:
            value = odom_displacement(capture['start'], end, capture['motion'])
        except ValueError:
            raise HTTPException(409, 'odom_discontinuity') from None
        diff = value - request.reference
        result = {'motion':capture['motion'], 'source':'odom_raw' if capture['source']=='raw' else 'ekf',
                  'unit':'deg' if capture['motion']=='rotation' else 'cm', 'reference':request.reference,
                  'recorded':value, 'difference':diff, 'relative_error_percent':diff/abs(request.reference)*100,
                  'method':'ros_start_end_comparison', 'frame_id':end['frame_id'], 'child_frame_id':end['child_frame_id'],
                  'started_at':capture['started_at'], 'finished_at':time.time(), 'applied':False}
        try:
            state['odometry'] = save_result('odometry', result)
        except (ValueError, OSError):
            raise HTTPException(503, 'save_failed') from None
        state['odom_capture'] = None
        return public_state()


@router.post('/odom-capture/cancel')
def odom_capture_cancel():
    """Discard an unfinished read-only recording. / 미완료 읽기 전용 기록을 취소한다."""
    with lock:
        state['odom_capture'] = None
        return public_state()


@router.post('/lidar-direction')
def lidar_direction(request: LidarDirectionRequest):
    """Start a bounded scan direction observation without publishing robot commands.

    한글: 로봇 명령 없이 제한된 스캔 방향 관찰을 시작한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        state['error'] = None
        state['running'] = 'lidar_scan'
        executor.submit(run_job, 'lidar_scan', request.model_dump())
        return public_state()


@router.post('/wheel-speed-sample')
def wheel_speed_sample(reference: WheelSpeedReference):
    """Collect a fresh wheel sample for an external speed reference.

    한글: 외부 속도 기준과 최신 휠 표본을 수집한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        feedback=public_state()['wheel_info']
        if feedback is None:raise HTTPException(503,'wheel_feedback_unavailable')
        sensor=feedback['port_rps'][reference.port-1];ref=reference.reference_rps
        if abs(sensor)<.02 or abs(ref)<.02 or sensor*ref<=0:raise HTTPException(400,'wheel_speed_invalid')
        samples=state.setdefault('wheel_speed_samples',[])
        if len(samples)>=10:raise HTTPException(400,'wheel_sample_limit')
        if samples and samples[0]['port']!=reference.port:raise HTTPException(409,'wheel_port_changed')
        if any(s['received_at']==feedback['received_at'] for s in samples):raise HTTPException(409,'wheel_duplicate_sample')
        samples.append({'port':reference.port,'sensor_rps':sensor,'reference_rps':ref,'received_at':feedback['received_at']})
        return public_state()


@router.post('/wheel-speed-fit')
def wheel_speed_fit():
    """Fit a per-port speed ratio without changing firmware or control.

    한글: 펌웨어와 제어를 바꾸지 않고 포트별 속도 비율을 추정한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        samples=state.get('wheel_speed_samples',[])
        if len(samples)<3:raise HTTPException(400,'wheel_insufficient_samples')
        magnitudes=[abs(s['sensor_rps']) for s in samples]
        if max(magnitudes)-min(magnitudes)<.2:raise HTTPException(400,'wheel_insufficient_range')
        denominator=sum(s['sensor_rps']**2 for s in samples)
        slope=sum(s['sensor_rps']*s['reference_rps'] for s in samples)/denominator
        if not .5<=slope<=2:raise HTTPException(400,'wheel_fit_invalid')
        residuals=[slope*s['sensor_rps']-s['reference_rps'] for s in samples]
        result={'port':samples[0]['port'],'samples':samples.copy(),'scale':slope,
                'rms_rps':math.sqrt(sum(v*v for v in residuals)/len(residuals)),
                'method':'external_speed_ratio','firmware_applied':False,'independent_validation':False,'applied':False}
        try:state['wheel_speed_fit']=save_result('wheel_speed_fit',result)
        except (OSError,ValueError):raise HTTPException(503,'save_failed') from None
        return public_state()


@router.post('/wheel-speed-samples-reset')
def wheel_speed_samples_reset():
    """Clear unfinished wheel samples. / 미완료 휠 표본을 초기화한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        state['wheel_speed_samples']=[]
        return public_state()


@router.post('/wheel-speed-compare')
def wheel_speed_compare(reference: WheelSpeedReference):
    """Compare a fresh controller port speed with a manual external reference.

    한글: 최신 컨트롤러 포트 속도를 수동 외부 기준과 비교한다.
    """
    if abs(reference.reference_rps) < 0.02:
        raise HTTPException(400, 'wheel_reference_too_small')
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        feedback = public_state()['wheel_info']
        if feedback is None:
            raise HTTPException(503, 'wheel_feedback_unavailable')
        measured = feedback['port_rps'][reference.port-1]
        result = {'port':reference.port, 'reference_rps':reference.reference_rps, 'sensor_rps':measured,
                  'difference_rps':measured-reference.reference_rps,
                  'relative_error_percent':(measured-reference.reference_rps)/abs(reference.reference_rps)*100,
                  'feedback_received_at':feedback['received_at'], 'method':'single_external_reference',
                  'independent_reference_verified':False, 'applied':False}
        try:
            state['wheel_speed'] = save_result('wheel_speed', result)
        except (ValueError, OSError):
            raise HTTPException(503, 'save_failed') from None
        return public_state()


@router.post('/gripper-width-sample')
def gripper_width_sample(sample: GripperWidthSample):
    """Record a fresh gripper observation and measured jaw width.

    한글: 최신 그리퍼 관측과 실측 개구 폭을 기록한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        arm = public_state()['arm_info']
        item = arm.get('joints', {}).get('r_joint')
        if not arm.get('source_confirmed') or not item or not item.get('fresh'):
            raise HTTPException(503, 'joint_unavailable')
        samples = dict(state.get('gripper_width_samples', {}))
        samples[sample.phase] = {'width_mm': sample.width_mm, 'angle_rad': item['position_rad'],
                                 'servo_id': item['servo_id'], 'recorded_at': time.time()}
        if set(samples) == {'open', 'closed'}:
            opened, closed = samples['open'], samples['closed']
            delta_angle = opened['angle_rad'] - closed['angle_rad']
            delta_width = opened['width_mm'] - closed['width_mm']
            if opened['servo_id'] != closed['servo_id'] or delta_width < 1 or abs(delta_angle) < 0.02:
                raise HTTPException(400, 'gripper_sample_invalid')
            slope = delta_width / delta_angle
            result = {'samples': samples, 'slope_mm_per_rad': slope,
                      'intercept_mm': opened['width_mm'] - slope * opened['angle_rad'],
                      'method':'two_point_linear_interpolation', 'independent_validation':False, 'applied':False}
            try:
                state['gripper_width'] = save_result('gripper_width', result)
            except (ValueError, OSError):
                raise HTTPException(503, 'save_failed') from None
        state['gripper_width_samples'] = samples
        return public_state()


@router.post('/gripper-width-reset')
def gripper_width_reset():
    """Clear only unfinished width samples. / 진행 중인 폭 표본만 초기화한다."""
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        state['gripper_width_samples'] = {}
        return public_state()


@router.post('/tcp-pivot-capture')
def tcp_pivot_capture():
    """Capture a fresh measured gripper pose without commanding the arm.

    한글: 팔 구동 명령 없이 최신 실측 그리퍼 자세를 캡처한다.
    """
    with lock:
        if state['running']: raise HTTPException(409, 'busy')
        def measured_joints():
            arm = public_state()['arm_info']
            joints = arm.get('joints', {})
            if not arm.get('source_confirmed') or any(not joints.get(f'joint{i}', {}).get('fresh') for i in range(1, 6)):
                raise HTTPException(503, 'arm_feedback_unavailable')
            return [joints[f'joint{i}']['position_rad'] for i in range(1, 6)]
        before = measured_joints()
        env = {**os.environ, 'ROS_DOMAIN_ID':'25', 'OPENBLAS_NUM_THREADS':'1', 'OMP_NUM_THREADS':'1'}
        command = ['/bin/bash', '-c', 'source /opt/ros/jazzy/setup.bash && exec /usr/bin/python3 "$1"',
                   'tcp-pose', str(PROJECT/'tools/ops/calibration/capture_arm_pose.py')]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=15, env=env)
            data = json.loads(completed.stdout)
            if completed.returncode or not isinstance(data.get('result'), list): raise ValueError('arm_tf_unavailable')
            after = measured_joints()
            if any(abs(a-b) > .01 for a,b in zip(before, after)): raise HTTPException(409, 'arm_moved')
            return {'pose':data['result'], 'stamp':data['stamp'], 'parent_frame':'base_link', 'child_frame':'gripper_link'}
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
            raise HTTPException(503, 'arm_tf_unavailable') from None


@router.post('/tcp-pivot-fit')
def tcp_pivot_fit(measurement: TcpPivotMeasurement):
    """Estimate a gripper TCP from multiple fixed-pivot arm poses.

    한글: 고정 접점의 여러 팔 자세로 그리퍼 기준 TCP를 추정한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        env = {**os.environ, 'OPENBLAS_NUM_THREADS':'1', 'OMP_NUM_THREADS':'1'}
        try:
            completed = subprocess.run(['/usr/bin/python3', str(PROJECT / 'tools/ops/calibration/tcp_pivot.py')],
                input=measurement.model_dump_json(), capture_output=True, text=True, timeout=10, env=env)
            data = json.loads(completed.stdout)
            if completed.returncode or not isinstance(data.get('result'), dict):
                error = data.get('error')
                raise HTTPException(400, error if error in ('invalid_pose', 'invalid_pose_count', 'insufficient_pose_diversity') else 'fit_failed')
            result = data['result']
            result.update({'parent_frame':'gripper_link', 'reference_frame':'base_link', 'source':'manual_poses',
                           'independent_validation':False, 'applied':False})
            state['tcp_pivot'] = save_result('tcp_pivot', result)
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
            raise HTTPException(503, 'fit_failed') from None
        return public_state()


def _camera_mount_transform():
    """Read a stable camera mount transform from the live ROS graph.

    한글: 실제 ROS 그래프에서 안정적인 카메라 장착 변환을 읽는다.
    """
    env = {**os.environ, 'ROS_DOMAIN_ID': '25', 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
    command = ['/bin/bash', '-c', 'source /opt/ros/jazzy/setup.bash && exec /usr/bin/python3 "$1"',
               'camera-mount', str(PROJECT / 'tools/ops/calibration/static_mount.py')]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=15, env=env)
        data = json.loads(completed.stdout)
        if completed.returncode or not isinstance(data.get('result'), list):
            raise ValueError(data.get('error', 'mount_tf_unavailable'))
        return data['result']
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        raise ValueError('mount_tf_unavailable') from None


@router.get('/hand-eye-settings')
def hand_eye_settings_status():
    """Preview the camera mount and its backups. / 카메라 장착 설정과 백업을 미리 본다."""
    path = PROJECT/'install/jetrover_description/share/jetrover_description/urdf/depth_camera.urdf.xacro'
    directory = ROOT/'calibration/hand-eye-settings'
    candidate = state.get('hand_eye') or stored_results().get('hand_eye')
    try:
        if not candidate: raise ValueError('candidate_unavailable')
        plan, error = hand_eye_settings.preview(path, candidate, _camera_mount_transform()), None
    except (OSError, ValueError, UnicodeError) as exc:
        plan, error = None, str(exc) if isinstance(exc, ValueError) else 'config_unavailable'
    backups = []
    try:
        for item in sorted(directory.glob('*.json'), key=lambda p:p.stat().st_mtime, reverse=True)[:50]:
            if item.is_symlink(): continue
            data = json.loads(item.read_text()); backup_id = data.get('id')
            if isinstance(backup_id, str) and len(backup_id) == 32 and item.stem == backup_id:
                backups.append({'id':backup_id, 'created_at':item.stat().st_mtime})
    except (OSError, ValueError, TypeError): backups = []
    return {'preview':plan, 'error':error, 'backups':backups}


@router.post('/hand-eye-settings/apply')
def hand_eye_settings_apply(request: GyroApply):
    """Apply the reviewed hand-eye mount. / 확인한 핸드아이 장착값을 적용한다."""
    with lock:
        if state['running']: raise HTTPException(409, 'busy')
        try:
            return hand_eye_settings.apply(
                PROJECT/'install/jetrover_description/share/jetrover_description/urdf/depth_camera.urdf.xacro',
                ROOT/'calibration/hand-eye-settings', state.get('hand_eye') or stored_results().get('hand_eye'),
                _camera_mount_transform(), request.config_hash, request.candidate_hash)
        except ValueError as exc: raise HTTPException(409, str(exc)) from None
        except (OSError, UnicodeError): raise HTTPException(503, 'config_unavailable') from None


@router.post('/hand-eye-settings/restore')
def hand_eye_settings_restore(request: GyroRestore):
    """Restore a matching camera model backup. / 일치하는 카메라 모델 백업을 복원한다."""
    with lock:
        if state['running']: raise HTTPException(409, 'busy')
        try:
            return hand_eye_settings.restore(
                PROJECT/'install/jetrover_description/share/jetrover_description/urdf/depth_camera.urdf.xacro',
                ROOT/'calibration/hand-eye-settings', request.backup_id)
        except (ValueError, KeyError, TypeError): raise HTTPException(409, 'restore_conflict') from None
        except (OSError, UnicodeError): raise HTTPException(503, 'config_unavailable') from None


@router.post('/hand-eye-capture')
def hand_eye_capture(board: Board):
    """Capture a stationary arm pose and time-matched chessboard image.

    한글: 정지한 팔 자세와 같은 시각의 체커보드 영상을 수집한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        def joints():
            arm=public_state()['arm_info'];items=arm.get('joints',{})
            if not arm.get('source_confirmed') or any(not items.get(f'joint{i}',{}).get('fresh') for i in range(1,6)):
                raise HTTPException(503,'arm_feedback_unavailable')
            return [items[f'joint{i}']['position_rad'] for i in range(1,6)]
        before=joints()
        env={**os.environ,'ROS_DOMAIN_ID':'25','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
        command=['/bin/bash','-c','source /opt/ros/jazzy/setup.bash && exec /usr/bin/python3 "$1"',
                 'hand-eye-capture',str(PROJECT/'tools/ops/calibration/hand_eye_capture.py')]
        try:
            completed=subprocess.run(command,input=board.model_dump_json(),capture_output=True,text=True,timeout=18,env=env)
            data=json.loads(completed.stdout)
            if completed.returncode or not isinstance(data.get('result'),dict):
                error=data.get('error')
                raise HTTPException(400,error if error in ('board_not_found','board_pose_failed','board_pose_inaccurate','camera_info_invalid') else 'hand_eye_sources_unavailable')
            after=joints()
            if any(abs(a-b)>.01 for a,b in zip(before,after)):raise HTTPException(409,'arm_moved')
            return data
        except (OSError,subprocess.TimeoutExpired,ValueError,KeyError):raise HTTPException(503,'hand_eye_sources_unavailable') from None


@router.post('/hand-eye-fit')
def hand_eye_fit(measurement: HandEyeMeasurement):
    """Estimate link4-to-camera hand-eye transform from multiple rigid poses.

    한글: 여러 강체 자세로 link4 기준 카메라 핸드아이 변환을 추정한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        env = {**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
        try:
            completed = subprocess.run(['/usr/bin/python3', str(PROJECT / 'tools/ops/calibration/hand_eye.py')],
                input=measurement.model_dump_json(), capture_output=True, text=True, timeout=10, env=env)
            data = json.loads(completed.stdout)
            if completed.returncode or not isinstance(data.get('result'), dict):
                error = data.get('error')
                raise HTTPException(400, error if error in ('invalid_pose', 'invalid_pose_count', 'insufficient_rotation_diversity') else 'fit_failed')
            result = data['result']
            result.update({'parent_frame': 'link4', 'camera_frame': 'depth_cam_color_optical_frame',
                           'source': 'manual_poses', 'independent_validation': False, 'applied': False})
            state['hand_eye'] = save_result('hand_eye', result)
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
            raise HTTPException(503, 'fit_failed') from None
        return public_state()


@router.post('/extrinsic-fit')
def extrinsic_fit(measurement: ExtrinsicMeasurement):
    """Fit a fixed-pose camera transform in an isolated bounded worker.

    한글: 고정 자세의 카메라 변환을 제한된 별도 계산으로 구한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        pairs = [pair.model_dump() for pair in measurement.pairs]
        payload = {'camera_points': [[p['camera'][axis] for axis in 'xyz'] for p in pairs],
                   'reference_points': [[p['reference'][axis] for axis in 'xyz'] for p in pairs]}
        env = {**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
        try:
            worker = subprocess.run(['/usr/bin/python3', str(PROJECT / 'tools/ops/calibration/rigid_transform.py')],
                                    input=json.dumps(payload), capture_output=True, text=True, timeout=5, env=env)
            result = json.loads(worker.stdout)
            if worker.returncode != 0 or 'result' not in result:
                raise HTTPException(400, result.get('error', 'fit_failed'))
            result = result['result']
            result.update({'camera_frame': 'depth_cam_color_optical_frame', 'reference_frame': measurement.reference_frame,
                           'method': 'single_pose_rigid_fit', 'source': 'manual_correspondences',
                           'hand_eye_calibrated': False, 'independent_validation': False, 'applied': False})
            state['tcp'] = save_result('tcp', result)
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
            raise HTTPException(503, 'fit_failed') from None
        return public_state()


class JointCandidateRequest(BaseModel):
    joint: Literal['joint1','joint2','joint3','joint4','joint5','r_joint']


@router.post('/joint-offset-candidate')
def joint_offset_candidate(request: JointCandidateRequest):
    """Compute an offset candidate from the latest source-confirmed comparison.

    한글: 발행 출처가 확인된 최근 기준 비교로 오프셋 후보를 계산한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        kind='gripper' if request.joint=='r_joint' else 'arm'
        comparison=state.get(kind) or stored_results().get(kind)
        if not isinstance(comparison,dict) or comparison.get('joint')!=request.joint or comparison.get('source_confirmed') is not True:
            raise HTTPException(409,'joint_reference_unconfirmed')
        current=comparison.get('current_offset_rad');difference=comparison.get('difference_rad')
        if (any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (current,difference))
                or abs(difference)>0.3 or abs(current-difference)>3):
            raise HTTPException(400,'joint_correction_out_of_range')
        result={'joint':request.joint,'current_offset_rad':current,'candidate_offset_rad':current-difference,
                'reference_rad':comparison['reference_rad'],'observed_rad':comparison['observed_rad'],
                'method':'single_reference_offset','source_confirmed':True,'independent_validation':False,'applied':False}
        try:state['joint_candidate']=save_result('joint_candidate',result)
        except (OSError,ValueError):raise HTTPException(503,'save_failed') from None
        return public_state()


@router.post('/joint-compare')
def joint_compare(reference: JointReference):
    """Compare a joint observation with an independent user-supplied reference.

    한글: 관절 관측을 사용자가 입력한 독립 기준 각도와 비교한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        arm = public_state()['arm_info']
        item = arm.get('joints', {}).get(reference.joint)
        if not arm.get('mapping_confirmed') or not item or not item.get('fresh'):
            raise HTTPException(503, 'joint_unavailable')
        kind = 'gripper' if reference.joint == 'r_joint' else 'arm'
        result = {'joint': reference.joint, 'reference_rad': reference.reference_rad,
                  'observed_rad': item['position_rad'],
                  'difference_rad': item['position_rad'] - reference.reference_rad,
                  'servo_id': item['servo_id'], 'servo_response_age_s': item['servo_response_age_s'],
                  'current_offset_rad': item.get('offset_rad'), 'source_confirmed': arm.get('source_confirmed') is True,
                  'source': 'manual_reference_and_ros_joint_state', 'independent_reference_verified': False,
                  'applied': False}
        try:
            state[kind] = save_result(kind, result)
        except (ValueError, OSError):
            raise HTTPException(503, 'save_failed') from None
        return public_state()


@router.get('/rgb-depth-settings')
def rgb_depth_settings_status(mode: Literal['OFF', 'HW_D2C', 'SW_D2C'] = 'HW_D2C'):
    """Preview startup registration and backups. / 정합 시작 설정과 백업을 미리 본다."""
    path=PROJECT/'install/jetrover_perception/share/jetrover_perception/config/dabai_dcw.yaml'
    directory=ROOT/'calibration/rgb-depth-settings'
    try: plan,error=rgbd_settings.preview(path,mode),None
    except (OSError,ValueError,UnicodeError) as exc: plan,error=None,str(exc) if isinstance(exc,ValueError) else 'config_unavailable'
    backups=[]
    try:
        for item in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            if item.is_symlink():continue
            record=json.loads(item.read_text());backup_id=record.get('id')
            if isinstance(backup_id,str) and len(backup_id)==32 and item.stem==backup_id:backups.append({'id':backup_id,'created_at':item.stat().st_mtime})
    except (OSError,ValueError,TypeError):backups=[]
    return {'preview':plan,'error':error,'backups':backups}


@router.post('/rgb-depth-settings/apply')
def rgb_depth_settings_apply(request: RegistrationApply):
    """Persist a reviewed camera startup mode. / 검토한 카메라 시작 모드를 저장한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return rgbd_settings.apply(PROJECT/'install/jetrover_perception/share/jetrover_perception/config/dabai_dcw.yaml',
            ROOT/'calibration/rgb-depth-settings',request.mode,request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/rgb-depth-settings/restore')
def rgb_depth_settings_restore(request: GyroRestore):
    """Restore an unchanged camera configuration. / 변경되지 않은 카메라 설정을 복원한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return rgbd_settings.restore(PROJECT/'install/jetrover_perception/share/jetrover_perception/config/dabai_dcw.yaml',
            ROOT/'calibration/rgb-depth-settings',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/corrected-background-capture')
def corrected_background_capture():
    """Record a new corrected background without commanding actuators.

    한글: 구동 명령 없이 새로운 보정 깊이 배경을 기록한다.
    """
    with lock:
        if state['running'] or state.get('odom_capture'):raise HTTPException(409,'busy')
        identifier=uuid4().hex;directory=ROOT/'calibration/backgrounds';target=directory/(identifier+'.npy')
        calibration=ROOT/'calibration/rgbd-extrinsic-active.json'
        command=['/bin/bash','-c','source /opt/ros/jazzy/setup.bash && exec /usr/bin/python3 "$1" "$2" "$3"',
                 'corrected-background',str(PROJECT/'tools/ops/calibration/capture_rgbd_background.py'),str(target),str(calibration)]
        try:
            result=subprocess.run(command,capture_output=True,text=True,timeout=25,env={**os.environ,'ROS_DOMAIN_ID':'25','OPENBLAS_NUM_THREADS':'1'})
            if result.returncode:raise ValueError('background_capture_failed')
            data=json.loads(result.stdout);return {'id':identifier,'frames':data['frames'],'valid_fraction':data['valid_fraction']}
        except (OSError,ValueError,KeyError,subprocess.TimeoutExpired):raise HTTPException(503,'background_capture_failed') from None


@router.get('/depth-source')
def depth_source_status():
    """Read the saved depth source and list recorded backgrounds.

    한글: 저장된 깊이 출처와 촬영된 배경을 읽는다.
    """
    root=ROOT/'calibration';path=root/'depth-source.json';selection={'source':'default'}
    try:
        if path.exists():
            if path.is_symlink() or path.stat().st_size>65536:raise ValueError()
            selection=json.loads(path.read_text())
            if selection.get('source') not in ('default','corrected'):raise ValueError()
    except (OSError,ValueError,TypeError):return {'source':'unknown','backgrounds':[]}
    backgrounds=[]
    try:
        for item in sorted((root/'backgrounds').glob('*.npy'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            if not item.is_symlink() and len(item.stem)==32 and all(c in '0123456789abcdef' for c in item.stem):
                backgrounds.append({'id':item.stem,'created_at':item.stat().st_mtime})
    except OSError:pass
    return {'source':selection.get('source'),'background_id':Path(selection.get('background_path','')).stem if selection.get('background_path') else None,'backgrounds':backgrounds}


@router.post('/depth-source')
def depth_source_select(request: DepthSourceSelection):
    """Save a reviewed source for the next camera launch.

    한글: 다음 카메라 실행에 사용할 확인된 출처를 저장한다.
    """
    with lock:
        if state['running'] or state.get('odom_capture'):raise HTTPException(409,'busy')
        directory=ROOT/'calibration';selection={'source':request.source}
        if request.source=='corrected':
            if not request.background_id:raise HTTPException(400,'background_required')
            background=directory/'backgrounds'/(request.background_id+'.npy')
            try:
                spec=importlib.util.spec_from_file_location('depth_source_guard',PROJECT/'src/jetrover_perception/launch/depth_source_guard.py')
                guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
                guard.validate_corrected_background(background,directory/'rgbd-extrinsic-active.json')
            except (OSError,ValueError,TypeError,AttributeError):raise HTTPException(409,'background_invalid') from None
            selection['background_path']=str(background)
        try:
            directory.mkdir(mode=0o700,parents=True,exist_ok=True)
            gyro_settings._atomic(directory/'depth-source.json',json.dumps(selection).encode(),0o600)
        except OSError:raise HTTPException(503,'save_failed') from None
        return {'source':request.source,'requires_restart':True}


@router.get('/rgb-depth-extrinsic-settings')
def rgb_depth_extrinsic_settings_status():
    """Review the candidate and backups. / 변환 후보와 백업을 검토한다."""
    path=ROOT/'calibration/rgbd-extrinsic-active.json';directory=ROOT/'calibration/rgbd-extrinsic-settings'
    try:plan,error=rgbd_extrinsic_settings.preview(path,state.get('rgbd_extrinsic') or stored_results().get('rgbd_extrinsic')),None
    except (OSError,ValueError,UnicodeError) as exc:plan,error=None,str(exc) if isinstance(exc,ValueError) else 'config_unavailable'
    backups=[]
    try:
        for item in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            if item.is_symlink():continue
            record=json.loads(item.read_text());identifier=record.get('id')
            if isinstance(identifier,str) and len(identifier)==32 and item.stem==identifier:backups.append({'id':identifier,'created_at':item.stat().st_mtime})
    except (OSError,ValueError,TypeError):backups=[]
    return {'preview':plan,'error':error,'backups':backups}


@router.post('/rgb-depth-extrinsic-settings/apply')
def rgb_depth_extrinsic_settings_apply(request: GyroApply):
    """Activate a reviewed separate-topic transform. / 검토된 별도 토픽 변환을 활성화한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return rgbd_extrinsic_settings.apply(ROOT/'calibration/rgbd-extrinsic-active.json',ROOT/'calibration/rgbd-extrinsic-settings',
            state.get('rgbd_extrinsic') or stored_results().get('rgbd_extrinsic'),request.config_hash,request.candidate_hash)
        except ValueError as exc:raise HTTPException(409,str(exc)) from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/rgb-depth-extrinsic-settings/restore')
def rgb_depth_extrinsic_settings_restore(request: GyroRestore):
    """Restore an unchanged active transform. / 변경되지 않은 활성 변환을 복원한다."""
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        try:return rgbd_extrinsic_settings.restore(ROOT/'calibration/rgbd-extrinsic-active.json',ROOT/'calibration/rgbd-extrinsic-settings',request.backup_id)
        except (ValueError,KeyError,TypeError):raise HTTPException(409,'restore_conflict') from None
        except (OSError,UnicodeError):raise HTTPException(503,'config_unavailable') from None


@router.post('/rgb-depth-extrinsic-fit')
def rgb_depth_extrinsic_fit(measurement: RgbdExtrinsicMeasurement):
    """Fit depth-optical to color-optical transform from 3D correspondences.

    한글: 3차원 대응점으로 깊이 광학 좌표에서 컬러 광학 좌표 변환을 추정한다.
    """
    with lock:
        if state['running']:raise HTTPException(409,'busy')
        pairs=[pair.model_dump() for pair in measurement.pairs]
        payload={'camera_points':[[p['camera'][axis] for axis in 'xyz'] for p in pairs],
                 'reference_points':[[p['reference'][axis] for axis in 'xyz'] for p in pairs]}
        try:
            proc=subprocess.run(['/usr/bin/python3',str(PROJECT/'tools/ops/calibration/rigid_transform.py')],input=json.dumps(payload),
                capture_output=True,text=True,timeout=5,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
            data=json.loads(proc.stdout)
            if proc.returncode or not isinstance(data.get('result'),dict):raise HTTPException(400,data.get('error','fit_failed'))
            result=data['result'];result.update({'source_frame':'depth_cam_depth_optical_frame','target_frame':'depth_cam_color_optical_frame',
                'method':'manual_3d_correspondences','device_applied':False,'independent_validation':False,'applied':False})
            state['rgbd_extrinsic']=save_result('rgbd_extrinsic',result)
        except (OSError,subprocess.TimeoutExpired,ValueError,KeyError):raise HTTPException(503,'fit_failed') from None
        return public_state()


@router.post('/rgb-depth-capture')
def rgb_depth_capture():
    """Freeze one recent synchronized image pair for user-selected points.

    한글: 사용자 대응점 선택을 위해 최근 동기 영상 한 쌍을 고정한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        path = ROOT / 'run/rgb-depth-pair.json'
        try:
            if path.stat().st_size > 6_000_000:
                raise ValueError()
            pair = json.loads(path.read_text())
            now = time.time()
            if not 0 <= now - pair['created_at'] < 5 or abs(pair['color_stamp'] - pair['depth_stamp']) > .15:
                raise ValueError()
            if not all(isinstance(pair[key], str) and 0 < len(pair[key]) <= 2_700_000 for key in ('color_jpeg','depth_jpeg')):
                raise ValueError()
            if not all(isinstance(pair[key], int) and 0 < pair[key] <= 10000 for key in ('width','height')):
                raise ValueError()
        except (OSError, ValueError, KeyError, TypeError):
            raise HTTPException(503, 'rgb_depth_pair_unavailable') from None
        pair['id'] = uuid4().hex
        pair['captured_at'] = time.time()
        state['rgb_depth_pair'] = pair
        return pair


@router.post('/rgb-depth-compare')
def rgb_depth_compare(measurement: AlignmentMeasurement):
    """Compare manually matched pixels only with matching live camera metadata.

    한글: 현재 카메라 메타데이터가 일치할 때 수동 대응 픽셀을 비교한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        info = public_state()['camera_info']
        color, depth = info.get('color'), info.get('depth')
        if not color or not depth:
            raise HTTPException(503, 'camera_info_unavailable')
        if ((color['width'], color['height'], color['frame_id']) !=
                (depth['width'], depth['height'], depth['frame_id'])):
            raise HTTPException(409, 'camera_info_mismatch')
        width, height = color['width'], color['height']
        pair = state.get('rgb_depth_pair')
        if measurement.pair_id is not None:
            if (not pair or pair.get('id') != measurement.pair_id or not 0 <= time.time() - pair['captured_at'] < 600
                    or (pair['width'], pair['height'], pair['frame_id']) != (width, height, color['frame_id'])):
                raise HTTPException(409, 'rgb_depth_pair_expired')
        points = [point.model_dump() for point in measurement.points]
        if any(p['color_x'] >= width or p['depth_x'] >= width or p['color_y'] >= height or p['depth_y'] >= height for p in points):
            raise HTTPException(400, 'alignment_out_of_bounds')
        errors = [math.hypot(p['depth_x'] - p['color_x'], p['depth_y'] - p['color_y']) for p in points]
        result = {'points': points, 'errors_px': errors,
                  'rms_px': math.sqrt(sum(e * e for e in errors) / len(errors)),
                  'width': width, 'height': height, 'frame_id': color['frame_id'],
                  'color_info_received_at': color['received_at'], 'depth_info_received_at': depth['received_at'],
                  'source': 'manual_pixel_correspondences', 'image_pair_synchronized': measurement.pair_id is not None,
                  'image_pair_time_difference_s': abs(pair['color_stamp'] - pair['depth_stamp']) if measurement.pair_id is not None else None,
                  'applied': False}
        try:
            state['rgb_depth'] = save_result('rgb_depth', result)
        except (ValueError, OSError):
            raise HTTPException(503, 'save_failed') from None
        return public_state()


@router.post('/wheel-observation')
def wheel_observation(measurement: WheelObservation):
    """Record observations of an existing forward trial; never command actuators.

    한글: 기존 전진 시험 관찰만 기록하며 구동 명령을 보내지 않는다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        result = {'environment': measurement.environment, 'trial': 'forward',
                  'wheels': measurement.model_dump(exclude={'environment'}),
                  'source': 'manual_observation', 'speed_measured': False,
                  'verified': False, 'applied': False}
        try:
            state['wheel'] = save_result('wheel', result)
        except (ValueError, OSError):
            raise HTTPException(503, 'save_failed') from None
        return public_state()


@router.post('/odometry-compare')
def odometry_compare(measurement: OdometryComparison):
    """Compare two signed observations from one trial without driving or tuning.

    한글: 한 시험의 부호 있는 두 관측값을 비교하며 주행·설정 변경은 하지 않는다.
    """
    if abs(measurement.reference) < 0.1:
        raise HTTPException(400, 'reference_too_small')
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        difference = measurement.recorded - measurement.reference
        result = {'motion': measurement.motion, 'source': measurement.source,
                  'unit': 'deg' if measurement.motion == 'rotation' else 'cm',
                  'reference': measurement.reference, 'recorded': measurement.recorded,
                  'difference': difference, 'relative_error_percent': difference / abs(measurement.reference) * 100,
                  'method': 'manual_single_trial_comparison', 'applied': False}
        try:
            state['odometry'] = save_result('odometry', result)
        except (ValueError, OSError):
            raise HTTPException(503, 'save_failed') from None
        return public_state()


@router.post('/lidar-position')
def lidar_position_candidate(measurement: LidarPositionMeasurement):
    """Record manually measured translation without assuming scan-frame orientation.

    한글: 스캔 좌표계 방향을 추정하지 않고 수동 실측 위치를 기록한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        result = {'translation_m': [measurement.x_cm / 100, measurement.y_cm / 100, measurement.z_cm / 100],
                  'parent_frame': 'base_link', 'child_frame': 'lidar_link',
                  'source': 'manual_measurement', 'rotation_verified': False,
                  'scan_frame_verified': False, 'applied': False}
        try:
            state['lidar'] = save_result('lidar', result)
        except (ValueError, OSError):
            raise HTTPException(503, 'save_failed') from None
        return public_state()


@router.post('/footprint')
def footprint_candidate(measurement: FootprintMeasurement):
    """Save an explicitly measured rectangular footprint candidate.

    한글: 명시적으로 실측한 사각형 외형 후보를 저장한다.
    """
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        front, rear, left, right = (getattr(measurement, field) / 100 for field in
                                    ('front_cm', 'rear_cm', 'left_cm', 'right_cm'))
        result = {'polygon_m': [[front, left], [front, -right], [-rear, -right], [-rear, left]],
                  'measurements_cm': measurement.model_dump(), 'frame_id': 'base_footprint',
                  'source': 'manual_measurement', 'safety_margin_included': None, 'applied': False}
        try:
            state['footprint'] = save_result('footprint', result)
        except (ValueError, OSError):
            raise HTTPException(503, 'save_failed') from None
        return public_state()


@router.post('/camera/capture')
def camera_capture():
    """Capture a fresh lossless color frame. / 최신 무손실 컬러 프레임을 수집한다."""
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        if len(state['captures']) >= 40:
            raise HTTPException(400, 'capture_limit')
        path = ROOT / 'run/camera-calibration.png'
        try:
            age = time.time() - path.stat().st_mtime
            if not 0 <= age < 5:
                raise ValueError()
            data = path.read_bytes()
            if not data.startswith(b'\x89PNG\r\n\x1a\n') or len(data) > 4_000_000:
                raise ValueError()
        except (OSError, ValueError):
            raise HTTPException(503, 'camera_unavailable') from None
        digest = hashlib.sha256(data).hexdigest()
        if any(p.stem == digest for p in state['captures']):
            raise HTTPException(409, 'duplicate_frame')
        destination = capture_dir / (digest + '.png')
        destination.write_bytes(data)
        state['captures'].append(destination)
        state['error'] = None
        return public_state()


@router.post('/camera/reset')
def camera_reset():
    """Clear only this process's captured images. / 이 프로세스가 촬영한 영상만 삭제한다."""
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        for path in state['captures']:
            path.unlink(missing_ok=True)
        state['captures'] = []
        state['error'] = None
        return public_state()


@router.post('/camera/compute')
def camera_compute(board: Board):
    """Start candidate computation using captured images. / 수집된 영상으로 후보 계산을 시작한다."""
    with lock:
        if state['running']:
            raise HTTPException(409, 'busy')
        if len(state['captures']) < 8:
            raise HTTPException(400, 'image_count')
        state['error'] = None
        state['running'] = 'camera'
        executor.submit(run_job, 'camera', {'columns': board.columns, 'rows': board.rows, 'square_m': board.square_mm / 1000})
        return public_state()
