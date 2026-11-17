"""Test guarded Nav2 footprint updates. / Nav2 외형의 안전한 설정 변경을 시험한다."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import footprint_settings as f

class FootprintTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'nav.yaml'
        self.original=('global_costmap:\n  global_costmap:\n    ros__parameters:\n      footprint: "[[0.2, 0.1], [0.2, -0.1], [-0.2, -0.1], [-0.2, 0.1]]"\n      footprint_padding: 0.05\nlocal_costmap:\n  local_costmap:\n    ros__parameters:\n      footprint: "[[0.2, 0.1], [0.2, -0.1], [-0.2, -0.1], [-0.2, 0.1]]"\n      footprint_padding: 0.03\n').encode()
        self.path.write_bytes(self.original)
        self.candidate={'frame_id':'base_footprint','applied':False,'polygon_m':[[.3,.2],[.3,-.2],[-.3,-.2],[-.3,.2]]}
    def tearDown(self):self.temp.cleanup()
    def test_apply_both_and_restore_padding(self):
        plan=f.preview(self.path,self.candidate)
        result=f.apply(self.path,self.root/'backup',self.candidate,plan['config_hash'],plan['candidate_hash'])
        self.assertEqual(self.path.read_text().count('[[0.3,0.2],[0.3,-0.2],[-0.3,-0.2],[-0.3,0.2]]'),2)
        self.assertIn('footprint_padding: 0.05',self.path.read_text())
        self.assertIn('footprint_padding: 0.03',self.path.read_text())
        f.restore(self.path,self.root/'backup',result['backup_id']);self.assertEqual(self.path.read_bytes(),self.original)
    def test_shrink_and_crossed_polygon_rejected(self):
        small=dict(self.candidate,polygon_m=[[.1,.1],[.1,-.1],[-.1,-.1],[-.1,.1]])
        with self.assertRaisesRegex(ValueError,'footprint_shrinks'):f.preview(self.path,small)
        crossed=dict(self.candidate,polygon_m=[[.3,.2],[-.3,-.2],[.3,-.2],[-.3,.2]])
        with self.assertRaisesRegex(ValueError,'invalid_footprint'):f.preview(self.path,crossed)

if __name__=='__main__':unittest.main()
