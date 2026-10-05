from glob import glob

from setuptools import find_packages, setup

package_name = 'jetrover_microros'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sang',
    maintainer_email='sang@todo.todo',
    description='Host side of the micro-ROS STM32 firmware',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'rrc_bridge = jetrover_microros.rrc_bridge:main',
        ],
    },
)
