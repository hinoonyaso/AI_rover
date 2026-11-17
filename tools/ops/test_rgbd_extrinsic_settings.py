"""Test candidate activation and rollback. / 후보 활성화와 복원을 검증한다."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import rgbd_extrinsic_settings as s

class ExtrinsicSettingsTest(unittest.TestCase):
    def test_apply_restore_and_conflict(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);path=root/'active.json';candidate={'source_frame':'depth_cam_depth_optical_frame','target_frame':'depth_cam_color_optical_frame','rotation_matrix':[[1,0,0],[0,1,0],[0,0,1]],'translation_m':[.01,0,0],'rms_m':.001,'applied':False}
            plan=s.preview(path,candidate);result=s.apply(path,root/'backup',candidate,plan['config_hash'],plan['candidate_hash']);self.assertTrue(path.exists())
            path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'config_changed'):s.restore(path,root/'backup',result['backup_id'])
            plan=s.preview(path,candidate);result=s.apply(path,root/'backup',candidate,plan['config_hash'],plan['candidate_hash']);s.restore(path,root/'backup',result['backup_id']);self.assertEqual(path.read_text(),'{}')
    def test_reject_reflection(self):
        candidate={'source_frame':'depth_cam_depth_optical_frame','target_frame':'depth_cam_color_optical_frame','rotation_matrix':[[-1,0,0],[0,1,0],[0,0,1]],'translation_m':[0,0,0],'rms_m':0,'applied':False}
        with self.assertRaisesRegex(ValueError,'invalid_candidate'):s.candidate(candidate)

if __name__=='__main__':unittest.main()
