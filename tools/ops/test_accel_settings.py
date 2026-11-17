"""Exercise acceleration settings on isolated files. / 격리 파일로 가속도 설정을 시험한다."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import accel_settings as accel
import gyro_settings as gyro

class AccelSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'base.yaml'
        self.original=b'base_node:\n  ros__parameters:\n    gyro_bias: [0, 0, 0] # existing\n    other: 2\n'
        self.path.write_bytes(self.original)
        self.candidate={'current_offset_m_s2':[0,0,0], 'current_scale':[1,1,1], 'offset_m_s2':[.1,.2,.3], 'scale':[1.1,.9,1.0], 'method':'six_pose_diagonal','applied':False}
    def tearDown(self):self.temp.cleanup()
    def test_apply_default_and_restore_exact_bytes(self):
        plan=accel.preview(self.path,self.candidate)
        result=accel.apply(self.path,self.root/'backups',self.candidate,plan['config_hash'],plan['candidate_hash'])
        text=self.path.read_text()
        self.assertIn('accel_offset_m_s2: [0.1, 0.2, 0.3]',text)
        self.assertIn('accel_scale: [1.1, 0.9, 1]',text)
        self.assertIn('other: 2',text)
        gyro.restore(self.path,self.root/'backups',result['backup_id'])
        self.assertEqual(self.path.read_bytes(),self.original)
    def test_conflicts_and_partial_parameters_rejected(self):
        plan=accel.preview(self.path,self.candidate)
        with self.assertRaisesRegex(ValueError,'candidate_changed'):
            accel.apply(self.path,self.root/'backups',dict(self.candidate,scale=[1,1,1]),plan['config_hash'],plan['candidate_hash'])
        self.path.write_bytes(self.original+b'    accel_scale: [1,1,1]\n')
        with self.assertRaisesRegex(ValueError,'invalid_config'):accel.preview(self.path,self.candidate)

if __name__ == '__main__': unittest.main()
