"""
pico_driver_node.py
--------------------
ROS2 node that talks serial to the Lumi Pico firmware.

Subscribes:
  /cmd_vel        (geometry_msgs/Twist)   -> motor speed commands to Pico
  /lumi/ear_cmd   (std_msgs/String)       -> e.g. "WIGGLE" or "E120:60"

Publishes:
  /lumi/touch     (std_msgs/Bool)         -> True when head is touched
  /odom_raw       (std_msgs/String)       -> raw "left:right" encoder ticks
"""

import serial
import threading
import time
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
        self.declare_parameter('speed', 190)

        port = self.get_parameter('port').value
        baud = self.get_parameter('baud').value
        self.speed = self.get_parameter('speed').value

        # Publishers
        self.touch_pub    = self.create_publisher(Bool,   '/lumi/touch',    10)
        self.odom_pub     = self.create_publisher(String, '/odom_raw',       10)
        self.obstacle_pub = self.create_publisher(String, '/lumi/obstacle',  10)

        # Subscribers
        self.create_subscription(Twist,  '/cmd_vel',       self.cmd_vel_cb,  10)
        self.create_subscription(String, '/lumi/ear_cmd',  self.ear_cmd_cb,  10)

        # IR sensor state: [front_left, front_right, back_left, back_right]
        # 1 = obstacle detected, 0 = clear
        self.ir = {'FL': 0, 'FR': 0, 'BL': 0, 'BR': 0}
        self._last_obstacle_dir = None  # Track last published direction

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
    #
    # Firmware protocol: 'm <leftPWM> <rightPWM>\r'   (MOTOR_SPEEDS cmd)
    # where leftPWM and rightPWM are integers in range [-255, 255]
    # The firmware parses chr==13 (carriage return '\r') as end-of-command
    # ------------------------------------------------------------------
    def cmd_vel_cb(self, msg: Twist):
        if not self.ser:
            return

        lin = msg.linear.x   # Positive = forward command
        ang = msg.angular.z

        # Stop if both are zero
        if abs(lin) < LINEAR_THRESHOLD and abs(ang) < ANGULAR_THRESHOLD:
            self._send_motors(0, 0)
            return

        # --- IR Obstacle Check ---
        front_blocked = self.ir['FL'] or self.ir['FR']
        back_blocked  = self.ir['BL'] or self.ir['BR']

        # Block forward motion if front obstacle
        if lin > LINEAR_THRESHOLD and front_blocked:
            self._send_motors(0, 0)
            self._publish_obstacle('front')
            return

        # Block backward motion if rear obstacle
        if lin < -LINEAR_THRESHOLD and back_blocked:
            self._send_motors(0, 0)
            self._publish_obstacle('back')
            return

        # Allow the motion — reset obstacle state
        self._last_obstacle_dir = None

        spd = self.speed  # max PWM (default 180)

        # Differential drive: convert linear + angular velocity to left/right PWM
        # Positive angular.z = turn left (CCW), so left wheel goes back, right goes forward
        if abs(lin) < LINEAR_THRESHOLD:
            # Pure in-place rotation
            if ang > 0:       # Turn left in place
                left  = -spd
                right =  spd
            else:             # Turn right in place
                left  =  spd
                right = -spd
        elif lin > 0:
            # Moving forward
            if abs(ang) < ANGULAR_THRESHOLD:
                left = right = spd          # Straight forward
            elif ang > 0:
                left  = int(spd * 0.5)     # Curve left
                right = spd
            else:
                left  = spd               # Curve right
                right = int(spd * 0.5)
        else:
            # Moving backward
            if abs(ang) < ANGULAR_THRESHOLD:
                left = right = -spd        # Straight backward
            elif ang > 0:
                left  = int(-spd * 0.5)   # Curve left backward
                right = -spd
            else:
                left  = -spd             # Curve right backward
                right = int(-spd * 0.5)

        self._send_motors(left, right)

    def _send_motors(self, left: int, right: int):
        """Send 'm left right\r' to firmware (MOTOR_SPEEDS command).
        Negating both speeds because motors are physically wired in reverse."""
        left  = max(-255, min(255, -left))   # Negate to fix physical wiring
        right = max(-255, min(255, -right))  # Negate to fix physical wiring
        cmd = f'm {left} {right}\r'
        self._send_raw(cmd)
        self.get_logger().debug(f'Motors: L={left} R={right}')

    # ------------------------------------------------------------------
    # Ear Servo Commands
    # Firmware protocol: 's <pin> <angle>\r'
    # LEFT_EAR_PIN = 0, RIGHT_EAR_PIN = 1, angles 0-180 degrees
    # ------------------------------------------------------------------
    LEFT_EAR_PIN  = 0
    RIGHT_EAR_PIN = 1

    def ear_cmd_cb(self, msg: String):
        cmd = msg.data.strip()

        if cmd == 'WIGGLE':
            # Run a quick wiggle animation in a background thread
            threading.Thread(target=self._wiggle_ears, daemon=True).start()

        elif cmd.startswith('E'):
            # Format: E<left_angle>:<right_angle>  e.g. E90:90 or E45:135
            try:
                parts = cmd[1:].split(':')
                left_angle  = int(parts[0])
                right_angle = int(parts[1])
                self._set_ears(left_angle, right_angle)
            except (ValueError, IndexError):
                self.get_logger().warn(f'Invalid ear command: {cmd}')

        elif cmd == 'NEUTRAL':
            self._set_ears(90, 90)

    def _set_ears(self, left_angle: int, right_angle: int):
        """Send servo commands for both ears."""
        left_angle  = max(0, min(180, left_angle))
        right_angle = max(0, min(180, right_angle))
        self._send_raw(f's {self.LEFT_EAR_PIN} {left_angle}\r')
        time.sleep(0.02)  # Small delay between commands
        self._send_raw(f's {self.RIGHT_EAR_PIN} {right_angle}\r')

    def _wiggle_ears(self):
        """Wiggle ears: alternate between up (45°) and down (135°) 4 times."""
        import time as _time
        for _ in range(4):
            self._set_ears(45, 135)    # Ears up/perked
            _time.sleep(0.25)
            self._set_ears(135, 45)    # Ears down/drooped
            _time.sleep(0.25)
        self._set_ears(90, 90)         # Back to neutral


    # ------------------------------------------------------------------
    # Serial Write Helper
    # ------------------------------------------------------------------
    def _send_raw(self, cmd: str):
        try:
            self.ser.write(cmd.encode())
        except Exception as e:
            self.get_logger().warn(f'Serial write error: {e}')

    def _publish_obstacle(self, direction: str):
        """Publish obstacle alert only when direction changes (avoid spam)."""
        if self._last_obstacle_dir != direction:
            self._last_obstacle_dir = direction
            self.get_logger().warn(f'IR Obstacle detected at: {direction}!')
            msg = String()
            msg.data = direction
            self.obstacle_pub.publish(msg)

    # ------------------------------------------------------------------
    # Background Read Loop (Pico → Pi)
    # ------------------------------------------------------------------
    def _read_loop(self):
        while rclpy.ok():
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
                if not line:
                    continue

                if line.startswith('IR:'):
                    # IR:FL:FR:BL
                    parts = line[3:].split(':')
                    if len(parts) == 3:
                        self.ir['FL'] = int(parts[0])
                        self.ir['FR'] = int(parts[1])
                        self.ir['BL'] = int(parts[2])

                elif line.startswith('ENC:'):
                    # ENC:left:right
                    parts = line[4:].split(':')
                    if len(parts) == 2:
                        odom_msg = String()
                        odom_msg.data = f'{parts[0]}:{parts[1]}'
                        self.odom_pub.publish(odom_msg)

                elif line.startswith('TOUCH:'):
                    val = line[6:]
                    is_touched = (val == '1')
                    touch_msg = Bool()
                    touch_msg.data = is_touched
                    self.touch_pub.publish(touch_msg)
                    self.get_logger().info(f'Touch sensor state changed to: {is_touched}')

                elif line.startswith('DEBUG:'):
                    self.get_logger().info(f'PICO_DEBUG: {line}')

            except Exception as e:
                self.get_logger().warn(f'Serial read error: {e}')

    def destroy_node(self):
        if self.ser and self.ser.is_open:
            self._send_motors(0, 0)   # Safety stop on shutdown
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
