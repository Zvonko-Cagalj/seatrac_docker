from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="diver_follow",
            executable="diver_keyboard_node",
            name="diver_keyboard_node",
            parameters=[{
                "step_xy": 0.5,
                "step_z": 0.25,
                "start_x": 5.0,
                "start_y": -10.0,
                "start_z": 0.5,
                "marker_scale": 1.2,
            }],
            output="screen",
            emulate_tty=True,
        ),
        Node(
            package="diver_follow",
            executable="seatrac_sim_node",
            name="seatrac_sim_node",
            parameters=[{
                "position_noise_std": 0.1,
                "publish_debug_marker": True,
            }],
            output="screen",
        ),
        Node(
            package="diver_follow",
            executable="boat_follow_node",
            name="boat_follow_node",
            parameters=[{
                "goal_tolerance": 1.5,
                "kp_yaw": 0.8,
                "surge_base": 0.15,
                "surge_gain": 0.04,
                "surge_max": 0.45,
                "yaw_max": 0.35,
                "heading_offset": 1.5708,
                "turn_sign": 1.0,
                "swap_motors": False,
            }],
            output="screen",
        ),
    ])