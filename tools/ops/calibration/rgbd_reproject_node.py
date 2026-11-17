#!/usr/bin/python3
"""Publish a separate corrected depth topic from unregistered camera data.

한글: 미정합 카메라 데이터로 별도의 보정 깊이 토픽을 발행한다.
"""
import json
import sys
import time
from pathlib import Path
import cv2
from cv_bridge import CvBridge
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image,CameraInfo
from rgbd_projection import project


class ReprojectNode(Node):
    """Reject aligned or stale inputs and publish color-frame depth separately.

    한글: 이미 정합됐거나 오래된 입력을 거부하고 보정 깊이를 별도로 발행한다.
    """
    def __init__(self,path):
        super().__init__('jetinspect_rgbd_reproject');self.path=Path(path);self.bridge=CvBridge();self.infos={}
        self.create_subscription(CameraInfo,'/depth_cam/depth/camera_info',lambda m:self.info('depth',m),qos_profile_sensor_data)
        self.create_subscription(CameraInfo,'/depth_cam/color/camera_info',lambda m:self.info('color',m),qos_profile_sensor_data)
        self.create_subscription(Image,'/depth_cam/depth/image_raw',self.receive,qos_profile_sensor_data)
        self.publisher=self.create_publisher(Image,'/depth_cam/depth_corrected/image_raw',qos_profile_sensor_data)
        self.info_publisher=self.create_publisher(CameraInfo,'/depth_cam/depth_corrected/camera_info',qos_profile_sensor_data)

    def info(self,kind,msg):
        """Keep recent camera intrinsics. / 최근 카메라 내부 파라미터를 저장한다."""
        self.infos[kind]=(msg,time.monotonic())

    def receive(self,msg):
        """Project only unaligned raw data using the reviewed configuration.

        한글: 검토된 설정을 사용하여 미정합 원본 데이터만 투영한다.
        """
        try:
            if msg.header.frame_id!='depth_cam_depth_optical_frame' or msg.encoding!='16UC1':raise ValueError('raw_depth_required')
            depth,dt=self.infos['depth'];color,ct=self.infos['color'];now=time.monotonic()
            if now-dt>3 or now-ct>3 or depth.header.frame_id!=msg.header.frame_id or color.header.frame_id!='depth_cam_color_optical_frame':raise ValueError('camera_info_unavailable')
            if (msg.width,msg.height)!=(depth.width,depth.height):raise ValueError('resolution_mismatch')
            if depth.distortion_model not in ('plumb_bob','rational_polynomial') or color.distortion_model not in ('plumb_bob','rational_polynomial'):raise ValueError('unsupported_distortion')
            if self.path.is_symlink() or self.path.stat().st_size>65536:raise ValueError('invalid_calibration')
            candidate=json.loads(self.path.read_text())
            if candidate.get('source_frame')!='depth_cam_depth_optical_frame' or candidate.get('target_frame')!='depth_cam_color_optical_frame':raise ValueError('invalid_calibration')
            image=self.bridge.imgmsg_to_cv2(msg,desired_encoding='passthrough')
            corrected=project(image,depth.k,depth.d,color.k,color.d,candidate['rotation_matrix'],candidate['translation_m'],(color.width,color.height))
            output=self.bridge.cv2_to_imgmsg(corrected,encoding='16UC1');output.header=msg.header;output.header.frame_id=color.header.frame_id
            color.header.stamp=msg.header.stamp
            self.publisher.publish(output);self.info_publisher.publish(color)
        except (OSError,ValueError,KeyError,TypeError,cv2.error) as exc:
            self.get_logger().warning('RGB-D reprojection unavailable: '+str(exc),throttle_duration_sec=10.)


def main():
    """Run only with an explicitly supplied candidate path.

    한글: 명시적으로 지정한 후보 경로가 있을 때만 실행한다.
    """
    if len(sys.argv)!=2:raise SystemExit('usage: rgbd_reproject_node.py CANDIDATE_JSON')
    rclpy.init(args=[]);node=ReprojectNode(sys.argv[1])
    try:rclpy.spin(node)
    finally:node.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
