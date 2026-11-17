#!/usr/bin/python3
"""Verify obstacle cloud fails closed on frame or calibration mismatch.

한글: 프레임이나 보정값 불일치 시 장애물 클라우드를 차단하는지 검증한다.
"""
import hashlib
import os
import tempfile
import time
from pathlib import Path
import sys
import threading
from unittest.mock import patch
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.executors import MultiThreadedExecutor
from sensor_msgs.msg import Image,CameraInfo,PointCloud2
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sparse_point_cloud import SparsePointCloud


def main():
    """Exercise matching, wrong-frame, and changed-calibration cases.

    한글: 일치, 다른 프레임, 보정값 변경 사례를 검증한다.
    """
    if os.environ.get('ROS_DOMAIN_ID')!='192':raise RuntimeError('requires isolated domain 192')
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);ref=root/'ref.npy';np.save(ref,np.full((16,16),1000,np.uint16));cal=root/'cal.json';cal.write_bytes(b'cal')
        digest=hashlib.sha256(b'cal').hexdigest()
        rclpy.init(args=['--ros-args','-p','background_depth_path:='+str(ref),'-p','background_calibration_path:='+str(cal),'-p','background_calibration_sha256:='+digest,'-p','expected_depth_frame:=depth_cam_color_optical_frame','-p','process_every_nth:=1','-p','home_pose_rad:=[0.0]'])
        node=SparsePointCloud();driver=Node('depth_guard_test');bridge=CvBridge();received=[]
        node.home_pose=None
        info_pub=driver.create_publisher(CameraInfo,'depth/camera_info',qos_profile_sensor_data)
        image_pub=driver.create_publisher(Image,'depth/image_raw',qos_profile_sensor_data)
        subscription=driver.create_subscription(PointCloud2,'depth/points_sparse',lambda m:received.append(m),10)
        executor=MultiThreadedExecutor(num_threads=2);executor.add_node(node);executor.add_node(driver)
        thread=threading.Thread(target=executor.spin,daemon=True);thread.start()
        def send(frame,count=15):
            for _ in range(count):
                info=CameraInfo();info.header.frame_id=frame;info.width=16;info.height=16;info.k=[100.,0.,8.,0.,100.,8.,0.,0.,1.];info_pub.publish(info)
                image=bridge.cv2_to_imgmsg(np.full((16,16),500,np.uint16),encoding='16UC1');image.header.frame_id=frame;image.header.stamp=driver.get_clock().now().to_msg();image_pub.publish(image)
                time.sleep(.05)
        try:
            for _ in range(20):
                node.pub.publish(PointCloud2());time.sleep(.05)
            if not received:raise RuntimeError('test PointCloud2 subscription unavailable')
            received.clear()
            with patch.object(node.pub,'publish',wraps=node.pub.publish) as publish:
                send('depth_cam_depth_optical_frame');assert publish.call_count==0 and not received,'unaligned depth published'
                send('depth_cam_color_optical_frame',30)
                assert publish.call_count>0,'aligned depth not published'
                assert received,'aligned depth not delivered'
                count=publish.call_count;cal.write_bytes(b'changed');send('depth_cam_color_optical_frame');assert publish.call_count==count,'changed calibration published'
            print('PASS frame and calibration mismatch withheld obstacle cloud')
        finally:executor.shutdown();thread.join(timeout=3);node.destroy_node();driver.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
