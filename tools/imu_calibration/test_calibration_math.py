"""Verify bias candidate and rejection paths. / bias 후보 계산과 거부 경로 검증."""
import unittest
from calibration_math import gyro_candidate, accel_pose_summary, accel_candidate


class GyroCandidateTests(unittest.TestCase):
    def test_existing_bias_is_added_to_residual(self):
        result = gyro_candidate([[0.01, -0.02, 0.03]] * 20, [0.2, 0.1, -0.1], [0.2, 0.1, -0.1])
        for actual, expected in zip(result['candidate'], [0.21, 0.08, -0.07]):
            self.assertAlmostEqual(actual, expected)
        self.assertFalse(result['applied'])

    def test_rejects_insufficient_nonfinite_motion_and_changed_bias(self):
        for rows, before, after, reason in [
            ([[0, 0, 0]] * 9, [0]*3, [0]*3, 'insufficient_samples'),
            ([[float('nan'), 0, 0]] * 10, [0]*3, [0]*3, 'invalid_vector'),
            ([[0.1 if i % 2 else -0.1, 0, 0] for i in range(20)], [0]*3, [0]*3, 'not_stationary'),
            ([[0, 0, 0]] * 10, [0]*3, [1, 0, 0], 'bias_changed')]:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                gyro_candidate(rows, before, after)


class AccelerometerTests(unittest.TestCase):
    def test_six_pose_offsets_and_scale(self):
        poses = {}
        offset = [0.3, -0.2, 0.1]
        scale = [1.05, 0.95, 1.02]
        for index, axis in enumerate('xyz'):
            for sign_name, sign in [('plus', 1), ('minus', -1)]:
                sample = offset.copy()
                sample[index] += sign * 9.80665 / scale[index]
                name = axis + '_' + sign_name
                poses[name] = {**accel_pose_summary([sample] * 60, name), 'frame_id': 'imu_link', 'source_id': 'fake', 'current_offset_m_s2':[0,0,0], 'current_scale':[1,1,1]}
        result = accel_candidate(poses)
        for actual, expected in zip(result['offset_m_s2'], offset): self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(result['scale'], scale): self.assertAlmostEqual(actual, expected)
        self.assertFalse(result['applied'])
        poses['x_plus']['source_id'] = 'another'
        with self.assertRaisesRegex(ValueError, 'source_changed'): accel_candidate(poses)

    def test_existing_calibration_is_composed_and_must_match_all_poses(self):
        poses = {}
        for index, axis in enumerate('xyz'):
            for sign_name, sign in [('plus',1),('minus',-1)]:
                vector=[0.2,0.2,0.2]; vector[index] += sign * 9.80665 / 1.1
                name=axis+'_'+sign_name
                poses[name]={**accel_pose_summary([vector]*60,name),'frame_id':'imu_link','source_id':'fake',
                             'current_offset_m_s2':[1.,1.,1.], 'current_scale':[1.25,1.25,1.25]}
        result=accel_candidate(poses)
        self.assertAlmostEqual(result['offset_m_s2'][0],1.16)
        self.assertAlmostEqual(result['scale'][0],1.375)
        poses['x_plus']['current_scale']=[1.,1.,1.]
        with self.assertRaisesRegex(ValueError,'accel_settings_changed'):accel_candidate(poses)

    def test_rejects_wrong_pose_and_movement(self):
        with self.assertRaisesRegex(ValueError, 'incorrect_pose'):
            accel_pose_summary([[0,0,9.8]] * 60, 'x_plus')
        with self.assertRaisesRegex(ValueError, 'not_stationary'):
            accel_pose_summary([[0,0,9.8 + (0.3 if i%2 else -0.3)] for i in range(60)], 'z_plus')
        with self.assertRaisesRegex(ValueError, 'incomplete_poses'): accel_candidate({})


if __name__ == '__main__':
    unittest.main()
