"""
pico_driver_node.py
--------------------
ROS2 node that talks serial to the Lumi Pico firmware.

Subscribes:
  /cmd_vel        (geometry_msgs/Twist)   -> F/B/L/R/S commands to Pico
  /lumi/ear_cmd   (std_msgs/String)       -> e.g. "WIGGLE" or "E120:60"

Publishes:
  /lumi/touch     (std_msgs/Bool)         -> True when head is touched
  /odom_raw       (std_msgs/String)       -> raw "left:right" encoder ticks
"""

import serial
import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool, String

# ---- Config: change this to your Pico's serial port ----
PICO_PORT   = '/dev/ttyACM0'
PICO_BAUD   = 115200
# --------------------------------------------------------

LINEAR_THRESHOLD  = 0.05   # m/s — below this we treat as zero
ANGULAR_THRESHOLD = 0.05   # rad/s

class PicoDriverNode(Node):
    def __init__(self):
        super().__init__('pico_driver_node')

        # Parameters (can be overridden in launch file)
        self.declare_parameter('port', PICO_PORT)
        self.declare_parameter('baud', PICO_BAUD)
        self.declare_parameter('speed', 180)

        port = self.get_parameter('port').value
        baud = self.get_parameter('baud').value
        self.speed = self.get_parameter('speed').value

        # Publishers
        self.touch_pub   = self.create_publisher(Bool,   '/lumi/touch',    10)
        self.odom_pub    = self.create_publisher(String, '/odom_raw',       10)

        # Subscribers
        self.create_subscription(Twist,  '/cmd_vel',       self.cmd_vel_cb,  10)
        self.create_subscription(String, '/lumi/ear_cmd',  self.ear_cmd_cb,  10)

        # Serial connection
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            self.get_logger().info(f'Connected to Pico on {port} at {baud} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Cannot open serial port {port}: {e}')
            self.ser = None

        # Start background thread to read from Pico
        if self.ser:
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()

        self.get_logger().info('Pico Driver Node started.')

    # ------------------------------------------------------------------
    # CMD_VEL -> Motor Commands
    # ------------------------------------------------------------------
    def cmd_vel_cb(self, msg: Twist):
        if not self.ser:
            return

        lin = msg.linear.x
        ang = msg.angular.z

        if abs(lin) < LINEAR_THRESHOLD and abs(ang) < ANGULAR_THRESHOLD:
            cmd = 'S'
        elif abs(ang) > LINEAR_THRESHOLD:
            cmd = 'L' if ang > 0 else 'R'
        elif lin > 0:
            cmd = 'F'
        else:
            cmd = 'B'

        self._send(cmd)

    # ------------------------------------------------------------------
    # Ear Command
    # ------------------------------------------------------------------
    def ear_cmd_cb(self, msg: String):
        cmd = msg.data.strip()
        if cmd == 'WIGGLE':
            self._send('WIGGLE_EARS')
        elif cmd.startswith('E'):
            self._send(cmd)

    # ------------------------------------------------------------------
    # Serial Write Helper
    # ------------------------------------------------------------------
    def _send(self, cmd: str):
        try:
            self.ser.write((cmd + '\n').encode())
        except Exception as e:
            self.get_logger().warn(f'Serial write error: {e}')

    # ------------------------------------------------------------------
    # Background Read Loop (Pico → Pi)
    # ------------------------------------------------------------------
    def _read_loop(self):
        while rclpy.ok():
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
                if not line:
                    continue

                if line.startswith('ENC:'):
                    # ENC:left:right
                    parts = line[4:].split(':')
                    if len(parts) == 2:
                        odom_msg = String()
                        odom_msg.data = f'{parts[0]}:{parts[1]}'
                        self.odom_pub.publish(odom_msg)

                elif line == 'TOUCH:1':
                    touch_msg = Bool()
                    touch_msg.data = True
                    self.touch_pub.publish(touch_msg)
                    self.get_logger().info('Head touch detected!')

            except Exception as e:
                self.get_logger().warn(f'Serial read error: {e}')

    def destroy_node(self):
        if self.ser and self.ser.is_open:
            self._send('S')   # Safety stop
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PicoDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
