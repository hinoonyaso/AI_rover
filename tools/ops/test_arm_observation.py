"""Test servo freshness and runtime mapping. / 서보 신선도와 런타임 대응을 검증한다."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from arm_observation import valid_mapping, arm_observation, fresh_arm_observation

class ArmObservationTests(unittest.TestCase):
    def test_mapping_must_be_complete_and_unique(self):
        self.assertEqual(valid_mapping(['joint1', 'r_joint'], [1, 10]), {'joint1': 1, 'r_joint': 10})
        for names, ids in [(['joint1'], []), (['joint1', 'joint1'], [1, 2]), (['a', 'b'], [1, 1]), (['a'], [True])]:
            self.assertEqual(valid_mapping(names, ids), {})

    def test_stale_servo_and_api_delay_are_not_fresh(self):
        mapping = {'joint1': 1, 'r_joint': 10}
        info = arm_observation(mapping, 99, {'joint1': 0.2, 'r_joint': 0.4}, 99.9, {1: 0.2, 10: -1}, 99.9, 100)
        self.assertTrue(info['joints']['joint1']['fresh'])
        self.assertFalse(info['joints']['r_joint']['fresh'])
        result = fresh_arm_observation({'timestamp': 100, 'arm': info}, 101.4)
        self.assertFalse(result['joints']['joint1']['fresh'])
        self.assertEqual(fresh_arm_observation({'timestamp': 100, 'arm': info}, 104)['joints'], {})
        self.assertFalse(arm_observation(mapping, 80, {}, 0, {}, 0, 100)['mapping_confirmed'])

    def test_invalid_measurement_never_becomes_fresh(self):
        info = arm_observation({'joint1': 1}, 99, {'joint1': float('nan')}, 99, {1: 0.1}, 99, 100)
        self.assertFalse(info['joints']['joint1']['fresh'])
        self.assertIsNone(info['joints']['joint1']['position_rad'])

if __name__ == '__main__':
    unittest.main()
