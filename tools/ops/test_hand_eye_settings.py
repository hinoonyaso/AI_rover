"""Exercise camera mount application with synthetic rigid transforms.

한글: 합성 강체 변환으로 카메라 장착 설정 적용을 검증한다.
"""
import math
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
import hand_eye_settings as settings

class HandEyeSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.path = self.root / 'camera.xacro'
        self.original = (Path(__file__).resolve().parents[2] / 'src/jetrover_description/urdf/depth_camera.urdf.xacro').read_bytes()
        self.path.write_bytes(self.original)
        self.mount = [[1,0,0,.1],[0,1,0,.2],[0,0,1,.3],[0,0,0,1]]
        self.candidate = {'applied': False, 'parent_frame': 'link4', 'camera_frame': 'depth_cam_color_optical_frame',
                          'link4_T_camera': [[0,-1,0,-.1],[1,0,0,.3],[0,0,1,.6],[0,0,0,1]]}
    def tearDown(self): self.temp.cleanup()
    def test_transform_apply_restore(self):
        plan = settings.preview(self.path, self.candidate, self.mount)
        for actual, expected in zip(plan['target_xyz_m'], [.1,.2,.3]): self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(plan['target_rpy_rad'][2], math.pi/2)
        result = settings.apply(self.path, self.root/'backup', self.candidate, self.mount, plan['config_hash'], plan['candidate_hash'])
        changed = settings.preview(self.path, self.candidate, self.mount)
        self.assertEqual(changed['current']['xyz'], '0.1 0.2 0.3')
        settings.restore(self.path, self.root/'backup', result['backup_id'])
        self.assertEqual(self.path.read_bytes(), self.original)
    def test_reject_conflicts_and_invalid_transforms(self):
        plan = settings.preview(self.path, self.candidate, self.mount)
        with self.assertRaisesRegex(ValueError, 'candidate_changed'):
            settings.apply(self.path, self.root/'backup', self.candidate, [[1,0,0,.2],[0,1,0,.2],[0,0,1,.3],[0,0,0,1]], plan['config_hash'], plan['candidate_hash'])
        with self.assertRaisesRegex(ValueError, 'invalid_pose'):
            settings.preview(self.path, dict(self.candidate, link4_T_camera=[[2,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]), self.mount)
        self.path.write_bytes(self.original + b'\n')
        with self.assertRaisesRegex(ValueError, 'config_changed'):
            settings.apply(self.path, self.root/'backup', self.candidate, self.mount, plan['config_hash'], plan['candidate_hash'])

if __name__ == '__main__': unittest.main()
