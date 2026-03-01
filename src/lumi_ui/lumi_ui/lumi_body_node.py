"""
lumi_body_node.py
------------------
Lumi's body reaction node. Listens to sensor events and
produces coordinated physical + UI responses.

Subscribes:
  /lumi/touch     (std_msgs/Bool)    -> head touch events

Publishes:
  /lumi/emotion   (std_msgs/String)  -> emotion to face UI
  /lumi/speak     (std_msgs/Bool)    -> talk animation toggle
  /lumi/ear_cmd   (std_msgs/String)  -> ear servo command to Pico
  /cmd_vel        (geometry_msgs/Twist) -> (optional) happy dance movement
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from geometry_msgs.msg import Twist
import time
import threading


class LumiBodyNode(Node):
    def __init__(self):
        super().__init__('lumi_body_node')

        # Publishers
        self.emotion_pub = self.create_publisher(String, '/lumi/emotion', 10)
        self.speak_pub   = self.create_publisher(Bool,   '/lumi/speak',   10)
        self.ear_pub     = self.create_publisher(String, '/lumi/ear_cmd', 10)
        self.cmd_vel_pub = self.create_publisher(Twist,  '/cmd_vel',      10)

        # Subscribers
        self.create_subscription(Bool, '/lumi/touch', self.touch_callback, 10)

        self.get_logger().info('Lumi Body Node started. Listening for touch...')

    # ---------------------------------------------------------------
    # Touch Sensor Reaction
    # ---------------------------------------------------------------
    def touch_callback(self, msg: Bool):
        if not msg.data:
            return

        self.get_logger().info('Touch detected! Triggering happy reaction...')

        # Run the full reaction in a background thread so we don't block
        t = threading.Thread(target=self._happy_reaction, daemon=True)
        t.start()

    def _happy_reaction(self):
        """Full coordinated reaction to a head touch."""

        # 1. Make face go happy
        self._set_emotion('happy')

        # 2. Wiggle the ears
        self._send_ear_cmd('WIGGLE')

        # 3. Little happy spin (in place) — wheels
        self._happy_spin()

        # 4. Hold happy for 3 seconds
        time.sleep(3.0)

        # 5. Return to neutral
        self._set_emotion('neutral')
        # Reset ears to center
        self._send_ear_cmd('E90:90')

    def _happy_spin(self):
        """Spin in place briefly as a happy dance."""
        twist = Twist()
        twist.angular.z = 1.5    # Spin left at ~1.5 rad/s
        self.cmd_vel_pub.publish(twist)
        time.sleep(0.8)

        twist.angular.z = -1.5   # Spin right
        self.cmd_vel_pub.publish(twist)
        time.sleep(0.8)

        # Stop
        self.cmd_vel_pub.publish(Twist())

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------
    def _set_emotion(self, emotion: str):
        msg = String()
        msg.data = emotion
        self.emotion_pub.publish(msg)

    def _send_ear_cmd(self, cmd: str):
        msg = String()
        msg.data = cmd
        self.ear_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LumiBodyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
