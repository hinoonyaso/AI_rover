#!/usr/bin/python3
"""Capture a chessboard pose and timestamp-matched arm TF, without motion.

한글: 구동 없이 체커보드 자세와 같은 시각의 팔 TF를 수집한다.
"""
import json
import math
import sys
import time
import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import Image, CameraInfo
from tf2_ros import Buffer, TransformListener, TransformException
from static_mount import transform_matrix


def board_pose(image, info, columns, rows, square_m):
    """Estimate optical-frame chessboard pose and reprojection error.

    한글: 광학 좌표계 체커보드 자세와 재투영 오차를 추정한다.
    """
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY) if len(image.shape)==3 else image
    ok,corners=cv2.findChessboardCorners(gray,(columns,rows),cv2.CALIB_CB_ADAPTIVE_THRESH|cv2.CALIB_CB_NORMALIZE_IMAGE)
    if not ok:raise ValueError('board_not_found')
    corners=cv2.cornerSubPix(gray,corners,(5,5),(-1,-1),(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_MAX_ITER,30,.001))
    points=np.zeros((rows*columns,3),np.float32);points[:,:2]=np.mgrid[0:columns,0:rows].T.reshape(-1,2)*square_m
    k=np.array(info.k,dtype=np.float64).reshape(3,3);d=np.array(info.d,dtype=np.float64)
    if not np.isfinite(k).all() or not np.isfinite(d).all() or k[0,0]<=0 or k[1,1]<=0 or info.distortion_model not in ('plumb_bob','rational_polynomial'):
        raise ValueError('camera_info_invalid')
    ok,rvec,tvec=cv2.solvePnP(points,corners,k,d,flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok or not np.isfinite(tvec).all() or tvec[2,0]<=0:raise ValueError('board_pose_failed')
    projected,_=cv2.projectPoints(points,rvec,tvec,k,d)
    rms=float(np.sqrt(np.mean(np.sum((projected-corners)**2,axis=2))))
    if not math.isfinite(rms) or rms>2:raise ValueError('board_pose_inaccurate')
    result=np.eye(4);result[:3,:3]=cv2.Rodrigues(rvec)[0];result[:3,3]=tvec.reshape(3)
    return result.tolist(),rms


def main():
    """Read a recent image, matching intrinsics and timestamped arm transform.

    한글: 최신 영상과 일치하는 내부 파라미터 및 시각 기반 팔 변환을 읽는다.
    """
    node=None
    try:
        board=json.load(sys.stdin);columns=int(board['columns']);rows=int(board['rows']);square=float(board['square_mm'])/1000
        if not 3<=columns<=20 or not 3<=rows<=20 or not .001<=square<=.5:raise ValueError('invalid_board')
        rclpy.init();node=Node('jetinspect_hand_eye_capture');buffer=Buffer();listener=TransformListener(buffer,node);bridge=CvBridge();images=[];infos=[]
        node.create_subscription(Image,'/depth_cam/color/image_raw',lambda msg:images.append(msg),qos_profile_sensor_data)
        node.create_subscription(CameraInfo,'/depth_cam/color/camera_info',lambda msg:infos.append(msg),qos_profile_sensor_data)
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=.1)
            if not images or not infos:continue
            img,info=images[-1],infos[-1];images[:]=images[-1:];infos[:]=infos[-1:]
            if img.header.frame_id!='depth_cam_color_optical_frame' or info.header.frame_id!=img.header.frame_id or (img.width,img.height)!=(info.width,info.height):continue
            image_sec=img.header.stamp.sec+img.header.stamp.nanosec*1e-9;info_sec=info.header.stamp.sec+info.header.stamp.nanosec*1e-9
            if abs(image_sec-info_sec)>.2 or not 0<=node.get_clock().now().nanoseconds*1e-9-image_sec<2:continue
            try:tf=buffer.lookup_transform('base_link','link4',Time.from_msg(img.header.stamp))
            except TransformException:continue
            target,rms=board_pose(bridge.imgmsg_to_cv2(img,desired_encoding='bgr8'),info,columns,rows,square)
            print(json.dumps({'result':{'base_T_link4':transform_matrix(tf.transform).tolist(),'camera_T_target':target},'reprojection_rms_px':rms,'image_stamp':image_sec},allow_nan=False));return
        raise ValueError('hand_eye_sources_unavailable')
    except (ValueError,RuntimeError,KeyError,cv2.error) as exc:
        print(json.dumps({'error':str(exc)}));sys.exit(1)
    finally:
        if node is not None:node.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
