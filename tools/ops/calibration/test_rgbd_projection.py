"""Synthetic tests for raw depth reprojection. / 원본 깊이 투영 합성 시험."""
import unittest
import numpy as np
from rgbd_projection import project

class ProjectionTests(unittest.TestCase):
    def test_identity_translation_and_holes(self):
        d=np.zeros((3,4),np.uint16);d[1,1]=1000;k=[[100,0,0],[0,100,0],[0,0,1]]
        identity=project(d,k,[0]*5,k,[0]*5,np.eye(3),[0,0,0],(4,3))
        self.assertEqual(identity[1,1],1000);self.assertEqual(np.count_nonzero(identity),1)
        shifted=project(d,k,[0]*5,k,[0]*5,np.eye(3),[.01,0,0],(4,3))
        self.assertEqual(shifted[1,2],1000);self.assertEqual(shifted[1,1],0)
    def test_reject_invalid_rotation(self):
        with self.assertRaisesRegex(ValueError,'invalid_calibration'):
            project(np.zeros((2,2),np.uint16),np.eye(3),[0]*5,np.eye(3),[0]*5,2*np.eye(3),[0,0,0],(2,2))

if __name__=='__main__':unittest.main()
