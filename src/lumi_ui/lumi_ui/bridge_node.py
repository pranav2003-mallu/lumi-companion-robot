import asyncio
import json
import threading
import queue
import websockets
import urllib.request
import re
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Point

msg_queue = queue.Queue()
clients = set()

async def ws_handler(websocket):
    clients.add(websocket)
    try:
        async for msg in websocket:
            try:
                data = json.loads(msg)
                if data.get('type') == 'youtube_search':
                    query = data.get('query', '').replace(' ', '+')
                    url = f"https://www.youtube.com/results?search_query={query}"
                    html = urllib.request.urlopen(url).read().decode('utf-8')
                    video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", html)
                    if video_ids:
                        response = {'type': 'play_youtube', 'videoId': video_ids[0]}
                        await websocket.send(json.dumps(response))
            except Exception as e:
                print(f"Failed to process websocket message: {e}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)

async def broadcast_loop():
    while True:
        try:
            # Check the thread-safe queue for new messages from ROS
            while not msg_queue.empty():
                msg = msg_queue.get_nowait()
                if clients:
                    websockets.broadcast(clients, json.dumps(msg))
        except Exception as e:
            print(f"Broadcast error: {e}")
        await asyncio.sleep(0.01)

async def start_ws_server():
    server = await websockets.serve(ws_handler, "0.0.0.0", 8765)
    await broadcast_loop()

def ws_thread():
    asyncio.run(start_ws_server())

class BridgeNode(Node):
    def __init__(self):
        super().__init__('bridge_node')
        self.emotion_sub = self.create_subscription(String, '/lumi/emotion', self.emotion_callback, 10)
        self.speak_sub = self.create_subscription(Bool, '/lumi/speak', self.speak_callback, 10)
        self.look_sub = self.create_subscription(Point, '/lumi/look', self.look_callback, 10)
        self.touch_sub = self.create_subscription(Bool, '/lumi/touch', self.touch_callback, 10)
        
        self.get_logger().info('Lumi UI Bridge Node Started. WebSocket server on ws://0.0.0.0:8765')
        
    def emotion_callback(self, msg):
        msg_queue.put({'type': 'emotion', 'value': msg.data})
        
    def speak_callback(self, msg):
        msg_queue.put({'type': 'speak', 'value': msg.data})
        
    def look_callback(self, msg):
        msg_queue.put({'type': 'look', 'x': msg.x, 'y': msg.y})

    def touch_callback(self, msg):
        if msg.data:
            msg_queue.put({'type': 'touch'})

def main(args=None):
    rclpy.init(args=args)
    
    # Start WebSocket Server in background
    t = threading.Thread(target=ws_thread, daemon=True)
    t.start()
    
    node = BridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
