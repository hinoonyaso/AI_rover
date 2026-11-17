"""Test odometry continuity, body-frame displacement and wrapping.

한글: 오도메트리 연속성, 몸체 기준 이동 및 각도 경계를 검증한다.
"""
import math
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace as N
sys.path.insert(0, str(Path(__file__).parent/'backend'))
from odom_observation import OdomTracker, odom_displacement, fresh_odom


def msg(x,y,yaw,stamp,frame='odom'):
    return N(header=N(stamp=N(sec=int(stamp),nanosec=int((stamp%1)*1e9)),frame_id=frame),child_frame_id='base_link',
             pose=N(pose=N(position=N(x=x,y=y),orientation=N(x=0.,y=0.,z=math.sin(yaw/2),w=math.cos(yaw/2)))))

class OdomTests(unittest.TestCase):
    def test_body_frame_and_wrapped_rotation(self):
        t=OdomTracker();t.update(msg(0,0,math.pi/2,10),100);start=t.value
        t.update(msg(0,1,math.pi/2,11),101)
        self.assertAlmostEqual(odom_displacement(start,t.value,'forward'),100.)
        self.assertAlmostEqual(odom_displacement(start,t.value,'lateral'),0.)
        t=OdomTracker();t.update(msg(0,0,math.radians(179),10),100);start=t.value
        t.update(msg(0,0,math.radians(-179),11),101)
        self.assertAlmostEqual(odom_displacement(start,t.value,'rotation'),2.)
    def test_gap_frame_and_stale_rejected(self):
        t=OdomTracker();t.update(msg(0,0,0,10),100);start=t.value
        t.update(msg(0,0,0,12,'other'),102)
        with self.assertRaisesRegex(ValueError,'odom_discontinuity'): odom_displacement(start,t.value,'forward')
        self.assertIsNone(fresh_odom({'timestamp':100,'odometry':{'raw':start}},'raw',104))
        self.assertIsNotNone(fresh_odom({'timestamp':100,'odometry':{'raw':start}},'raw',101))

if __name__ == '__main__': unittest.main()
