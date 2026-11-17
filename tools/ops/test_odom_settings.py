"""Test command odometry fit and guarded settings. / 명령 오도메트리 계산과 설정을 검증한다."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import odom_settings as odom
import gyro_settings as gyro

class OdomSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'base.yaml'
        self.original=b'base_node:\n  ros__parameters:\n    gyro_bias: [0,0,0]\n    odom_linear_scale: 1.0\n    odom_lateral_scale: 1.0\n    odom_angular_scale: 1.0\n'
        self.path.write_bytes(self.original)
    def tearDown(self):self.temp.cleanup()
    def trials(self,motion,source='command'):
        return [{'kind':'odometry','result':{'motion':motion,'source':source,'method':'manual_single_trial_comparison','recorded':100.,'reference':110.}} for _ in range(3)]
    def test_fit_apply_and_restore(self):
        candidate=odom.fit(self.path,'forward',self.trials('forward'))
        self.assertAlmostEqual(candidate['candidate'],1.1)
        plan=odom.preview(self.path,candidate)
        result=odom.apply(self.path,self.root/'backups',candidate,plan['config_hash'],plan['candidate_hash'])
        self.assertIn('odom_linear_scale: 1.1',self.path.read_text())
        gyro.restore(self.path,self.root/'backups',result['backup_id']);self.assertEqual(self.path.read_bytes(),self.original)
    def test_lateral_accounts_for_linear_and_rejects_noncommand(self):
        self.path.write_bytes(self.original.replace(b'odom_linear_scale: 1.0',b'odom_linear_scale: 1.1'))
        candidate=odom.fit(self.path,'lateral',self.trials('lateral'))
        self.assertAlmostEqual(candidate['candidate'],1.)
        with self.assertRaisesRegex(ValueError,'invalid_trials'):odom.fit(self.path,'forward',self.trials('forward','ekf'))
        with self.assertRaisesRegex(ValueError,'invalid_trials'):odom.fit(self.path,'forward',self.trials('forward')[:2])

if __name__=='__main__':unittest.main()
