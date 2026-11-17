#!/usr/bin/python3
"""Synthetic hand-eye tests without hardware. / 하드웨어 없는 핸드아이 합성 시험."""
import unittest
import cv2
import numpy as np
from hand_eye import fit_hand_eye


def pose(vector, translation):
    result = np.eye(4)
    result[:3,:3] = cv2.Rodrigues(np.array(vector, dtype=float))[0]
    result[:3,3] = translation
    return result


class HandEyeTests(unittest.TestCase):
    def test_recovers_fixed_camera_transform(self):
        x = pose([.2,-.1,.3],[.05,-.1,.2])
        y = pose([-.3,.15,.1],[.4,.1,.8])
        positions = [([.2,.1,0],[.1,.2,.1]), ([-.3,.2,.1],[.2,.0,.2]),
                     ([.1,-.25,.3],[.3,.1,.2]), ([.35,.2,-.2],[.0,.2,.3]),
                     ([-.1,-.2,-.3],[.2,.3,.2]), ([.2,-.3,-.1],[.1,.2,.4])]
        pairs = []
        for rot, trans in positions:
            a = pose(rot, trans)
            b = np.linalg.inv(x) @ np.linalg.inv(a) @ y
            pairs.append({'base_T_link4':a.tolist(), 'camera_T_target':b.tolist()})
        result = fit_hand_eye(pairs)
        np.testing.assert_allclose(result['link4_T_camera'],x,atol=1e-6)
        self.assertLess(result['translation_rms_m'], 1e-6)
        self.assertLess(result['rotation_max_rad'], 1e-6)

    def test_degenerate_and_nonrigid_are_rejected(self):
        identity = np.eye(4).tolist()
        pairs = [{'base_T_link4':identity, 'camera_T_target':identity}] * 5
        with self.assertRaisesRegex(ValueError, 'insufficient_rotation_diversity'): fit_hand_eye(pairs)
        bad = np.eye(4); bad[0,0]=2
        with self.assertRaisesRegex(ValueError, 'invalid_pose'):
            fit_hand_eye([{'base_T_link4':bad.tolist(), 'camera_T_target':identity}]*5)

if __name__ == '__main__': unittest.main()
