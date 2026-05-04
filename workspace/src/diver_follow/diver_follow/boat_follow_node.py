#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from std_msgs.msg import Float32MultiArray


def quat_to_yaw(x, y, z, w):
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def wrap_to_pi(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def clamp(value, low, high):
    return max(low, min(high, value))


class BoatFollowNode(Node):
    def __init__(self):
        super().__init__("boat_follow_node")

        self.target_pose = None
        self.boat_pose = None
        self.debug_counter = 0

        self.declare_parameter("goal_tolerance", 1.5)
        self.declare_parameter("kp_yaw", 0.8)
        self.declare_parameter("surge_base", 0.15)
        self.declare_parameter("surge_gain", 0.04)
        self.declare_parameter("surge_max", 0.45)
        self.declare_parameter("yaw_max", 0.35)

        self.declare_parameter("heading_offset", 1.5708)
        self.declare_parameter("turn_sign", 1.0)
        self.declare_parameter("swap_motors", False)

        self.create_subscription(
            PoseStamped,
            "/diver/seatrac_pose",
            self.target_callback,
            10,
        )

        self.create_subscription(
            PoseWithCovarianceStamped,
            "/marus_boat/pose",
            self.boat_callback,
            10,
        )

        self.pwm_pub = self.create_publisher(Float32MultiArray, "/marus_boat/pwm_out", 10)
        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info("boat_follow_node started")

    def target_callback(self, msg: PoseStamped):
        self.target_pose = msg

    def boat_callback(self, msg: PoseWithCovarianceStamped):
        self.boat_pose = msg

    def control_loop(self):
        if self.target_pose is None or self.boat_pose is None:
            return

        bx = self.boat_pose.pose.pose.position.x
        by = self.boat_pose.pose.pose.position.y

        tx = self.target_pose.pose.position.x
        ty = self.target_pose.pose.position.y

        dx = tx - bx
        dy = ty - by
        dist = math.hypot(dx, dy)

        desired_yaw = math.atan2(dy, dx)

        q = self.boat_pose.pose.pose.orientation
        raw_yaw = quat_to_yaw(q.x, q.y, q.z, q.w)

        heading_offset = float(self.get_parameter("heading_offset").value)
        turn_sign = float(self.get_parameter("turn_sign").value)
        swap_motors = bool(self.get_parameter("swap_motors").value)

        boat_yaw = wrap_to_pi(raw_yaw + heading_offset)
        yaw_err = wrap_to_pi(desired_yaw - boat_yaw)

        goal_tolerance = float(self.get_parameter("goal_tolerance").value)
        kp_yaw = float(self.get_parameter("kp_yaw").value)
        surge_base = float(self.get_parameter("surge_base").value)
        surge_gain = float(self.get_parameter("surge_gain").value)
        surge_max = float(self.get_parameter("surge_max").value)
        yaw_max = float(self.get_parameter("yaw_max").value)

        if dist < goal_tolerance:
            left = 0.0
            right = 0.0
            rear = 0.0
        else:
            surge = clamp(surge_base + surge_gain * dist, 0.0, surge_max)
            surge *= max(0.0, 1.0 - abs(yaw_err) / math.pi)

            yaw_cmd = clamp(turn_sign * kp_yaw * yaw_err, -yaw_max, yaw_max)

            left = clamp(surge - yaw_cmd, -1.0, 1.0)
            right = clamp(surge + yaw_cmd, -1.0, 1.0)
            rear = 0.0

            if swap_motors:
                left, right = right, left

        pwm_msg = Float32MultiArray()
        pwm_msg.data = [float(left), float(right), float(rear)]
        self.pwm_pub.publish(pwm_msg)

        self.debug_counter += 1
        if self.debug_counter % 10 == 0:
            self.get_logger().info(
                f"boat=({bx:.2f},{by:.2f}) target=({tx:.2f},{ty:.2f}) "
                f"dist={dist:.2f} err={yaw_err:.2f} pwm=[{left:.2f},{right:.2f},{rear:.2f}]"
            )


def main():
    rclpy.init()
    node = BoatFollowNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()