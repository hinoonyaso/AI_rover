"""goal_clearance unit tests (no ROS). / goal_clearance 단위 시험(ROS 불필요)."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from goal_clearance import MapClearance, scan_clearance  # noqa: E402
import math  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


class GridTests(unittest.TestCase):
    def test_live_grid_rows_start_at_smallest_y(self):
        # 10x10 grid, 0.1 m cells, origin (0, 0); one lethal cell at column 2, row 7 -> centre (0.25, 0.75).
        data = [0] * 100
        data[7 * 10 + 2] = 100
        data[0] = 99   # inscribed is not an obstacle / 내접 비용은 장애물이 아니다
        c = MapClearance.from_grid(10, 10, 0.1, (0.0, 0.0), data)
        self.assertAlmostEqual(c.clearance(0.25, 0.75), 0.0)
        self.assertAlmostEqual(c.clearance(0.25, 0.35), 0.4)
        self.assertEqual(c.check(0.25, 0.25)[0], True)    # 0.5 m
        self.assertEqual(c.check(0.25, 0.45)[0], False)   # 0.3 m

    def test_empty_grid_is_clear(self):
        self.assertTrue(MapClearance.from_grid(3, 3, 0.1, (0, 0), [0] * 9).check(0.1, 0.1)[0])


class ScanTests(unittest.TestCase):
    def test_rear_sector_is_ignored_and_front_counts(self):
        # 360 beams, 1 deg each from -pi; a 0.2 m return straight behind (blind) and 0.6 m in front.
        ranges = [math.inf] * 360
        ranges[0] = 0.2      # angle -pi: behind the robot, arm-occluded / 팔에 가린 뒤쪽
        ranges[180] = 0.6    # angle 0: ahead / 앞
        self.assertAlmostEqual(scan_clearance(ranges, -math.pi, math.radians(1)), 0.6)
        ranges[200] = 0.3    # 20 deg left of ahead / 앞 왼쪽
        self.assertAlmostEqual(scan_clearance(ranges, -math.pi, math.radians(1)), 0.3)


class SavedMapTests(unittest.TestCase):
    def test_gazebo_return_start_is_clear_and_old_spawn_is_not(self):
        # Matches troubleshooting/065: the wall-side spawn deadlocked, the clear spawn works.
        # 한글: 065와 일치 — 벽 옆 시작점은 너무 가깝고, 여유 시작점은 통과한다.
        c = MapClearance(ROOT / 'maps/lap2_20261005.yaml')
        self.assertTrue(c.check(1.30, 0.40)[0])
        self.assertFalse(c.check(1.02, 0.37)[0])


if __name__ == '__main__':
    unittest.main()
