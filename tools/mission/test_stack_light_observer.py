"""Unit tests for observation freshness. / 영상 관측의 최신성 단위 시험."""
import unittest

import numpy as np

from stack_light_observer import ObservationWindow, fixture_regions


class ObservationTests(unittest.TestCase):
    def test_finds_shifted_three_color_simulation_fixture(self):
        image = np.zeros((360, 640, 3), dtype=np.uint8)
        image[50:80, 205:235] = (255, 0, 0)
        image[100:130, 210:240] = (47, 47, 0)
        image[150:180, 215:245] = (0, 255, 0)
        regions = fixture_regions(image)
        self.assertIsNotNone(regions)
        self.assertEqual(regions['red'], (214, 59, 12, 12))
        image[100:130, 210:240] = 0
        self.assertIsNone(fixture_regions(image))

    def test_inverted_fixture_observation(self):
        image = np.zeros((360, 640, 3), dtype=np.uint8)
        image[50:80, 205:235] = (47, 0, 0)
        image[100:130, 210:240] = (255, 255, 0)
        image[150:180, 215:245] = (0, 47, 0)
        window = ObservationWindow()
        for index in range(5):
            timestamp = index * .5 + 1
            window.add(image, timestamp, timestamp, timestamp)
        self.assertEqual([window.result(3)[name]['state'] for name in ('red', 'yellow', 'green')],
                         ['off', 'on', 'off'])

    def test_diagnostics_filter_untrusted_reasons(self):
        window = ObservationWindow()
        window.received = 4
        window.invalid_time = 1
        diagnostic = window.diagnostics({'red': "'red'", 'yellow': 'ambiguous_brightness',
                                         'unrelated': 'private information'})
        self.assertEqual(diagnostic['received'], 4)
        self.assertEqual(diagnostic['invalid_time'], 1)
        self.assertEqual(diagnostic['color_reasons'],
                         {'red': 'fixture_not_found', 'yellow': 'ambiguous_brightness'})

    def test_stale_or_repeated_stamp_clears_window(self):
        window = ObservationWindow()
        image = np.zeros((360, 640, 3), dtype=np.uint8)
        window.add(image, 1, 1, 10)
        self.assertEqual(len(window.frames), 1)
        window.add(image, 1, 1.1, 10.4)
        self.assertEqual(window.frames, [])
        window.add(image, 2, 3, 11)
        self.assertEqual(window.frames, [])
        self.assertEqual(window.received, 3)
        self.assertEqual(window.invalid_time, 2)

    def test_long_reception_gap_restarts_window(self):
        window = ObservationWindow()
        image = np.zeros((360, 640, 3), dtype=np.uint8)
        window.add(image, 1, 1, 10)
        window.add(image, 2, 2, 11)
        self.assertEqual(len(window.frames), 1)
        self.assertEqual(window.frames[0][0], 11)
        self.assertEqual(window.gap_resets, 1)
        self.assertTrue(all(value['state'] == 'unknown' for value in window.result(11).values()))


if __name__ == '__main__':
    unittest.main()
