"""Tests base_node open-loop odom_raw on a virtual serial port with a fake STM32 IMU stream.
No hardware needed. Expected values are printed next to each result.
"""
import os,pty,tty,subprocess,threading,time,struct,math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
def crc(b):
    c=0
    for x in b:
        c^=x
        for _ in range(8): c=(c>>1)^0x8C if c&1 else c>>1
    return c
def frame(func,data):
    f=bytes([0xAA,0x55,func,len(data)])+bytes(data); return f+bytes([crc(f[2:])])
master,slave=pty.openpty(); tty.setraw(master); path=os.ttyname(slave)
stop=threading.Event()
def feeder():   # stand-in for the STM32: IMU frames at 100 Hz (robot flat, sensor axes X right/Y back/Z down, gz=+0.1 rad/s?), drain motor frames
    import select
    while not stop.is_set():
        # sensor gz (deg/s): ROS z = -gz_sensor ; send gz_sensor = -5.73 deg/s -> +0.1 rad/s about ROS z
        imu=struct.pack("<6f",0.0,0.0,-0.96,0.0,0.0,-5.7296)
        os.write(master,frame(7,imu)); 
        if select.select([master],[],[],0)[0]: os.read(master,4096)
        time.sleep(0.01)
threading.Thread(target=feeder,daemon=True).start()
node=subprocess.Popen([os.path.expanduser("~/jetrover_ws/install/jetrover_base/lib/jetrover_base/base_node"),
   "--ros-args","-p",f"port:={path}"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
rclpy.init(); n=Node("odom_test"); pub=n.create_publisher(Twist,"cmd_vel",1)
odom=[None]; imus=[]
n.create_subscription(Odometry,"odom_raw",lambda m: odom.__setitem__(0,m),10)
n.create_subscription(Imu,"imu/data_raw",lambda m: imus.append(m),qos_profile_sensor_data)
def spin(t):
    end=time.monotonic()+t
    while time.monotonic()<end: rclpy.spin_once(n,timeout_sec=0.01)
def yaw(m): q=m.pose.pose.orientation; return 2*math.atan2(q.z,q.w)
def drive(vx,vy,wz,secs):
    end=time.monotonic()+secs
    while time.monotonic()<end:
        t=Twist(); t.linear.x=float(vx); t.linear.y=float(vy); t.angular.z=float(wz); pub.publish(t); spin(0.05)
def pose(): m=odom[0]; return (m.pose.pose.position.x,m.pose.pose.position.y,yaw(m))
spin(2.0)
p0=pose(); print(f"start           x={p0[0]:+.3f} y={p0[1]:+.3f} yaw={p0[2]:+.3f}  frame={odom[0].header.frame_id}->{odom[0].child_frame_id}")
drive(0.1,0,0,2.0); spin(1.0); p1=pose(); print(f"fwd 0.1 x 2s    x={p1[0]:+.3f} y={p1[1]:+.3f} yaw={p1[2]:+.3f}   (expect x~+0.20, incl. 0.5s timeout tail ~+0.25)")
drive(0,0.1,0,2.0); spin(1.0); p2=pose(); print(f"left 0.1 x 2s   dx={p2[0]-p1[0]:+.3f} dy={p2[1]-p1[1]:+.3f}              (expect dy~+0.20..0.25)")
drive(0,0,0.5,2.0); spin(1.0); p3=pose(); print(f"turn 0.5 x 2s   dyaw={p3[2]-p2[2]:+.3f} rad                 (expect ~+1.0..1.25)")
drive(0.1,0,0,1.0); spin(1.0); p4=pose(); print(f"fwd after turn  dx={p4[0]-p3[0]:+.3f} dy={p4[1]-p3[1]:+.3f}  yaw={p3[2]:+.2f}  (rotated frame: direction follows yaw)")
spin(1.0); p5=pose(); print(f"idle 1s         moved={math.hypot(p5[0]-p4[0],p5[1]-p4[1]):.4f} m       (expect 0: velocity zero after timeout)")
m=odom[0]; print(f"twist now       vx={m.twist.twist.linear.x} vy={m.twist.twist.linear.y} wz={m.twist.twist.angular.z}")
last=imus[-1]; print(f"imu/data_raw    frame={last.header.frame_id} n={len(imus)} az={last.linear_acceleration.z:+.2f} gz={last.angular_velocity.z:+.3f} (expect gz~+0.1-0.0169 bias, az>0)")
stop.set(); node.send_signal(2); node.wait(timeout=5); rclpy.shutdown()
