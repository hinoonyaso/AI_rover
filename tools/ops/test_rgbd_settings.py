"""Test registration mode persistence on temporary files.

한글: 임시 파일에서 정합 모드 저장과 복원을 시험한다.
"""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import rgbd_settings as settings

class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.path=self.root/'camera.yaml'
        self.original=(Path(__file__).resolve().parents[2]/'src/jetrover_perception/config/dabai_dcw.yaml').read_bytes();self.path.write_bytes(self.original)
    def tearDown(self):self.tmp.cleanup()
    def test_apply_and_restore_each_mode(self):
        for mode in ('SW_D2C','OFF','HW_D2C'):
            plan=settings.preview(self.path,mode);self.assertEqual(plan['current'],'HW_D2C')
            result=settings.apply(self.path,self.root/'backup',mode,plan['config_hash'],plan['candidate_hash'])
            self.assertEqual(settings.preview(self.path,mode)['current'],mode)
            self.assertIn('enable_color: true',self.path.read_text())
            settings.restore(self.path,self.root/'backup',result['backup_id']);self.assertEqual(self.path.read_bytes(),self.original)
    def test_reject_conflicts_and_unsupported_direction(self):
        with self.assertRaisesRegex(ValueError,'invalid_registration_mode'):settings.preview(self.path,'SW_C2D')
        plan=settings.preview(self.path,'OFF');self.path.write_bytes(self.original+b'\n')
        with self.assertRaisesRegex(ValueError,'config_changed'):settings.apply(self.path,self.root/'backup','OFF',plan['config_hash'],plan['candidate_hash'])

if __name__=='__main__':unittest.main()
