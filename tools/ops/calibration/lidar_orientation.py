#!/usr/bin/python3
"""Read a bounded LiDAR scan and TF for a user-assisted direction check.

한글: 사용자 보조 방향 점검을 위해 제한된 LiDAR 스캔과 TF를 읽는다.
"""
import json
import math
import sys
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from rclpy.duration import Duration
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener, TransformException


def main():
    """Collect scan without publishing robot commands. / 로봇 명령 없이 스캔을 수집한다."""
    node = None
    try:
        expected = float(sys.argv[1]); max_range = float(sys.argv[2])
        if not math.isfinite(expected) or not -180 <= expected <= 180 or not math.isfinite(max_range) or not .1 <= max_range <= 5:
            raise ValueError('invalid_reference')
        rclpy.init(); node=Node('jetinspect_lidar_orientation')
        buffer=Buffer(); listener=TransformListener(buffer,node)
        samples=[]
        node.create_subscription(LaserScan, '/scan', lambda msg: samples.append(msg), qos_profile_sensor_data)
        deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=.1)
            if len(samples)>100: samples.pop(0)
        if not samples: raise ValueError('scan_unavailable')
        scan=samples[-1]
        if not scan.header.frame_id: raise ValueError('scan_frame_unconfirmed')
        # Timestamped lookup prevents using an unrelated TF sample for a moving frame.
        # 한글: 시각을 지정해 움직이는 프레임의 무관한 TF를 사용하지 않는다.
        try:
            tf=buffer.lookup_transform('base_link',scan.header.frame_id,Time.from_msg(scan.header.stamp),Duration(seconds=1.0))
        except TransformException:
            raise ValueError('scan_tf_unavailable') from None
        q=tf.transform.rotation
        norm=math.sqrt(q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w)
        if not math.isfinite(norm) or abs(norm-1)>0.01 or abs(q.x)>0.05 or abs(q.y)>0.05:
            raise ValueError('scan_tf_tilted')
        yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
        tx,ty=tf.transform.translation.x,tf.transform.translation.y
        if not all(math.isfinite(x) for x in (tx,ty,scan.angle_min,scan.angle_increment)):
            raise ValueError('invalid_scan')
        points=[]
        for i,r in enumerate(scan.ranges):
            if math.isfinite(r) and scan.range_min<=r<=min(scan.range_max,max_range):
                angle=scan.angle_min+i*scan.angle_increment+yaw
                x,y=tx+r*math.cos(angle),ty+r*math.sin(angle)
                points.append((math.hypot(x,y),math.atan2(y,x)))
        if len(points)<5: raise ValueError('scan_no_target')
        points.sort(); closest=points[:max(5,len(points)//20)]
        bearing=math.degrees(math.atan2(sum(math.sin(a) for _,a in closest),sum(math.cos(a) for _,a in closest)))
        diff=(bearing-expected+180)%360-180
        result={'scan_frame':scan.header.frame_id,'reference_frame':'base_link','scan_count':len(samples),
                'expected_bearing_deg':expected,'observed_bearing_deg':bearing,'difference_deg':diff,
                'nearest_m':closest[0][0],'max_range_m':max_range,'point_count':len(closest),
                'target_identity_verified':False,'applied':False}
        print(json.dumps({'result':result},allow_nan=False))
    except (ValueError, RuntimeError, IndexError) as exc:
        print(json.dumps({'error':str(exc)}));sys.exit(1)
    finally:
        if node is not None:node.destroy_node();rclpy.shutdown()

if __name__ == '__main__':main()
