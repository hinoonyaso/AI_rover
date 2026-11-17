"""Verify isolated gyro file transaction and restoration. / 격리 자이로 설정 거래와 복원을 검증한다."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
import gyro_settings as g

class GyroSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = self.root / 'base.yaml'
        self.original = b'base_node:\n  ros__parameters:\n    # keep\n    gyro_bias: [0.1, 0.2, -0.3]  # units\n    other: true\n'
        self.path.write_bytes(self.original)
        self.candidate = {'current_bias':[.1,.2,-.3], 'candidate':[.11,.19,-.25], 'unit':'rad/s', 'applied':False}

    def tearDown(self): self.tmp.cleanup()

    def test_apply_backup_and_guarded_restore(self):
        plan = g.preview(self.path, self.candidate)
        result = g.apply(self.path, self.root / 'backups', self.candidate, plan['config_hash'], plan['candidate_hash'])
        self.assertIn(b'gyro_bias: [0.11, 0.19, -0.25]  # units', self.path.read_bytes())
        self.assertEqual((self.root / 'backups' / (result['backup_id'] + '.json')).stat().st_mode & 0o777, 0o600)
        g.restore(self.path, self.root / 'backups', result['backup_id'])
        self.assertEqual(self.path.read_bytes(), self.original)
        with self.assertRaisesRegex(ValueError, 'config_changed'): g.restore(self.path, self.root / 'backups', result['backup_id'])

    def test_drift_duplicate_symlink_and_invalid_candidate_are_rejected(self):
        plan = g.preview(self.path, self.candidate)
        self.path.write_bytes(self.original + b'# changed\n')
        with self.assertRaisesRegex(ValueError, 'config_changed'): g.apply(self.path, self.root / 'backups', self.candidate, plan['config_hash'], plan['candidate_hash'])
        with self.assertRaisesRegex(ValueError, 'bias_changed'): g.preview(self.path, dict(self.candidate, current_bias=[0,0,0]))
        with self.assertRaisesRegex(ValueError, 'invalid_bias'): g.preview(self.path, dict(self.candidate, candidate=[float('nan'),0,0]))
        self.path.write_bytes(self.original + b'    gyro_bias: [0,0,0]\n')
        with self.assertRaisesRegex(ValueError, 'invalid_config'): g.preview(self.path, self.candidate)
        link = self.root / 'link.yaml'
        link.symlink_to(self.path)
        with self.assertRaisesRegex(ValueError, 'config_unavailable'): g.preview(link, self.candidate)

    def test_changed_candidate_is_not_applied(self):
        plan = g.preview(self.path, self.candidate)
        changed = dict(self.candidate, candidate=[.15,.19,-.25])
        with self.assertRaisesRegex(ValueError, 'candidate_changed'):
            g.apply(self.path, self.root / 'backups', changed, plan['config_hash'], plan['candidate_hash'])
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_failed_replace_leaves_original_and_backup(self):
        plan = g.preview(self.path, self.candidate)
        with patch.object(g.os, 'replace', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError): g.apply(self.path, self.root / 'backups', self.candidate, plan['config_hash'], plan['candidate_hash'])
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(len(list((self.root / 'backups').glob('*.json'))), 1)

if __name__ == '__main__': unittest.main()
