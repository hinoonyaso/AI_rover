#!/usr/bin/python3
"""Verify background capture and metadata with isolated ROS input.

한글: 격리 ROS 입력으로 배경 촬영과 메타데이터를 검증한다.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


def main():
    """Publish fresh corrected frames and check the captured reference.

    한글: 최신 보정 프레임을 발행하고 촬영된 기준을 확인한다.
    """
    if os.environ.get('ROS_DOMAIN_ID')!='193':raise RuntimeError('requires isolated domain 193')
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);cal=root/'calibration.json';cal.write_text('{}');output=root/'background.npy'
        worker=subprocess.Popen(['/usr/bin/python3',str(Path(__file__).parent/'capture_rgbd_background.py'),str(output),str(cal)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'1'})
        rclpy.init();node=Node('rgbd_background_test');pub=node.create_publisher(Image,'/depth_cam/depth_corrected/image_raw',qos_profile_sensor_data);bridge=CvBridge()
        try:
            end=time.monotonic()+23
            while worker.poll() is None and time.monotonic()<end:
                msg=bridge.cv2_to_imgmsg(np.full((8,8),1000,np.uint16),encoding='16UC1');msg.header.frame_id='depth_cam_color_optical_frame';msg.header.stamp=node.get_clock().now().to_msg();pub.publish(msg)
                rclpy.spin_once(node,timeout_sec=.03);time.sleep(.04)
            out,err=worker.communicate(timeout=3)
            if worker.returncode:raise RuntimeError(err+' '+out)
            data=json.loads(out);image=np.load(output,allow_pickle=False);metadata=json.loads(output.with_suffix('.npy.json').read_text())
            assert data['frames']==10 and np.all(image==1000) and metadata['source_topic']=='/depth_cam/depth_corrected/image_raw'
            print('PASS corrected background capture with bound metadata')
        finally:
            if worker.poll() is None:worker.kill();worker.wait()
            node.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
