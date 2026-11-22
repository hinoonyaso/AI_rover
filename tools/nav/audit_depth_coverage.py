#!/usr/bin/env python3
"""Audit recorded depth cloud heights and the rear-left coverage.

기록된 깊이 장애물 점의 높이와 좌측 후방 관측 범위를 확인한다.
Usage: python3 tools/nav/audit_depth_coverage.py BAG START_SECONDS END_SECONDS
"""
import sys
from pathlib import Path
import yaml
import numpy as np, rosbag2_py, rclpy
from rclpy.duration import Duration
from rclpy.serialization import deserialize_message
from rclpy.time import Time
from rosidl_runtime_py.utilities import get_message
from sensor_msgs_py import point_cloud2
from tf2_ros import Buffer
P=sys.argv[1]; start=float(sys.argv[2]); end=float(sys.argv[3])
def reader():
 r=rosbag2_py.SequentialReader();r.open(rosbag2_py.StorageOptions(uri=P,storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'));return r
rclpy.init();b=Buffer(cache_time=Duration(seconds=400));r=reader();T=get_message('tf2_msgs/msg/TFMessage');tfnum=0
while r.has_next():
 topic,raw,t=r.read_next()
 if topic not in ('/tf','/tf_static'):continue
 for tr in deserialize_message(raw,T).transforms:
  try:
   (b.set_transform_static if topic=='/tf_static' else b.set_transform)(tr,'recorded');tfnum+=1
  except Exception:pass
print('TF inserted',tfnum,flush=True)
r=reader();PCL=get_message('sensor_msgs/msg/PointCloud2');base=yaml.safe_load((Path(P)/'metadata.yaml').read_text())['rosbag2_bagfile_information']['starting_time']['nanoseconds_since_epoch']*1e-9;last=-100;ok=0;fail=0; xmin=[]; rearframes=0; lowframes=0; nf=[]
while r.has_next():
 topic,raw,t=r.read_next()
 if topic!='/depth_cam/depth/points_sparse':continue
 sec=t*1e-9-base
 if not (start<=sec<=end) or sec-last<0.10:continue
 last=sec;m=deserialize_message(raw,PCL)
 try:
  tr=b.lookup_transform('base_footprint',m.header.frame_id,Time.from_msg(m.header.stamp)).transform
  points=point_cloud2.read_points_numpy(m,field_names=['x','y','z'],skip_nans=True)
  if points.size==0:print('t %.1f empty'%sec);continue
  q=tr.rotation;x,y,z,w=q.x,q.y,q.z,q.w
  R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
  p=points@R.T+np.array([tr.translation.x,tr.translation.y,tr.translation.z]);
  zone=(p[:,0]>-.25)&(p[:,0]<1.2)&(abs(p[:,1])<.6)
  low=zone&(p[:,2]>=.02)&(p[:,2]<.06);high=zone&(p[:,2]>=.06)&(p[:,2]<.15)
  rearleft=zone&(p[:,0]<0)&(p[:,1]>0)
  xmin.append(float(p[:,0].min())); rearframes+=int(rearleft.any()); lowframes+=int(low.any()); nf.append(int(low.sum())); ok+=1
 except Exception as e:fail+=1;print('t %.1f unavailable %s'%(sec,str(e)[:180]),flush=True)
print('processed',ok,'failed',fail,'min_forward',round(min(xmin),3) if xmin else None,'rear_left_frames',rearframes,'frames_with_2_6cm_points',lowframes,'low_points_median',round(float(np.median(nf)),1) if nf else None)
rclpy.shutdown()
