#!/usr/bin/python3
"""Exercise corrected depth publication in an isolated ROS domain.

한글: 격리 ROS 도메인에서 보정 깊이 발행을 검증한다.
"""
import json
import os
import tempfile
import time
from pathlib import Path
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image,CameraInfo
from rgbd_reproject_node import ReprojectNode


def main():
    """Publish synthetic unregistered frames and verify transformed output.

    한글: 합성 미정합 영상을 발행하고 변환 결과를 확인한다.
    """
    if os.environ.get('ROS_DOMAIN_ID')!='191':raise RuntimeError('requires isolated domain 191')
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'candidate.json';path.write_text(json.dumps({'source_frame':'depth_cam_depth_optical_frame','target_frame':'depth_cam_color_optical_frame','rotation_matrix':[[1,0,0],[0,1,0],[0,0,1]],'translation_m':[.01,0,0]}))
        rclpy.init();node=ReprojectNode(path);driver=Node('rgbd_test_source');bridge=CvBridge();received=[]
        dp=driver.create_publisher(Image,'/depth_cam/depth/image_raw',qos_profile_sensor_data)
        dc=driver.create_publisher(CameraInfo,'/depth_cam/depth/camera_info',qos_profile_sensor_data)
        cc=driver.create_publisher(CameraInfo,'/depth_cam/color/camera_info',qos_profile_sensor_data)
        driver.create_subscription(Image,'/depth_cam/depth_corrected/image_raw',lambda m:received.append(m),qos_profile_sensor_data)
        try:
            end=time.monotonic()+10
            while not received and time.monotonic()<end:
                for publisher,frame in ((dc,'depth_cam_depth_optical_frame'),(cc,'depth_cam_color_optical_frame')):
                    info=CameraInfo();info.header.frame_id=frame;info.width=4;info.height=3;info.k=[100.,0.,0.,0.,100.,0.,0.,0.,1.];info.d=[0.]*5;info.distortion_model='plumb_bob';publisher.publish(info)
                data=np.zeros((3,4),np.uint16);data[1,1]=1000;msg=bridge.cv2_to_imgmsg(data,encoding='16UC1');msg.header.frame_id='depth_cam_depth_optical_frame';msg.header.stamp=driver.get_clock().now().to_msg();dp.publish(msg)
                rclpy.spin_once(node,timeout_sec=.05);rclpy.spin_once(driver,timeout_sec=.05)
            if not received:raise RuntimeError('corrected frame missing')
            output=bridge.imgmsg_to_cv2(received[-1],desired_encoding='passthrough')
            if output[1,2]!=1000 or received[-1].header.frame_id!='depth_cam_color_optical_frame':raise RuntimeError('incorrect corrected frame')
            print('PASS: candidate transform applied to isolated depth topic')
        finally:node.destroy_node();driver.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
