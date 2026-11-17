"""Exercise checkerboard input validation. / 체커보드 입력 검증 시험."""
import unittest
import numpy as np
import cv2
from calibration_math import calibrate_checkerboard


class CameraTests(unittest.TestCase):
    def test_estimates_candidate_from_multiple_views(self):
        board = np.zeros((210, 240), np.uint8)
        for y in range(7):
            for x in range(8):
                if (x + y) % 2:
                    board[y*30:(y+1)*30, x*30:(x+1)*30] = 255
        src = np.float32([[0, 0], [239, 0], [239, 209], [0, 209]])
        images = []
        for i in range(12):
            x, y = 70 + (i % 4) * 75, 20 + (i // 4) * 48
            dst = np.float32([[x,y],[x+205+i*2,y+5],[x+210,y+180],[x+5,y+175-i]])
            images.append(cv2.warpPerspective(board, cv2.getPerspectiveTransform(src, dst), (640,360), borderValue=127))
        result = calibrate_checkerboard(images, 7, 6, .025)
        self.assertGreaterEqual(result['detected_views'], 8)
        self.assertLess(result['reprojection_rms_px'], 2)
        self.assertFalse(result['applied'])

    def test_rejects_invalid_board_and_missing_views(self):
        image = np.zeros((360, 640), dtype=np.uint8)
        for args, reason in [(([image]*8, 2, 6, .025), 'invalid_board'),
                             (([image]*7, 7, 6, .025), 'image_count'),
                             (([image]*8, 7, 6, .025), 'insufficient_detections')]:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                calibrate_checkerboard(*args)

    def test_rejects_repeated_identical_view(self):
        image = np.zeros((360, 640), dtype=np.uint8)
        for y in range(7):
            for x in range(8):
                if (x + y) % 2:
                    image[50+y*30:50+(y+1)*30, 160+x*30:160+(x+1)*30] = 255
        with self.assertRaisesRegex(ValueError, 'insufficient_diversity'):
            calibrate_checkerboard([image]*8, 7, 6, .025)


if __name__ == '__main__': unittest.main()
