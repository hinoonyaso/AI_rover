"""Validate isolated joint-offset update and restore. / 격리 관절 오프셋 변경과 복원을 검증한다."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import joint_settings as joint
import gyro_settings as gyro

class JointSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'base.yaml'
        self.original=b'base_node:\n  ros__parameters:\n    gyro_bias: [0,0,0]\n    arm_joint_names: [joint1, joint2, r_joint]\n    arm_joint_offsets_rad: [0.0, 0.1, 0.0]\n'
        self.path.write_bytes(self.original)
        self.candidate={'joint':'joint2','current_offset_rad':.1,'candidate_offset_rad':.2,'method':'single_reference_offset','source_confirmed':True,'applied':False}
    def tearDown(self):self.temp.cleanup()
    def test_apply_one_and_restore(self):
        plan=joint.preview(self.path,self.candidate)
        result=joint.apply(self.path,self.root/'backups',self.candidate,plan['config_hash'],plan['candidate_hash'])
        self.assertIn('arm_joint_offsets_rad: [0, 0.2, 0]',self.path.read_text())
        gyro.restore(self.path,self.root/'backups',result['backup_id']);self.assertEqual(self.path.read_bytes(),self.original)
    def test_reject_wrong_baseline_and_excess_correction(self):
        with self.assertRaisesRegex(ValueError,'joint_settings_changed'):joint.preview(self.path,dict(self.candidate,current_offset_rad=0))
        with self.assertRaisesRegex(ValueError,'invalid_joint_candidate'):joint.preview(self.path,dict(self.candidate,candidate_offset_rad=1))
        with self.assertRaisesRegex(ValueError,'candidate_unavailable'):joint.preview(self.path,dict(self.candidate,source_confirmed=False))

if __name__=='__main__':unittest.main()
