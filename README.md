# 🤖 Lumi Companion Robot

Lumi is an interactive, offline-capable, AI-powered Smart Robot Companion built with ROS2 (Humble), WebSockets, and a robust HTML/JS/CSS frontend. It is designed to run on compute-constrained devices like a Raspberry Pi attached to a 7-inch touch display, while coordinating hardware motors and sensors via a Raspberry Pi Pico.

## ✨ Features
- **Expressive Animated UI:** A fully dynamic face with multiple emotional states (Happy, Sad, Angry, Sleepy, Laughing, Star, Love, etc.).
- **Hardware Integration:** Connects gracefully to a Raspberry Pi Pico to control wheel motors (`cmd_vel`) and physical ear servos based on real-time emotional state.
- **AI Brain & Voice:** Integrates with the **Gemini 2.5 Flash** model to hold real-time, context-aware conversations. Includes natural text-to-speech with synced lip animations.
- **Local Face Recognition:** Built-in OpenCV LBPH face recognizer detects predefined faces offline and triggers custom greetings.
- **Game Hub (Lumi Originals):** Features 6 fully offline, touch-friendly minigames embedded right into her UI:
  - Tic-Tac-Toe
  - Math Challenge
  - Word Guesser
  - Memory Match
  - Simon Says
  - Animal Quiz
- **YouTube Browser:** An embedded mode to search and play YouTube videos dynamically.

---

## 🛠️ Folder Structure
- `src/lumi_ui/` - The core ROS2 package containing the Python backend and web frontend.
  - `lumi_ui/` - Python ROS2 Nodes (`lumi_brain.py`, `face_tracker_node.py`, `bridge_node.py`, etc.).
  - `web/` - The frontend application (`index.html`, `style.css`, `script.js`).
  - `launch/` - ROS2 launch files to start the entire system with one command.
  - `firmware/` - MicroPython/Arduino `.ino` code for the Pico motor controller.

---

## 🚀 Installation & Setup

These instructions are specifically designed for deploying Lumi natively onto a Raspberry Pi (or Linux PC) running Ubuntu 22.04 with ROS2 Humble.

### 1. Prerequisites
Ensure you have ROS2 Humble Desktop installed. You will also need `pip3` and OpenCV.
```bash
sudo apt update
sudo apt install python3-pip python3-colcon-common-extensions ffmpeg
pip3 install websockets SpeechRecognition gTTS pygame google-generativeai opencv-python opencv-contrib-python edge-tts
```

### 2. Clone the Repository
Clone this repository directly into your home folder to create your workspace:
```bash
git clone https://github.com/pranav2003-mallu/lumi-companion-robot.git ~/lumi_ws
cd ~/lumi_ws
```

### 3. Build the ROS2 Package
Compile the codebase into executable ROS2 nodes:
```bash
source /opt/ros/humble/setup.bash
colcon build
```

---

## 🎮 How to Run Lumi

To start all of Lumi's brain nodes, hardware bridges, and camera sensors at once, follow these steps:

**1. Source your new build:**
```bash
cd ~/lumi_ws
source install/setup.bash
```

**2. Launch the master file:**
```bash
ros2 launch lumi_ui all.launch.py
```

**3. Set up your API Keys (Optional but recommended):**
If you want Lumi to have deep conversational AI, she expects a Gemini API key. If not provided, she will fall back to simple command parsing.
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**4. Open the Face UI:**
Open Chromium or any modern web browser on your 7-inch display and navigate to:
```url
http://localhost:8001
```

---

## 🧠 Training Lumi to Recognize You
You can map a custom offline ML model to your own face without using the cloud! 

1. Sit in front of the robot's camera.
2. Run the included training script:
   ```bash
   cd ~/lumi_ws
   python3 train_lumi_vision.py
   ```
3. Follow the CLI wizard. It will take ~30 snapshots of your face, generate a `lumi_face_model.yml` file, and inject it directly into the `face_tracker_node.py`. The next time Lumi sees you, she will say hello specifically to you!

---

## ✋ Custom Voice Commands

While Lumi is running, she actively listens to her ambient microphone in an offline loop.

*   `"Lumi, start presentation"` -> Enters "Star" mode, triggers a preset speech introduction for your presentation.
*   `"Lumi, let's dance"` -> Plays a local techno track, wiggles her servo ears, spins her wheels, and bounces happily on screen.
*   `"Lumi, go to sleep"` -> Shows a dreaming sleep animation and closes her eyes.
*   `"Stop."` -> Masters emergency stop for motors, music, text generation, and resets ears to 90 degrees.
*   `"Hey Lumi, [any detailed question]"` -> Connects to Gemini 2.5 and natively speaks the response aloud while lip syncing.

---
*Created by Mallu. Feel free to fork and add more games!*
