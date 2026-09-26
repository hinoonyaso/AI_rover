"""Stand-in for base_node (publishes imu/data_raw, has a gyro_bias parameter) to test
tools/imu_calibration scripts without the robot.
"""
import rclpy,sys
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu
rclpy.init(); n=Node("base_node")
n.declare_parameter("gyro_bias",[0.197,0.168,-0.017])
p=n.create_publisher(Imu,"imu/data_raw",qos_profile_sensor_data)
def tick():
    m=Imu(); m.linear_acceleration.z=9.46; m.linear_acceleration.x=-0.3; m.linear_acceleration.y=-0.57
    m.angular_velocity.x=0.010; m.angular_velocity.y=-0.020; m.angular_velocity.z=0.005   # residual bias after subtraction
    p.publish(m)
n.create_timer(0.009,tick); rclpy.spin(n)
