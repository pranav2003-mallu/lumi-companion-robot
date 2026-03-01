import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'lumi_ui'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'web'), glob('web/*')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mallu',
    maintainer_email='pranavspillai2003@gmail.com',
    description='Lumi UI Package',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'bridge_node = lumi_ui.bridge_node:main',
            'lumi_brain = lumi_ui.lumi_brain:main',
            'face_tracker_node = lumi_ui.face_tracker_node:main',
            'pico_driver_node = lumi_ui.pico_driver_node:main',
            'lumi_body_node = lumi_ui.lumi_body_node:main',
        ],
    },
)
