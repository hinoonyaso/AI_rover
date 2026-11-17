"""Check that safety background and active calibration cannot silently drift.

한글: 안전 기준 영상과 활성 보정값의 불일치를 거부한다.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('guard',Path(__file__).resolve().parents[1]/'launch/depth_source_guard.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)

class DepthGuardTests(unittest.TestCase):
    def test_only_matching_background_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);bg=root/'reference.npy';cal=root/'calibration.json';bg.write_bytes(b'background');cal.write_bytes(b'calibration')
            digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            meta={'source_topic':'/depth_cam/depth_corrected/image_raw','background_sha256':digest(bg),'calibration_sha256':digest(cal)}
            bg.with_suffix('.npy.json').write_text(json.dumps(meta))
            self.assertEqual(guard.validate_corrected_background(bg,cal),str(bg))
            cal.write_bytes(b'changed')
            with self.assertRaises(ValueError):guard.validate_corrected_background(bg,cal)

if __name__=='__main__':unittest.main()
