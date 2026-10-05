# 한글: /cmd_vel을 ±V m/s로 2초마다 번갈아 20Hz로 발행한다. 반드시 바퀴를 띄운 상태에서 사용.
"""Publish /cmd_vel alternating +-V m/s every 2 s at 20 Hz for N seconds.
Usage: python3 cmd_vel_alternate.py 0.2 180. WHEELS OFF THE GROUND.
"""
import rclpy,time,sys
from rclpy.node import Node
from geometry_msgs.msg import Twist
rclpy.init(); n=Node("alt_pub"); p=n.create_publisher(Twist,"cmd_vel",1)
V=float(sys.argv[1]); DUR=float(sys.argv[2]); t0=time.monotonic()
try:
    while time.monotonic()-t0<DUR:
        m=Twist(); m.linear.x=V if int((time.monotonic()-t0)/2)%2==0 else -V
        p.publish(m); time.sleep(0.05)
finally:
    p.publish(Twist()); time.sleep(0.2); rclpy.shutdown()
