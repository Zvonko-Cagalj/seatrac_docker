#!/usr/bin/env python3
import random

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from visualization_msgs.msg import Marker


class SeatracSimNode(Node):
    def __init__(self):
        super().__init__("seatrac_sim_node")

        self.true_pose = None
        self.boat_pose = None

        self.declare_parameter("position_noise_std", 0.1)
        self.declare_parameter("publish_debug_marker", True)

        self.noise_std = float(self.get_parameter("position_noise_std").value)
        self.publish_debug_marker = bool(self.get_parameter("publish_debug_marker").value)

        self.create_subscription(PoseStamped, "/diver/true_pose", self.true_cb, 10)
        self.create_subscription(PoseWithCovarianceStamped, "/marus_boat/pose", self.boat_cb, 10)

        self.pose_pub = self.create_publisher(PoseStamped, "/diver/seatrac_pose", 10)
        self.marker_pub = self.create_publisher(Marker, "/unity/marker", 10)

        self.timer = self.create_timer(0.1, self.loop)
        self.get_logger().info("seatrac_sim_node started")

    def true_cb(self, msg):
        self.true_pose = msg

    def boat_cb(self, msg):
        self.boat_pose = msg

    def loop(self):
        if self.true_pose is None or self.boat_pose is None:
            return

        tx = self.true_pose.pose.position.x
        ty = self.true_pose.pose.position.y
        tz = self.true_pose.pose.position.z

        bx = self.boat_pose.pose.pose.position.x
        by = self.boat_pose.pose.pose.position.y
        bz = self.boat_pose.pose.pose.position.z

        # relative target position with small measurement noise
        rel_x = tx - bx
        rel_y = ty - by
        rel_z = tz - bz

        meas_rel_x = rel_x + random.gauss(0.0, self.noise_std)
        meas_rel_y = rel_y + random.gauss(0.0, self.noise_std)
        meas_rel_z = rel_z + random.gauss(0.0, self.noise_std)

        # estimated global target position
        est_x = bx + meas_rel_x
        est_y = by + meas_rel_y
        est_z = bz + meas_rel_z

        now = self.get_clock().now().to_msg()

        pose = PoseStamped()
        pose.header.stamp = now
        pose.header.frame_id = "map"
        pose.pose.position.x = est_x
        pose.pose.position.y = est_y
        pose.pose.position.z = est_z
        pose.pose.orientation.w = 1.0
        self.pose_pub.publish(pose)

        if self.publish_debug_marker:
            # delete old marker first
            delete_marker = Marker()
            delete_marker.header.stamp = now
            delete_marker.header.frame_id = "map"
            delete_marker.ns = "diver_seatrac"
            delete_marker.id = 2
            delete_marker.action = Marker.DELETE
            self.marker_pub.publish(delete_marker)

            # add updated marker
            marker = Marker()
            marker.header.stamp = now
            marker.header.frame_id = "map"
            marker.ns = "diver_seatrac"
            marker.id = 2
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            marker.pose = pose.pose
            marker.scale.x = 1.6
            marker.scale.y = 1.6
            marker.scale.z = 1.6
            marker.color.r = 0.0
            marker.color.g = 1.0
            marker.color.b = 0.0
            marker.color.a = 1.0
            self.marker_pub.publish(marker)


def main():
    rclpy.init()
    node = None
    try:
        node = SeatracSimNode()
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