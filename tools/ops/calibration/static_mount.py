#!/usr/bin/python3
"""Read the fixed camera mount chain from robot and camera TF publishers.

한글: 로봇과 카메라 TF 발행자의 고정 카메라 장착 체인만 읽는다.
"""
import json
import math
import sys
import time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from tf2_msgs.msg import TFMessage


def transform_matrix(transform):
    """Convert a normalized quaternion rigid transform to a 4x4 matrix.

    한글: 정규화된 쿼터니언 강체 변환을 4x4 행렬로 바꾼다.
    """
    t,q=transform.translation,transform.rotation
    values=[t.x,t.y,t.z,q.x,q.y,q.z,q.w]
    if not all(math.isfinite(v) for v in values):raise ValueError('invalid_static_tf')
    x,y,z,w=q.x,q.y,q.z,q.w;norm=math.sqrt(x*x+y*y+z*z+w*w)
    if abs(norm-1)>.01:raise ValueError('invalid_static_tf')
    x,y,z,w=(v/norm for v in (x,y,z,w))
    result=np.eye(4)
    result[:3,:3]=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                   [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                   [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
    result[:3,3]=[t.x,t.y,t.z]
    return result


def chain(transforms,parent,child):
    """Resolve only an unambiguous fixed child-to-parent chain.

    한글: 모호하지 않은 고정 자식→부모 체인만 계산한다.
    """
    entries={}
    for t in transforms:
        key=t.child_frame_id;name=t.header.frame_id
        if not key or not name:continue
        value=transform_matrix(t.transform)
        if key in entries and (entries[key][0]!=name or not np.allclose(entries[key][1],value,atol=1e-8,rtol=0)):
            raise ValueError('ambiguous_static_tf')
        entries[key]=(name,value)
    current=child;result=np.eye(4);visited=set()
    while current!=parent:
        if current in visited or current not in entries or len(visited)>20:raise ValueError('mount_tf_unavailable')
        visited.add(current);current,value=entries[current];result=value@result
    return result


def main():
    """Collect static transforms and output one validated mount matrix.

    한글: 정적 변환을 수집하고 검증된 장착 행렬 하나를 출력한다.
    """
    node=None
    try:
        rclpy.init();node=Node('jetinspect_static_mount');transforms=[]
        qos=QoSProfile(depth=100,reliability=ReliabilityPolicy.RELIABLE,durability=DurabilityPolicy.TRANSIENT_LOCAL)
        node.create_subscription(TFMessage,'/tf_static',lambda msg:transforms.extend(msg.transforms),qos)
        # The Orbbec driver republishes factory-fixed camera transforms on /tf
        # when tf_publish_rate is positive; do not include movable arm joints.
        # Orbbec은 tf_publish_rate가 양수이면 공장 고정 변환을 /tf로 재발행한다.
        # 움직이는 팔 관절은 수집하지 않는다.
        camera_frames={'depth_cam_depth_frame','depth_cam_color_frame','depth_cam_color_optical_frame'}
        node.create_subscription(TFMessage,'/tf',lambda msg:transforms.extend(
            t for t in msg.transforms if t.child_frame_id in camera_frames),10)
        end=time.monotonic()+8
        while time.monotonic()<end:rclpy.spin_once(node,timeout_sec=.1)
        value=chain(transforms,'camera_connect_link','depth_cam_color_optical_frame')
        print(json.dumps({'result':value.tolist()},allow_nan=False))
    except (ValueError,RuntimeError) as exc:
        print(json.dumps({'error':str(exc)}));sys.exit(1)
    finally:
        if node is not None:node.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
