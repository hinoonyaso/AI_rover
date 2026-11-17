#!/usr/bin/python3
"""Capture a corrected-depth background bound to the active calibration.

한글: 활성 보정값에 연결된 보정 깊이 기준 영상을 촬영한다.
"""
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


def main():
    """Capture a median of distinct fresh frames without commanding the robot.

    한글: 로봇 명령 없이 서로 다른 최신 프레임의 중앙값을 촬영한다.
    """
    if len(sys.argv)!=3:raise SystemExit('usage: capture_rgbd_background.py OUTPUT.npy ACTIVE_CALIBRATION.json')
    target,calib=Path(sys.argv[1]),Path(sys.argv[2])
    if target.exists() or target.is_symlink() or target.with_suffix(target.suffix+'.json').exists() or calib.is_symlink() or not calib.is_file() or target.suffix!='.npy':raise SystemExit('invalid paths or existing reference')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    before=digest(calib);frames=[];stamps=set();bridge=CvBridge();rclpy.init(args=[]);node=Node('jetinspect_rgbd_background_capture')
    def receive(msg):
        stamp=msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9;now=node.get_clock().now().nanoseconds*1e-9
        if msg.header.frame_id!='depth_cam_color_optical_frame' or msg.encoding!='16UC1' or stamp in stamps or not 0<=now-stamp<2:return
        image=bridge.imgmsg_to_cv2(msg,desired_encoding='passthrough')
        if image.dtype!=np.uint16 or image.ndim!=2 or (frames and image.shape!=frames[0].shape):return
        stamps.add(stamp);frames.append(image.copy())
    node.create_subscription(Image,'/depth_cam/depth_corrected/image_raw',receive,qos_profile_sensor_data)
    try:
        end=time.monotonic()+20
        while len(frames)<10 and time.monotonic()<end:rclpy.spin_once(node,timeout_sec=.1)
        if len(frames)<10 or digest(calib)!=before:raise RuntimeError('insufficient frames or calibration changed')
        stack=np.stack(frames);valid=(stack>0).sum(axis=0)>=8
        masked=np.where(stack>0,stack,np.nan);median=np.nanmedian(masked,axis=0);median[~valid]=0
        image=np.nan_to_num(median,nan=0).astype(np.uint16)
        if (image>0).mean()<.05:raise RuntimeError('insufficient valid depth')
        target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        fd,temp=tempfile.mkstemp(prefix='.rgbd-background-',dir=target.parent)
        try:
            with os.fdopen(fd,'wb') as out:np.save(out,image,allow_pickle=False);out.flush();os.fsync(out.fileno())
            os.replace(temp,target)
        finally:
            if os.path.exists(temp):os.unlink(temp)
        metadata={'source_topic':'/depth_cam/depth_corrected/image_raw','background_sha256':digest(target),'calibration_sha256':before,'frame_count':len(frames)}
        sidecar=target.with_suffix(target.suffix+'.json');fd,temp=tempfile.mkstemp(prefix='.rgbd-metadata-',dir=target.parent)
        try:
            with os.fdopen(fd,'w') as out:json.dump(metadata,out);out.flush();os.fsync(out.fileno())
            os.replace(temp,sidecar)
        finally:
            if os.path.exists(temp):os.unlink(temp)
        print(json.dumps({'saved':True,'frames':len(frames),'valid_fraction':float((image>0).mean())}))
    finally:node.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
