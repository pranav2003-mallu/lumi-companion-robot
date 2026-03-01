import cv2
import rclpy
import os
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import String
import threading

class FaceTrackerNode(Node):
    def __init__(self):
        super().__init__('face_tracker_node')
        self.look_pub = self.create_publisher(Point, '/lumi/look', 10)
        self.person_pub = self.create_publisher(String, '/lumi/person_seen', 10)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.active = True
        
        # Load Trained Face Recognizer if it exists
        self.has_model = False
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            model_path = '/home/mallu/app_ui/lumi_ws/src/lumi_ui/lumi_ui/lumi_face_model.yml'
            if os.path.exists(model_path):
                self.recognizer.read(model_path)
                self.has_model = True
                self.get_logger().info('Loaded Face Recognizer Model for Mallu successfully.')
        except Exception as e:
            self.get_logger().warning(f"Could not load face recognizer: {e}")
        
        self.get_logger().info('Lumi Face Tracker Node Started.')
        
        # Start the video loop in a thread so ROS can spin normally
        self.video_thread = threading.Thread(target=self.track_face_loop, daemon=True)
        self.video_thread.start()

    def track_face_loop(self):
        self.get_logger().info('Starting Laptop Camera...')
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.get_logger().error('Could not open camera 0. Trying camera 1...')
            cap = cv2.VideoCapture(1)
            if not cap.isOpened():
                self.get_logger().error('Could not open any camera. Shutting down tracking.')
                self.active = False
                return
                
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        cam_center_x = 320
        cam_center_y = 240
        self.get_logger().info('Camera running. Press \'q\' in the window to stop.')
        
        while self.active and rclpy.ok():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                (fx, fy, fw, fh) = faces[0]
                fx_center = fx + (fw // 2)
                fy_center = fy + (fh // 2)
                
                # mapping max x to roughly +/- 30px
                mapped_x = float(((fx_center - cam_center_x) / cam_center_x) * 30)
                mapped_y = float(((fy_center - cam_center_y) / cam_center_y) * 30)
                
                msg = Point()
                msg.x = mapped_x
                msg.y = mapped_y
                msg.z = 0.0
                self.look_pub.publish(msg)
                
                # Face Recognition Logic
                name_detected = "Unknown"
                if self.has_model:
                    try:
                        id_, confidence = self.recognizer.predict(gray[fy:fy+fh, fx:fx+fw])
                        # LBPH Confidence (Distance): Lower is a better match. Usually < 85 is strictly accurate
                        if confidence < 85:
                            if id_ == 1:
                                name_detected = "Mallu"
                                msg_str = String()
                                msg_str.data = "Mallu"
                                self.person_pub.publish(msg_str)
                    except Exception as e:
                        pass
                
                cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), (255, 0, 0), 2)
                cv2.putText(frame, f"Lumi Tracking: {name_detected}", (fx, fy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
            # Only show window if display is available (prevents crash on headless Pi)
            try:
                cv2.imshow('Lumi AI Vision', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.active = False
                    break
            except cv2.error:
                pass # Running headless, ignore UI rendering
                
        cap.release()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = FaceTrackerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.active = False
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
