import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    # Declare the serial port as a launch argument (override per-robot)
    pico_port_arg = DeclareLaunchArgument(
        'pico_port',
        default_value='/dev/ttyACM0',
        description='Serial port for the Pico (e.g. /dev/ttyACM0)'
    )

    return LaunchDescription([
        pico_port_arg,

        # WebSocket Bridge (ROS2 topics -> Web UI)
        Node(
            package='lumi_ui',
            executable='bridge_node',
            name='bridge_node',
            output='screen'
        ),

        # Lumi AI Brain (voice + Gemini)
        Node(
            package='lumi_ui',
            executable='lumi_brain',
            name='lumi_brain',
            output='screen'
        ),

        # Face Tracker (camera -> /lumi/look)
        Node(
            package='lumi_ui',
            executable='face_tracker_node',
            name='face_tracker_node',
            output='screen'
        ),

        # Pico Serial Driver (motors + ears + touch)
        Node(
            package='lumi_ui',
            executable='pico_driver_node',
            name='pico_driver_node',
            output='screen',
            parameters=[{
                'port': LaunchConfiguration('pico_port'),
                'baud': 115200,
                'speed': 180,
            }]
        ),

        # Body Reaction Node (touch -> happy face + ear wiggle + spin)
        Node(
            package='lumi_ui',
            executable='lumi_body_node',
            name='lumi_body_node',
            output='screen'
        ),
    ])
