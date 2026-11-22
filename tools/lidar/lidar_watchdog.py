#!/usr/bin/env python3
"""Run the RPLIDAR driver and restart it when /scan never starts or stops.

The installed rplidar_ros 2.1.0 / SDK 1.12.0 can block forever in its startup handshake
(``checkMotorCtrlSupport -> waitfordata`` waiting for a 7-byte header with 6 bytes queued,
troubleshooting/062); restarting the driver recovers it. This wrapper launches the driver
as a child process group, watches /scan, and restarts it a bounded number of times.
It never moves the robot (the LiDAR motor spins as in normal operation).

한글: RPLIDAR 드라이버를 실행하고 /scan이 시작되지 않거나 끊기면 재시작한다. 설치된 드라이버는
시작 핸드셰이크에서 무한 대기할 수 있으며(062) 재시작으로 복구된다. 드라이버를 자식 프로세스
그룹으로 실행해 /scan을 감시하고 정해진 횟수까지만 재시작한다. 로봇을 움직이지 않는다.
"""
import argparse
import os
import signal
import subprocess
import sys
import threading
import time

DEFAULT_COMMAND = ['ros2', 'launch', 'jetrover_bringup', 'lidar.launch.py']


class ScanClock:
    """Thread-safe time of the last /scan message. / 마지막 /scan 수신 시각."""

    def __init__(self):
        self.lock = threading.Lock()
        self.last = None
        self.count = 0

    def tick(self, _msg=None):
        with self.lock:
            self.last = time.monotonic()
            self.count += 1

    def reset(self):
        with self.lock:
            self.last = None
            self.count = 0

    def age(self):
        with self.lock:
            return None if self.last is None else time.monotonic() - self.last


def decide(started_at, scan_age, now, start_timeout, gap_timeout):
    """Return 'ok', 'wait', 'no_start' or 'stalled' for the current driver run.

    한글: 현재 드라이버 실행 상태를 판정한다(정상·대기·시작 실패·중단).
    """
    if scan_age is None:
        return 'no_start' if now - started_at > start_timeout else 'wait'
    return 'stalled' if scan_age > gap_timeout else 'ok'


def stop_child(child, grace=5.0):
    """Stop the whole driver process group. / 드라이버 프로세스 그룹 전체를 멈춘다."""
    if child.poll() is not None:
        return
    try:
        os.killpg(child.pid, signal.SIGINT)
        child.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=grace)
    except ProcessLookupError:
        pass


def log(message):
    print(f'[lidar_watchdog] {message}', flush=True)


def run(command, clock, *, start_timeout, gap_timeout, max_restarts, stop_event, settle=2.0,
        healthy_reset=60.0):
    """Supervise the driver; return the process exit code for systemd.

    한글: 드라이버를 감독하고 systemd에 돌려줄 종료 코드를 반환한다.
    """
    restarts = 0
    while not stop_event.is_set():
        clock.reset()
        child = subprocess.Popen(command, start_new_session=True)
        started = time.monotonic()
        log(f'driver started pid={child.pid} (restart {restarts}/{max_restarts})')
        reason = None
        while not stop_event.is_set():
            if child.poll() is not None:
                reason = f'driver exited code={child.returncode}'
                break
            state = decide(started, clock.age(), time.monotonic(), start_timeout, gap_timeout)
            if state == 'no_start':
                reason = f'no /scan within {start_timeout:.0f}s (driver stall, or LiDAR power/cable)'
                break
            if state == 'stalled':
                reason = f'/scan stopped for {clock.age():.1f}s'
                break
            if state == 'ok' and restarts and time.monotonic() - started > healthy_reset:
                # A long healthy run means a later failure is a new incident.
                # 한글: 충분히 정상 동작했으면 이후 장애는 새 사건으로 보고 횟수를 초기화한다.
                log(f'scan healthy for {healthy_reset:.0f}s, restart counter reset')
                restarts = 0
            time.sleep(0.2)
        stop_child(child)
        if stop_event.is_set():
            return 0
        if restarts >= max_restarts:
            log(f'giving up after {restarts} restarts: {reason}')
            return 1
        restarts += 1
        log(f'restarting driver: {reason}')
        time.sleep(settle)  # let the serial port close / 시리얼 포트가 닫힐 시간을 준다
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start-timeout', type=float, default=15.0)
    parser.add_argument('--gap-timeout', type=float, default=5.0)
    parser.add_argument('--max-restarts', type=int, default=3)
    parser.add_argument('command', nargs=argparse.REMAINDER,
                        help='driver command (default: ros2 launch jetrover_bringup lidar.launch.py)')
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    command = command or DEFAULT_COMMAND

    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan

    from rclpy.executors import SingleThreadedExecutor

    # Own signal handling: rclpy's default SIGINT handler would tear down the context while the
    # executor thread is spinning (std::terminate / core dump on systemctl stop).
    # 한글: rclpy 기본 신호 처리기가 스핀 중 컨텍스트를 끊어 종료 시 코어 덤프가 나므로 직접 처리한다.
    rclpy.init(signal_handler_options=rclpy.signals.SignalHandlerOptions.NO)
    node = rclpy.create_node('lidar_watchdog')
    clock = ScanClock()
    node.create_subscription(LaserScan, '/scan', clock.tick, qos_profile_sensor_data)
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    spinner = threading.Thread(target=executor.spin, daemon=True)
    spinner.start()
    stop_event = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop_event.set())
    try:
        code = run(command, clock, start_timeout=args.start_timeout, gap_timeout=args.gap_timeout,
                   max_restarts=args.max_restarts, stop_event=stop_event)
    finally:
        executor.shutdown(timeout_sec=2.0)
        spinner.join(3.0)
        node.destroy_node()
        rclpy.try_shutdown()
    return code


if __name__ == '__main__':
    sys.exit(main())
