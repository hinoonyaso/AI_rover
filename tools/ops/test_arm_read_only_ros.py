#!/usr/bin/python3
"""Prove opt-in arm observation emits only read frames on a fake serial port.

한글: 가상 시리얼에서 팔 관측 모드가 읽기 프레임만 보내는지 검증한다.
"""
import os
import pty
import select
import signal
import subprocess
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool


def packet(function,payload):
    """Encode one RRC packet. / RRC 패킷 하나를 인코딩한다."""
    body=bytes([function,len(payload)])+bytes(payload);crc=0
    for value in body:
        crc^=value
        for _ in range(8):crc=(crc>>1)^(0x8c if crc&1 else 0)
    return b'\xaa\x55'+body+bytes([crc])


def main():
    """Feed synthetic servo replies and reject every non-read command.

    한글: 가상 서보 응답을 공급하고 읽기 외 명령은 모두 거부한다.
    """
    if os.environ.get('ROS_DOMAIN_ID')!='189':raise RuntimeError('requires isolated domain 189')
    master,slave=pty.openpty();executable='/tmp/jetrover-calibration-install/jetrover_base/lib/jetrover_base/base_node'
    proc=subprocess.Popen([executable,'--ros-args','-p','port:='+os.ttyname(slave),'-p','sensor_only:=true',
        '-p','sensor_arm_read_enabled:=true','-p','publish_arm_joint_states:=true','-p','arm_command_enabled:=true',
        '-p','arm_move_home_on_start:=true','-p','clear_estop_on_start:=true','-p','motor_stop_frame_on_stop:=true'],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    rclpy.init();node=Node('arm_read_only_test');observed=[]
    node.create_subscription(JointState,'/joint_states',lambda m:observed.append(m),10)
    motor=node.create_publisher(Twist,'/cmd_vel',10);arm=node.create_publisher(JointState,'/arm/command',10);torque=node.create_publisher(Bool,'/arm/torque',10)
    received=bytearray();count=0
    def drain():
        nonlocal count
        if select.select([master],[],[],0)[0]:received.extend(os.read(master,4096))
        while len(received)>=5:
            if received[:2]!=b'\xaa\x55':raise RuntimeError('invalid serial prefix')
            length=received[3]+5
            if len(received)<length:break
            raw=bytes(received[:length]);del received[:length]
            if len(raw)!=7 or raw[2]!=5 or raw[3]!=2 or raw[4] not in (5,9) or raw!=packet(raw[2],raw[4:-1]):
                raise RuntimeError('non-read serial frame: '+raw.hex())
            count+=1;servo=raw[5]
            response=[servo,5,0,244,1] if raw[4]==5 else [servo,9,0,35]
            os.write(master,packet(5,response))
    try:
        end=time.monotonic()+12
        while time.monotonic()<end:
            if proc.poll() is not None:raise RuntimeError('base node exited')
            msg=Twist();msg.linear.x=.2;motor.publish(msg);arm.publish(JointState());msg2=Bool();msg2.data=True;torque.publish(msg2)
            rclpy.spin_once(node,timeout_sec=.05);drain()
            if any(len(m.name)>=6 for m in observed) and count>=20:break
        if not any(len(m.name)>=6 for m in observed):raise RuntimeError('missing servo joint states')
        if motor.get_subscription_count() or arm.get_subscription_count() or torque.get_subscription_count():raise RuntimeError('actuator command subscriber exists')
    finally:
        proc.send_signal(signal.SIGINT)
        try:proc.wait(timeout=8)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
        drain();node.destroy_node();rclpy.shutdown();os.close(master);os.close(slave)
    if received:raise RuntimeError('incomplete serial output')
    print(f'PASS read frames={count}; six joints observed; actuator subscribers and writes=0')

if __name__=='__main__':main()
