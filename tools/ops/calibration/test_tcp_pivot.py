#!/usr/bin/python3
"""Synthetic TCP pivot calibration tests. / TCP 접점 보정 합성 시험."""
import unittest
import numpy as np
import cv2
from tcp_pivot import fit_tcp

class TcpTests(unittest.TestCase):
    def test_recovers_tcp_and_pivot(self):
        tip=np.array([.04,-.02,.15]); pivot=np.array([.4,.1,.3]); poses=[]
        for v in ([0,0,0],[.3,.1,0],[-.2,.3,.1],[.1,-.3,.2],[.3,.2,-.3],[0,.4,.3]):
            m=np.eye(4); m[:3,:3]=cv2.Rodrigues(np.array(v,dtype=float))[0]; m[:3,3]=pivot-m[:3,:3]@tip; poses.append(m.tolist())
        result=fit_tcp(poses)
        np.testing.assert_allclose(result['tcp_gripper_m'],tip,atol=1e-7)
        np.testing.assert_allclose(result['pivot_base_m'],pivot,atol=1e-7)
        self.assertLess(result['rms_m'],1e-7)

    def test_identical_poses_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'insufficient_pose_diversity'):fit_tcp([np.eye(4).tolist()]*5)

if __name__ == '__main__': unittest.main()
