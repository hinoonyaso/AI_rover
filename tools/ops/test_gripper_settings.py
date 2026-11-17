"""Verify display-only gripper width calibration. / 그리퍼 폭 표시 보정을 검증한다."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import gripper_settings as g

class GripperSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'active.json'
        self.candidate={'method':'two_point_linear_interpolation','applied':False,'slope_mm_per_rad':60.,'intercept_mm':-20.,
                        'samples':{'open':{'angle_rad':1.,'width_mm':40.,'servo_id':10},'closed':{'angle_rad':.5,'width_mm':10.,'servo_id':10}}}
    def tearDown(self):self.temp.cleanup()
    def test_apply_interpolate_and_restore(self):
        plan=g.preview(self.path,self.candidate)
        result=g.apply(self.path,self.root/'backups',self.candidate,plan['config_hash'],plan['candidate_hash'])
        self.assertAlmostEqual(g.width(self.path,.75,10),25.)
        self.assertIsNone(g.width(self.path,1.1,10))
        self.assertIsNone(g.width(self.path,.75,9))
        g.restore(self.path,self.root/'backups',result['backup_id']);self.assertFalse(self.path.exists())
    def test_inconsistent_samples_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'invalid_gripper_candidate'):g.preview(self.path,dict(self.candidate,intercept_mm=0))

if __name__=='__main__':unittest.main()
