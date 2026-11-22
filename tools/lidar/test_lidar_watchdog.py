"""Watchdog logic tests with fake driver processes; no ROS or LiDAR needed.

한글: 가짜 드라이버 프로세스로 감시 로직을 시험한다. ROS·LiDAR 불필요.
"""
import threading
import time
import unittest

from lidar_watchdog import decide, run, ScanClock


class DecideTests(unittest.TestCase):
    def test_states(self):
        self.assertEqual(decide(0, None, 10, 15, 5), 'wait')
        self.assertEqual(decide(0, None, 16, 15, 5), 'no_start')
        self.assertEqual(decide(0, 1.0, 16, 15, 5), 'ok')
        self.assertEqual(decide(0, 6.0, 16, 15, 5), 'stalled')


class RunTests(unittest.TestCase):
    def test_stalled_startup_is_restarted_then_gives_up(self):
        clock, stop = ScanClock(), threading.Event()
        began = time.monotonic()
        code = run(['sleep', '30'], clock, start_timeout=0.5, gap_timeout=0.5, max_restarts=2,
                   stop_event=stop, settle=0.05)
        self.assertEqual(code, 1)
        self.assertLess(time.monotonic() - began, 10)  # children were killed, not waited for

    def test_recovers_when_second_start_publishes(self):
        clock, stop = ScanClock(), threading.Event()
        runs = []

        def feeder():
            # Second driver run "publishes" scans; the first never does.
            while not stop.is_set():
                if len(runs) >= 2:
                    clock.tick()
                time.sleep(0.05)
        import lidar_watchdog
        original = lidar_watchdog.subprocess.Popen

        def counting_popen(*args, **kwargs):
            runs.append(1)
            return original(*args, **kwargs)
        lidar_watchdog.subprocess.Popen = counting_popen
        threading.Thread(target=feeder, daemon=True).start()
        result = {}
        worker = threading.Thread(target=lambda: result.setdefault('code', run(
            ['sleep', '30'], clock, start_timeout=0.5, gap_timeout=0.5, max_restarts=3,
            stop_event=stop, settle=0.05)))
        try:
            worker.start()
            time.sleep(2.0)
            self.assertEqual(len(runs), 2, 'one restart after the stalled start')
            self.assertGreater(clock.count, 5)
            stop.set()
            worker.join(10)
        finally:
            lidar_watchdog.subprocess.Popen = original
        self.assertEqual(result['code'], 0)

    def test_driver_exit_is_restarted(self):
        clock, stop = ScanClock(), threading.Event()
        code = run(['true'], clock, start_timeout=5, gap_timeout=5, max_restarts=1,
                   stop_event=stop, settle=0.05)
        self.assertEqual(code, 1)


if __name__ == '__main__':
    unittest.main()
