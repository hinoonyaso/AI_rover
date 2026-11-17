"""Test display-only battery corrections. / 표시 전용 배터리 보정을 시험한다."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import battery_settings as b

class BatterySettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'active.json'
        self.candidate={'method':'linear_reference_fit','applied':False,'slope':1.0,'intercept_v':0.2,
                        'samples':[{'sensor_v':10.},{'sensor_v':11.},{'sensor_v':12.}]}
    def tearDown(self):self.temp.cleanup()
    def test_apply_display_only_and_restore_absent(self):
        plan=b.preview(self.path,self.candidate)
        result=b.apply(self.path,self.root/'backups',self.candidate,plan['config_hash'],plan['candidate_hash'])
        self.assertAlmostEqual(b.corrected(self.path,11.),11.2)
        self.assertIsNone(b.corrected(self.path,12.1))
        self.assertIsNone(b.corrected(self.path,9.9))
        b.restore(self.path,self.root/'backups',result['backup_id'])
        self.assertFalse(self.path.exists())
    def test_candidate_and_config_drift_rejected(self):
        plan=b.preview(self.path,self.candidate)
        with self.assertRaisesRegex(ValueError,'candidate_changed'):
            b.apply(self.path,self.root/'backups',dict(self.candidate,intercept_v=.3),plan['config_hash'],plan['candidate_hash'])
        self.path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'config_changed'):
            b.apply(self.path,self.root/'backups',self.candidate,plan['config_hash'],plan['candidate_hash'])
        self.assertIsNone(b.corrected(self.path,11.))

if __name__=='__main__':unittest.main()
