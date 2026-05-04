#!/usr/bin/env python3
import sys
import termios
import tty
import threading

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from visualization_msgs.msg import Marker


HELP = """
WASD: move in x/y
R/F : move up/down
Q   : quit

W = +y
S = -y
A = -x
D = +x
R = +z
F = -z
"""


class DiverKeyboardNode(Node):
    def __init__(self):
        super().__init__("diver_keyboard_node")

        self.pose_pub = self.create_publisher(PoseStamped, "/diver/true_pose", 10)
        self.marker_pub = self.create_publisher(Marker, "/unity/marker", 10)

        self.declare_parameter("step_xy", 0.5)
        self.declare_parameter("step_z", 0.25)
        self.declare_parameter("start_x", 5.0)
        self.declare_parameter("start_y", -10.0)
        self.declare_parameter("start_z", 0.5)
        self.declare_parameter("marker_scale", 2.0)

        self.x = float(self.get_parameter("start_x").value)
        self.y = float(self.get_parameter("start_y").value)
        self.z = float(self.get_parameter("start_z").value)

        self.step_xy = float(self.get_parameter("step_xy").value)
        self.step_z = float(self.get_parameter("step_z").value)
        self.marker_scale = float(self.get_parameter("marker_scale").value)

        self.lock = threading.Lock()
        self.running = True

        self.settings = termios.tcgetattr(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())

        self.key_thread = threading.Thread(target=self.keyboard_loop, daemon=True)
        self.key_thread.start()

        self.timer = self.create_timer(0.05, self.publish_pose_and_marker)

        self.get_logger().info("diver_keyboard_node started")
        self.get_logger().info(HELP)
        self.print_pose()

    def keyboard_loop(self):
        while self.running and rclpy.ok():
            try:
                key = sys.stdin.read(1)
            except Exception:
                break

            if not key:
                continue

            moved = False

            with self.lock:
                if key == "w":
                    self.y += self.step_xy
                    moved = True
                elif key == "s":
                    self.y -= self.step_xy
                    moved = True
                elif key == "a":
                    self.x -= self.step_xy
                    moved = True
                elif key == "d":
                    self.x += self.step_xy
                    moved = True
                elif key == "r":
                    self.z += self.step_z
                    moved = True
                elif key == "f":
                    self.z -= self.step_z
                    moved = True
                elif key == "q":
                    self.running = False
                    break

                # keep movement inside a reasonable area for debugging
                self.x = max(-30.0, min(30.0, self.x))
                self.y = max(-30.0, min(30.0, self.y))
                self.z = max(-2.0, min(3.0, self.z))

            if moved:
                self.print_pose()

    def print_pose(self):
        self.get_logger().info(
            f"diver true pose -> x={self.x:.2f}, y={self.y:.2f}, z={self.z:.2f}"
        )

    def publish_pose_and_marker(self):
        with self.lock:
            x = self.x
            y = self.y
            z = self.z

        now = self.get_clock().now().to_msg()

        pose = PoseStamped()
        pose.header.stamp = now
        pose.header.frame_id = "map"
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.w = 1.0
        self.pose_pub.publish(pose)

        # delete old marker first
        delete_marker = Marker()
        delete_marker.header.stamp = now
        delete_marker.header.frame_id = "map"
        delete_marker.ns = "diver_true"
        delete_marker.id = 1
        delete_marker.action = Marker.DELETE
        self.marker_pub.publish(delete_marker)

        # add updated marker
        marker = Marker()
        marker.header.stamp = now
        marker.header.frame_id = "map"
        marker.ns = "diver_true"
        marker.id = 1
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose = pose.pose
        marker.scale.x = self.marker_scale
        marker.scale.y = self.marker_scale
        marker.scale.z = self.marker_scale
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0
        marker.color.a = 1.0
        self.marker_pub.publish(marker)

    def destroy_node(self):
        self.running = False
        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.settings)
        except Exception:
            pass
        super().destroy_node()


def main():
    rclpy.init()
    node = None
    try:
        node = DiverKeyboardNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()