"""Test LiDAR model update and rollback. / LiDAR 모델 변경과 복원을 시험한다."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import lidar_settings as lidar

class LidarSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'lidar.xacro'
        source=Path(__file__).resolve().parents[2]/'src/jetrover_description/urdf/lidar.urdf.xacro'
        self.original=source.read_bytes();self.path.write_bytes(self.original)
        self.candidate={'parent_frame':'base_link','child_frame':'lidar_link','translation_m':[.1,.02,.05],'applied':False}
    def tearDown(self):self.temp.cleanup()
    def test_apply_xyz_only_and_restore(self):
        plan=lidar.preview(self.path,self.candidate)
        result=lidar.apply(self.path,self.root/'backup',self.candidate,plan['config_hash'],plan['candidate_hash'])
        after=lidar.preview(self.path,self.candidate)
        self.assertEqual(after['current_m'],[.1,.02,.05])
        self.assertEqual(after['rotation_rpy'],plan['rotation_rpy'])
        lidar.restore(self.path,self.root/'backup',result['backup_id']);self.assertEqual(self.path.read_bytes(),self.original)
    def test_reject_drift_and_wrong_frame(self):
        plan=lidar.preview(self.path,self.candidate)
        with self.assertRaisesRegex(ValueError,'candidate_unavailable'):lidar.preview(self.path,dict(self.candidate,child_frame='other'))
        self.path.write_bytes(self.original+b'\n')
        with self.assertRaisesRegex(ValueError,'config_changed'):lidar.apply(self.path,self.root/'backup',self.candidate,plan['config_hash'],plan['candidate_hash'])
    def test_yaw_preserves_position_and_restores(self):
        candidate={'parent_frame':'base_link','child_frame':'lidar_link','yaw_deg':12.0,'applied':False}
        plan=lidar.preview_yaw(self.path,candidate)
        result=lidar.apply_yaw(self.path,self.root/'backup',candidate,plan['config_hash'],plan['candidate_hash'])
        after=lidar.preview_yaw(self.path,candidate)
        self.assertAlmostEqual(after['current_deg'],12.0,places=8)
        self.assertEqual(after['position_m'],plan['position_m'])
        lidar.restore(self.path,self.root/'backup',result['backup_id'])
        self.assertEqual(self.path.read_bytes(),self.original)
    def test_yaw_rejects_large_change_and_changed_config(self):
        candidate={'parent_frame':'base_link','child_frame':'lidar_link','yaw_deg':10.0,'applied':False}
        with self.assertRaisesRegex(ValueError,'yaw_change_too_large'):lidar.preview_yaw(self.path,dict(candidate,yaw_deg=80))
        plan=lidar.preview_yaw(self.path,candidate)
        self.path.write_bytes(self.original+b'\n')
        with self.assertRaisesRegex(ValueError,'config_changed'):
            lidar.apply_yaw(self.path,self.root/'backup',candidate,plan['config_hash'],plan['candidate_hash'])

if __name__=='__main__':unittest.main()
