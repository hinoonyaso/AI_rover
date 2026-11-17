"""Test color CameraInfo configuration on isolated files.

한글: 격리 파일로 컬러 CameraInfo 설정을 시험한다.
"""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import camera_settings as camera

class CameraSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'dabai.yaml'
        self.original=b'/**:\n  ros__parameters:\n    depth_registration: true\n    enable_color: true\n    color_width: 640\n'
        self.path.write_bytes(self.original)
        self.candidate={'width':640,'height':360,'camera_matrix':[[500,0,320],[0,501,180],[0,0,1]],
                        'distortion':[.1,0,0,0,0],'applied':False}
        self.info={'width':640,'height':360}
    def tearDown(self):self.temp.cleanup()
    def test_apply_and_restore_config_without_touching_depth(self):
        plan=camera.preview(self.path,self.candidate,self.info)
        result=camera.apply(self.path,self.root/'backups',self.candidate,self.info,plan['config_hash'],plan['candidate_hash'])
        self.assertIn('depth_registration: true',self.path.read_text())
        self.assertIn('color_info_url: "file://',self.path.read_text())
        calibration=self.root/'backups'/('color-'+result['backup_id']+'.yaml')
        self.assertIn('distortion_model: plumb_bob',calibration.read_text())
        self.assertEqual(calibration.stat().st_mode&0o777,0o600)
        camera.restore(self.path,self.root/'backups',result['backup_id'])
        self.assertEqual(self.path.read_bytes(),self.original)
    def test_drift_bad_matrix_and_resolution_are_rejected(self):
        plan=camera.preview(self.path,self.candidate,self.info)
        with self.assertRaisesRegex(ValueError,'camera_resolution_mismatch'):camera.preview(self.path,self.candidate,{'width':320,'height':180})
        with self.assertRaisesRegex(ValueError,'invalid_camera_candidate'):camera.preview(self.path,dict(self.candidate,distortion=[0]),self.info)
        self.path.write_bytes(self.original+b'    # changed\n')
        with self.assertRaisesRegex(ValueError,'config_changed'):camera.apply(self.path,self.root/'backups',self.candidate,self.info,plan['config_hash'],plan['candidate_hash'])

if __name__=='__main__':unittest.main()
