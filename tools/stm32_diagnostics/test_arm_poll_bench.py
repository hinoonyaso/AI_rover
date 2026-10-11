import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import arm_poll_bench as b  # noqa: E402


def servos(hz, ok_ratio=1.0, req_ratio=1.0, lat_max=15.0, duration=30.0):
    out = {}
    for sid in (1, 2, 3, 4, 5, 10):
        req = hz / 6 * duration * req_ratio
        out[sid] = {'requests': req, 'replies': req * ok_ratio, 'misses': 0, 'failed': 0, 'unmatched': 0,
                    'requests_per_s': req / duration, 'replies_per_s': req * ok_ratio / duration,
                    'mean_latency_ms': 6.0, 'max_latency_ms': lat_max, 'mean_period_s': 6 / hz, 'max_period_s': 6 / hz * 1.5}
    return out


def row(hz, imu_n=1545, imu_gap=0.035, odom_gap=0.04, **kw):
    return {'hz': hz, 'duration': 30.0, 'servos': servos(hz, **kw),
            'imu': {'n': imu_n, 'max_gap_s': imu_gap, 'mean_gap_s': 0.02},
            'odom': {'n': 1500, 'max_gap_s': odom_gap, 'mean_gap_s': 0.02}, 'serial_bytes_per_s_est': 100.0}


class Judge(unittest.TestCase):
    def test_equal_or_better_than_baseline_is_adopted_even_with_baseline_losses(self):
        base = row(5, ok_ratio=0.95)          # the bus loses 5 % even at the baseline rate
        ok, why = b.judge_rate(base, row(20, ok_ratio=0.95))
        self.assertTrue(ok, why)

    def test_success_ratio_clearly_worse_than_baseline_blocks(self):
        ok, why = b.judge_rate(row(5, ok_ratio=0.97), row(20, ok_ratio=0.88))
        self.assertFalse(ok)
        self.assertTrue(any('success ratio' in w for w in why))

    def test_spread_between_identical_windows_is_tolerated(self):
        self.assertTrue(b.judge_rate(row(5, ok_ratio=0.97), row(5, ok_ratio=0.93))[0])   # 4 points, like 5 Hz vs 5 Hz

    def test_hopeless_loss_blocks_even_if_baseline_is_equally_bad(self):
        ok, why = b.judge_rate(row(5, ok_ratio=0.7), row(20, ok_ratio=0.7))
        self.assertFalse(ok)
        self.assertTrue(any('without a reading' in w for w in why))

    def test_timer_that_cannot_keep_up_blocks(self):
        ok, why = b.judge_rate(row(5), row(30, req_ratio=0.8))
        self.assertFalse(ok)
        self.assertTrue(any('timer cannot keep up' in w for w in why))

    def test_latency_jump_blocks(self):
        ok, why = b.judge_rate(row(5), row(20, lat_max=300.0))
        self.assertFalse(ok)
        self.assertTrue(any('latency' in w for w in why))

    def test_imu_rate_loss_or_gap_blocks_adoption(self):
        self.assertFalse(b.judge_rate(row(5), row(20, imu_n=1500))[0])        # -2.9 %
        self.assertTrue(b.judge_rate(row(5), row(20, imu_n=1535))[0])         # -0.6 % is inside 1 %
        ok, why = b.judge_rate(row(5), row(20, imu_gap=0.20))
        self.assertFalse(ok)
        self.assertTrue(any('IMU max gap' in w for w in why))

    def test_loop_delay_proxy_blocks_adoption(self):
        ok, why = b.judge_rate(row(5), row(20, odom_gap=0.25))
        self.assertFalse(ok)
        self.assertTrue(any('odom_raw' in w for w in why))

    def test_no_stats_is_never_adopted(self):
        empty = copy.deepcopy(row(20))
        empty['servos'] = {}
        self.assertFalse(b.judge_rate(row(5), empty)[0])

    def test_gap_helper(self):
        g = b.gaps([0.0, 0.1, 0.2, 0.5])
        self.assertAlmostEqual(g['max_gap_s'], 0.3)
        self.assertEqual(b.gaps([])['n'], 0)


if __name__ == '__main__':
    unittest.main()
