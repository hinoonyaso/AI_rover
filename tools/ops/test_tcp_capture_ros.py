#!/usr/bin/python3
"""Exercise TCP TF capture in an isolated ROS domain.

한글: 격리된 ROS 도메인에서 TCP TF 캡처를 검증한다.
"""
import json
import os
from pathlib import Path
import subprocess
import time
import unittest
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster

class CaptureTest(unittest.TestCase):
    def test_dynamic_tf_capture(self):
        rclpy.init(); node=Node('tcp_pose_test_publisher'); publisher=TransformBroadcaster(node)
        script=Path(__file__).parent/'calibration/capture_arm_pose.py'
        process=subprocess.Popen(['/usr/bin/python3',str(script)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                                 env={**os.environ,'OPENBLAS_NUM_THREADS':'1'})
        try:
            deadline=time.monotonic()+13
            while process.poll() is None and time.monotonic()<deadline:
                tf=TransformStamped();tf.header.frame_id='base_link';tf.child_frame_id='gripper_link'
                tf.header.stamp=node.get_clock().now().to_msg();tf.transform.translation.x=.25;tf.transform.rotation.w=1.
                publisher.sendTransform(tf);rclpy.spin_once(node,timeout_sec=.05)
            stdout,stderr=process.communicate(timeout=3)
            self.assertEqual(process.returncode,0,stderr+' '+stdout)
            self.assertAlmostEqual(json.loads(stdout)['result'][0][3],.25)
        finally:
            if process.poll() is None:process.kill();process.wait()
            node.destroy_node();rclpy.shutdown()

if __name__=='__main__':unittest.main()
