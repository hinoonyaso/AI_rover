"""Check simulation DDS isolation. / 시뮬레이션 DDS 격리 조건을 검사한다."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from gazebo_nav_trial import require_simulation


class GazeboTransportTests(unittest.TestCase):
    def test_only_validated_profile_accepts_subnet_discovery(self):
        profile = str(Path(__file__).resolve().with_name('fastdds-loopback.xml'))
        base = {'ROS_DOMAIN_ID': '31', 'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp',
                'ROS_AUTOMATIC_DISCOVERY_RANGE': 'SUBNET', 'GZ_IP': '127.0.0.1',
                'FASTRTPS_DEFAULT_PROFILES_FILE': profile}
        with patch.dict(os.environ, base, clear=True):
            require_simulation()
            for key, value in (('FASTRTPS_DEFAULT_PROFILES_FILE', '/tmp/other.xml'),
                               ('GZ_IP', '0.0.0.0'), ('ROS_DOMAIN_ID', '98'),
                               ('ROS_STATIC_PEERS', '192.0.2.1'),
                               ('FASTDDS_DEFAULT_PROFILES_FILE', '/tmp/other.xml'),
                               ('FASTDDS_BUILTIN_TRANSPORTS', 'UDPv4')):
                with self.subTest(key=key), patch.dict(os.environ, {key: value}):
                    with self.assertRaises(RuntimeError):
                        require_simulation()
            with patch.object(Path, 'read_bytes', return_value=b'altered profile'):
                with self.assertRaises(RuntimeError):
                    require_simulation()

    def test_legacy_localhost_without_profile(self):
        with patch.dict(os.environ, {'ROS_DOMAIN_ID': '31', 'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp',
                                     'ROS_AUTOMATIC_DISCOVERY_RANGE': 'LOCALHOST'}, clear=True):
            require_simulation()


if __name__ == '__main__':
    unittest.main()
