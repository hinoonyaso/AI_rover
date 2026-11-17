"""Check chessboard pose extraction with synthetic imagery.

한글: 합성 영상으로 체커보드 자세 추출을 확인한다.
"""
import unittest
from types import SimpleNamespace
import cv2
import numpy as np
from hand_eye_capture import board_pose

class CaptureMathTests(unittest.TestCase):
    def test_chessboard_and_missing_board(self):
        image=np.full((480,640,3),127,dtype=np.uint8)
        for y in range(7):
            for x in range(8):
                color=255 if (x+y)%2 else 0
                cv2.rectangle(image,(120+x*45,75+y*45),(120+(x+1)*45-1,75+(y+1)*45-1),(color,)*3,-1)
        info=SimpleNamespace(k=[500,0,320,0,500,240,0,0,1],d=[0,0,0,0,0],distortion_model='plumb_bob')
        pose,rms=board_pose(image,info,7,6,.025)
        self.assertEqual(np.asarray(pose).shape,(4,4));self.assertGreater(pose[2][3],0);self.assertLess(rms,1)
        with self.assertRaisesRegex(ValueError,'board_not_found'):board_pose(np.zeros_like(image),info,7,6,.025)

if __name__=='__main__':unittest.main()
