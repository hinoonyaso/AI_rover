#!/usr/bin/python3
"""Isolated ROS arm observation integration; no hardware commands.

한글: 격리된 ROS 팔 상태 연동 시험이며 하드웨어 명령은 보내지 않는다.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
import rclpy
from rclpy.executors import SingleThreadedExecutor
from sensor_msgs.msg import JointState
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from ros_monitor import SensorMonitor

with tempfile.TemporaryDirectory() as directory:
    os.environ['HOME'] = directory
    rclpy.init()
    base = rclpy.create_node('base_node')
    base.declare_parameter('arm_joint_names', ['joint1', 'r_joint'])
    base.declare_parameter('arm_servo_ids', [1, 10])
    base.declare_parameter('arm_joint_offsets_rad', [0.1, -0.2])
    joint_pub = base.create_publisher(JointState, '/joint_states', 10)
    stats_pub = base.create_publisher(DiagnosticArray, '/arm/servo_stats', 10)
    monitor = SensorMonitor()
    executor = SingleThreadedExecutor()
    executor.add_node(base)
    executor.add_node(monitor)
    joint = JointState(name=['joint1', 'r_joint'], position=[0.1, 0.2])
    stats = DiagnosticArray(status=[DiagnosticStatus(hardware_id='1', values=[KeyValue(key='age_s', value='0.1')]),
                                    DiagnosticStatus(hardware_id='10', values=[KeyValue(key='age_s', value='-1')])])
    try:
        end = time.monotonic() + 12
        while time.monotonic() < end:
            joint_pub.publish(joint)
            stats_pub.publish(stats)
            executor.spin_once(timeout_sec=0.05)
            if monitor.arm_mapping and monitor.arm_joints and monitor.arm_diagnostics:
                break
        assert monitor.arm_mapping == {'joint1': 1, 'r_joint': 10}, monitor.arm_mapping
        assert monitor.arm_offsets == {'joint1':0.1, 'r_joint':-0.2}
        monitor.write_status()
        saved=json.loads((Path(directory)/'.local/share/jetinspect-ops/run/ros-status.json').read_text())
        assert saved['arm']['source_confirmed'] is True
        assert saved['arm']['joints']['joint1']['offset_rad'] == 0.1
        from arm_observation import arm_observation
        result = arm_observation(monitor.arm_mapping, monitor.arm_mapping_at, monitor.arm_joints, monitor.arm_joint_at,
                                 monitor.arm_diagnostics, monitor.arm_diagnostics_at, time.time())
        assert result['joints']['joint1']['fresh']
        assert not result['joints']['r_joint']['fresh']
        print('PASS isolated ROS runtime mapping, joint messages, and servo response freshness')
    finally:
        executor.shutdown()
        monitor.destroy_node()
        base.destroy_node()
        rclpy.shutdown()
