"""Supervise a simulation-only Gazebo subprocess. / Gazebo 시뮬레이션 전용 하위 프로세스를 관리한다."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from uuid import uuid4

from mission_contract import ContractError


class GazeboWorker:
    """Own at most one isolated Gazebo trial process. / 격리 Gazebo 시험 프로세스를 최대 하나만 관리한다."""
    def __init__(self, manager, auto_start=True):
        self.manager = manager
        self.auto_start = auto_start
        self.process = None
        self.mission_id = None
        self.output = None
        self.cancel_sent = False
        self.pending_result = None
        self.kind = None
        self.read_offset = 0

    def _launch(self):
        env = os.environ.copy()
        for key in ('ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER', 'FASTRTPS_DEFAULT_PROFILES_FILE',
                    'FASTDDS_DEFAULT_PROFILES_FILE', 'CYCLONEDDS_URI', 'PYTHONPATH',
                    'FASTDDS_BUILTIN_TRANSPORTS', 'ROS_LOCALHOST_ONLY'):
            env.pop(key, None)
        profile = Path(__file__).resolve().parents[2] / 'mission/fastdds-loopback.xml'
        env.update({'ROS_DOMAIN_ID': '31', 'ROS_AUTOMATIC_DISCOVERY_RANGE': 'SUBNET',
                    'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp', 'GZ_IP': '127.0.0.1',
                    'FASTRTPS_DEFAULT_PROFILES_FILE': str(profile)})
        script = Path(__file__).resolve().parents[2] / ('mission/gazebo_managed_session.py' if self.auto_start else 'mission/gazebo_nav_trial.py')
        if self.auto_start:
            env['GZ_PARTITION'] = 'jetinspect_dashboard_' + uuid4().hex
            command = 'set -e; source /opt/ros/jazzy/setup.bash; source "$1"; exec /usr/bin/python3 "$2" "$3"'
        else:
            command = 'set -e; source /opt/ros/jazzy/setup.bash; source "$1"; args=(--managed); if [ "$3" = inspect_stack_light ]; then args+=(--inspect); fi; if [ "$3" = return_to_start ]; then args+=(--return); fi; exec /usr/bin/python3 "$2" "${args[@]}"'
        setup = Path(__file__).resolve().parents[3] / 'install/setup.bash'
        self.output = tempfile.TemporaryFile(mode='w+t', encoding='utf-8')
        self.process = subprocess.Popen(['/bin/bash', '-c', command, 'gazebo-worker', str(setup), str(script), self.kind],
                                        env=env, stdin=subprocess.PIPE, stdout=self.output,
                                        stderr=subprocess.STDOUT, text=True, close_fds=True)

    def tick(self):
        """Advance supervision once without blocking on navigation. / 주행을 기다리지 않고 감독을 한 번 수행한다."""
        if self.pending_result is not None:
            result = self.pending_result
            try:
                self.manager.finish_gazebo(self.mission_id, result['state'], result['reason'],
                                           result.get('colors'), result.get('diagnostics'))
            except ContractError as error:
                if error.code != 'stale_result':
                    raise
            self.pending_result = None
            self.mission_id = None
            return
        if self.process is None:
            active = self.manager.active_gazebo()
            if active is None:
                return
            if active['state'] == 'cancel_requested':
                self.manager.finish_gazebo(active['id'], 'canceled', 'canceled_before_launch')
                return
            if active['state'] != 'queued':
                return
            self.manager.begin_gazebo(active['id'], active['version'], preparing=self.auto_start)
            self.mission_id = active['id']
            self.kind = active['kind']
            self.read_offset = 0
            try:
                self._launch()
            except OSError:
                if self.output:
                    self.output.close()
                    self.output = None
                self.mission_id = None
                self.manager.finish_gazebo(active['id'], 'interrupted', 'gazebo_worker_unavailable')
            return
        # pread does not move the file offset shared with the child writer.
        # 한글: pread는 하위 프로세스와 공유하는 파일 오프셋을 변경하지 않는다.
        while True:
            chunk = os.pread(self.output.fileno(), 65536, self.read_offset)
            complete = chunk.rfind(b'\n')
            if complete < 0:
                break
            for line in chunk[:complete + 1].splitlines():
                if line == b'MISSION_STAGE gazebo_navigation':
                    self.manager.mark_gazebo_navigation(self.mission_id)
                if line == b'MISSION_STAGE gazebo_inspection':
                    self.manager.mark_gazebo_inspection(self.mission_id)
                for stage in (b'gazebo_returning', b'gazebo_paused', b'gazebo_navigation'):
                    if line == b'MISSION_STAGE ' + stage:
                        self.manager.mark_gazebo_motion(self.mission_id, stage.decode())
            self.read_offset += complete + 1
            if len(chunk) < 65536:
                break
        row = self.manager.get(self.mission_id)
        if row['state'] == 'cancel_requested' and not self.cancel_sent:
            self.request_stop()
        if self.process.poll() is None:
            return
        self.output.seek(0)
        result = None
        for line in self.output:
            # Keep bounded diagnostic evidence after the temporary child output is closed.
            # 한글: 하위 프로세스 임시 출력이 닫힌 뒤에도 제한된 진단 근거를 남긴다.
            if line.startswith('INSPECTION_DIAGNOSTIC '):
                print(f'mission={self.mission_id} {line.strip()[:1024]}', flush=True)
            if line.startswith('MISSION_RESULT '):
                try:
                    result = json.loads(line[len('MISSION_RESULT '):])
                except ValueError:
                    pass
        self.process.stdin.close()
        self.output.close()
        self.output = None
        self.process = None
        self.cancel_sent = False
        if not isinstance(result, dict) or result.get('state') not in ('succeeded', 'failed', 'canceled', 'interrupted'):
            result = {'state': 'interrupted', 'reason': 'gazebo_result_unconfirmed'}
        self.pending_result = {'state': result['state'], 'reason': str(result.get('reason', 'unknown'))[:128],
                               'colors': result.get('colors'), 'diagnostics': result.get('diagnostics')}
        # Retain the result until it is persisted; a transient DB failure must not lose it.
        # 한글: 일시적 DB 오류로 결과가 유실되지 않도록 저장될 때까지 보관한다.
        self.tick()

    def send_motion(self, mission_id, command):
        """Forward pause/resume to the running trial of this mission. / 해당 임무 시험에 일시정지·재개 전달.

        Returns False when no matching mission process is running.
        한글: 해당 임무의 프로세스가 없으면 False를 반환한다.
        """
        if command not in ('pause', 'resume'):
            raise ValueError('invalid command')
        if self.process is None or self.mission_id != mission_id or self.cancel_sent or self.process.poll() is not None:
            return False
        try:
            self.process.stdin.write(command + '\n')
            self.process.stdin.flush()
            return True
        except (BrokenPipeError, OSError, ValueError):
            return False

    def request_stop(self):
        """Request child cancellation without reporting success. / 취소 완료로 가정하지 않고 하위 프로세스에 요청한다."""
        if self.process is not None and not self.cancel_sent:
            self.cancel_sent = True
            try:
                self.process.stdin.write('cancel\n')
                self.process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

    def close(self):
        """Stop supervision and request cancellation on shutdown. / 종료 시 취소를 요청하고 감독을 중지한다."""
        if self.process is None:
            return
        self.request_stop()
        try:
            self.process.wait(timeout=25 if self.auto_start else 12)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=10 if self.auto_start else 3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process.stdin.close()
        self.output.close()
        self.process = None
        self.output = None
