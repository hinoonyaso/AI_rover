"""Test TCP model update without hardware. / 하드웨어 없이 TCP 모델 변경을 검증한다."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import tcp_settings as t

class TcpSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'arm.xacro'
        self.original=(Path(__file__).resolve().parents[2]/'src/jetrover_description/urdf/arm.urdf.xacro').read_bytes()
        self.path.write_bytes(self.original)
        self.candidate={'parent_frame':'gripper_link','reference_frame':'base_link','tcp_gripper_m':[0.,0.,.1],'applied':False}
    def tearDown(self):self.temp.cleanup()
    def test_apply_frame_transform_and_restore(self):
        plan=t.preview(self.path,self.candidate)
        self.assertAlmostEqual(plan['target_link5_m'][2],.1054388)
        result=t.apply(self.path,self.root/'backups',self.candidate,plan['config_hash'],plan['candidate_hash'])
        after=t.preview(self.path,self.candidate)
        self.assertAlmostEqual(after['current_link5_m'][2],.1054388)
        self.assertEqual(after['rotation_rpy'],plan['rotation_rpy'])
        t.restore(self.path,self.root/'backups',result['backup_id']);self.assertEqual(self.path.read_bytes(),self.original)
    def test_changed_candidate_and_frame_are_rejected(self):
        plan=t.preview(self.path,self.candidate)
        with self.assertRaisesRegex(ValueError,'candidate_unavailable'):t.preview(self.path,dict(self.candidate,parent_frame='other'))
        with self.assertRaisesRegex(ValueError,'candidate_changed'):t.apply(self.path,self.root/'backups',dict(self.candidate,tcp_gripper_m=[0,0,.2]),plan['config_hash'],plan['candidate_hash'])

if __name__=='__main__':unittest.main()
