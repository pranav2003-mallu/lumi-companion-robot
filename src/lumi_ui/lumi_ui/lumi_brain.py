import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist
import speech_recognition as sr
from gtts import gTTS
import os
import pygame
import google.generativeai as genai
import threading
import time
from datetime import datetime

# --- CONFIGURE GEMINI API KEY HERE ---
# 1. Get a free API key from https://aistudio.google.com/
# 2. Paste it here:
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "<PLACE_YOUR_API_KEY_HERE>")

class LumiBrainNode(Node):
    def __init__(self):
        super().__init__('lumi_brain')
        
        # Publishers to control the Face UI
        self.emotion_pub = self.create_publisher(String, '/lumi/emotion', 10)
        self.speak_pub = self.create_publisher(Bool, '/lumi/speak', 10)
        
        # Publishers to control the body/ears
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.ear_pub = self.create_publisher(String, '/lumi/ear_cmd', 10)
        self.is_dancing = False
        
        # Setup Pygame for Audio playback
        pygame.mixer.init()
        self.is_listening = False
        
        self.person_sub = self.create_subscription(String, '/lumi/person_seen', self.person_callback, 10)
        self.last_person_greeted = None
        
        # Setup Gemini if Key is valid (will fail gracefully if not)
        try:
           genai.configure(api_key=GEMINI_API_KEY)
           
           # Get current date/time to inject into the system prompt
           current_time = datetime.now().strftime("%I:%M %p on %A, %B %d, %Y")
           
           # A system prompt gives Lumi its personality and awareness
           system_instruction = f"You are Lumi, a friendly, smart, cheerful companion robot with a face. Your creator is Mallu. You are currently running on a robot built for a presentation. Mallu's favorite game is Tic-Tac-Toe. You play, help, and talk. Keep responses short (1-3 sentences). IMPORTANT: You MUST change your facial expression based on your emotion by starting EVERY message with ONE of these tags: [happy], [sad], [angry], [surprised], [confused], [sleepy], [laughing], [love], [star], [dead], [dizzy], [wink], [battery]. Example: '[love] I love you too!'. The current date/time is: {current_time}."
           
           self.model = genai.GenerativeModel(
               'gemini-2.5-flash',
               system_instruction=system_instruction
           )
           
           # Start a chat session so it remembers history
           self.chat = self.model.start_chat(history=[])
           self.get_logger().info('Gemini AI Initialized Successfully.')
        except Exception as e:
           self.get_logger().error(f"Failed to intialize Gemini: {e}")
           self.model = None

        self.get_logger().info('Lumi Brain Node Started. Running voice loop...')
        
        # Start looking for voice in a background thread so ROS doesn't freeze
        self.voice_thread = threading.Thread(target=self.run_voice_loop, daemon=True)
        self.voice_thread.start()

    def person_callback(self, msg):
        person = msg.data
        if person == "Mallu" and self.last_person_greeted != "Mallu":
            self.get_logger().info('Saw Mallu! Initiating automatic greeting.')
            self.last_person_greeted = "Mallu"
            self.set_emotion('surprised')
            self.speak("Oh, hi Mallu! It is so great to see you today.", emotion="love")
            self.set_emotion('happy')

    def set_emotion(self, emotion):
        msg = String()
        msg.data = emotion
        self.emotion_pub.publish(msg)

    def dance_routine(self):
        self.is_dancing = True
        self.set_emotion('laughing')
        
        track_path = "/home/mallu/app_ui/lumi_ws/src/lumi_ui/media/dance_track.wav"
        if os.path.exists(track_path):
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.play()
        else:
            self.get_logger().error(f"Could not find dance track at {track_path}")
            
        step_duration = 0.5
        ear_state = ["WIGGLE", "E90:90"]
        spin_dirs = [1.5, -1.5]
        tick = 0
        
        while self.is_dancing and pygame.mixer.music.get_busy():
            # Wiggle ears
            ear_msg = String()
            ear_msg.data = ear_state[tick % 2]
            self.ear_pub.publish(ear_msg)
            
            # Spin wheels
            twist = Twist()
            twist.angular.z = spin_dirs[tick % 2]
            self.cmd_vel_pub.publish(twist)
            
            # small polling sleep to catch stop events quickly
            slept = 0.0
            while slept < step_duration and self.is_dancing:
                time.sleep(0.1)
                slept += 0.1
                
            tick += 1
            
        # Clean up dance moves
        self.is_dancing = False
        self.cmd_vel_pub.publish(Twist()) # Stop wheels from spinning
        
        ear_msg = String()
        ear_msg.data = "E90:90"
        self.ear_pub.publish(ear_msg) # Reset ears to neutral
        self.set_emotion('happy')

    def set_talking(self, is_talking):
        msg = Bool()
        msg.data = is_talking
        self.speak_pub.publish(msg)

    def speak(self, text, emotion='happy'):
        """Talks out loud with an incredibly realistic, sweet neural voice and lip syncs the face"""
        self.get_logger().info(f"Lumi talking: {text}")
        
        try:
            # 1. Create a fluent voice audio file
            # edge-tts connects to Microsoft Azure Neural voices for extremely realistic speech
            filename = "/tmp/lumi_voice.mp3"
            safe_text = text.replace('"', '').replace("'", "")
            # Aria is a very sweet and natural sounding female voice
            # we also speed it up slightly (+5%) to sound more energetic
            os.system(f'edge-tts --rate=+5% --voice "en-US-AriaNeural" --text "{safe_text}" --write-media {filename}')
            
            # 2. Play the Audio using pygame
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            # 3. Animate the Face while audio plays
            self.set_talking(True)
            self.set_emotion(emotion)
            
            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            # 4. Stop Face Lips
            self.set_talking(False)
            self.set_emotion('neutral')
            
            # Cleanup
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            self.get_logger().error(f"Error speaking: {e}")
            self.set_talking(False)
            self.set_emotion('neutral')

    def ask_gemini(self, query):
        if not self.model or GEMINI_API_KEY == "YOUR_API_KEY_HERE":
            return "I am not connected to my brain yet! Please add a Gemini API Key to my code.", "sad"
        
        try:
            self.set_emotion('thinking') # Or surprised/confused while thinking
            response = self.chat.send_message(query)
            reply = response.text.replace("*", "") # Remove markdown stars
            
            import re
            emotion = 'happy'
            # Look for emotion tags like [love], [star], [dead]
            match = re.search(r'\[(.*?)\]', reply)
            if match:
                extracted = match.group(1).lower()
                valid_emotions = ['happy', 'sad', 'angry', 'surprised', 'confused', 'sleepy', 'laughing', 'love', 'star', 'dead', 'dizzy', 'wink', 'battery']
                if extracted in valid_emotions:
                    emotion = extracted
                # Clean tag from text so TTS doesn't say "bracket love bracket"
                reply = reply.replace(f"[{match.group(1)}]", "").strip()
                
            return reply, emotion
        except Exception as e:
            self.get_logger().error(f"Gemini Error: {e}")
            return "Sorry, I had a little trouble thinking just now.", "sad"

    def run_voice_loop(self):
        recognizer = sr.Recognizer()
        # Set explicitly to avoid missing lower volumes
        recognizer.energy_threshold = 300  
        recognizer.dynamic_energy_threshold = True 
        # Shorter pause before assuming the user is done talking (0.8s)
        recognizer.pause_threshold = 0.8   
        
        # Start in Happy mode
        self.set_emotion('happy')
        self.get_logger().info("Lumi is awake and happy!")
        
        # State tracking
        self.is_sleeping = False
        
        # This will constantly loop and listen
        while rclpy.ok():
            try:
                # Time-based automatic sleep check
                current_hour = datetime.now().hour
                is_night = current_hour >= 22 or current_hour <= 6
                
                if is_night and not self.is_sleeping:
                    self.is_sleeping = True
                    self.set_emotion('sleepy')
                    pygame.mixer.music.set_volume(0.3)
                    self.get_logger().info("Nighttime detected. Going to sleep automatically.")
                elif not is_night and self.is_sleeping:
                    self.is_sleeping = False
                    self.set_emotion('happy')
                    pygame.mixer.music.set_volume(1.0)
                    self.get_logger().info("Good morning! Waking up automatically.")
                    self.speak("Good morning! I am awake.")

                with sr.Microphone() as source:
                    # Only do ambient noise adjustment briefly 
                    recognizer.adjust_for_ambient_noise(source, duration=0.2)

                    self.get_logger().info("Listening...")
                    
                    # 'timeout=5' allows loop to hit the time check periodically 
                    # 'phrase_time_limit' stops it from accidentally recording minutes of static
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    
                    self.get_logger().info("Processing speech...")
                    text = recognizer.recognize_google(audio).lower()
                    self.get_logger().info(f"Heard something: {text}")

                    # 1. Custom Command: WAKE UP
                    if "wake up" in text:
                        pygame.mixer.music.set_volume(1.0) # Reset volume
                        self.set_emotion('happy')
                        self.speak("I'm awake and ready!")
                        continue
                        
                    # 2. Custom Command: SLEEP
                    if "go to sleep" in text or "sleep" in text and "lumi" in text:
                        self.set_emotion('sleepy')
                        self.speak("Okay, I'm going to sleep now. Call me if you need me.")
                        continue
                        
                    # 3. Custom Command: DANCE
                    if "dance" in text and ("lumi" in text or "let's" in text):
                        if not self.is_dancing:
                            self.set_emotion('laughing')
                            self.speak("I love dancing! Initiating dance mode.")
                            # Start dance in background thread so the voice loop continues listening
                            threading.Thread(target=self.dance_routine, daemon=True).start()
                        continue

                    # 4. Custom Command: PRESENTATION MODE
                    if "execute presentation mode" in text or "start presentation" in text:
                        self.set_emotion('star')
                        self.speak("Hello everyone! I am Lumi, an offline-capable Smart Robot Companion. Mallu built me using a custom WebSocket bridge, native JavaScript games, and the Gemini 2.5 Flash AI model. I am thrilled to be here today!", emotion="star")
                        time.sleep(1)
                        self.set_emotion('happy')
                        continue

                    # 5. Custom Command: STOP / RESET
                    if "stop" in text and len(text.split()) <= 3:
                        self.is_dancing = False
                        
                        pygame.mixer.music.stop()
                        self.set_talking(False)
                        self.set_emotion('neutral')
                        
                        # Stop hardware
                        self.cmd_vel_pub.publish(Twist()) 
                        ear_msg = String()
                        ear_msg.data = "E90:90"
                        self.ear_pub.publish(ear_msg)
                        
                        self.speak("Okay, stopping.")
                        time.sleep(0.5)
                        self.set_emotion('happy')
                        continue

                    # 6. WAKE WORD CHECK (Only talk to AI if name is called)
                    if "lumi" in text:
                        self.set_emotion('surprised')
                        query = text.replace("hey lumi", "").replace("lumi", "").strip()
                        
                        if len(query) > 2:
                            reply, emotion = self.ask_gemini(query)
                            self.speak(reply, emotion=emotion)
                        else:
                            self.speak("Yes? I am listening.", emotion="surprised")
                            
                        self.set_emotion('happy')

            except sr.WaitTimeoutError:
                pass 
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                self.get_logger().error(f"Google Speech Error: {e}")
            except Exception as e:
                self.get_logger().error(f"Loop Error: {e}")

def main(args=None):
    rclpy.init(args=args)
    
    node = LumiBrainNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
