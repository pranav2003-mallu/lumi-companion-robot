#!/bin/bash
# install_pi.sh

echo "====================================="
echo " Installing Lumi Pi 4 Prerequisites"
echo "====================================="

# Use apt where possible to avoid long compilation times on Pi
sudo apt-get update
sudo apt-get install -y \
  python3-dev \
  python3-pip \
  python3-opencv \
  python3-pyaudio \
  portaudio19-dev \
  libasound-dev \
  flac

# Install python-specific packages using pip
# 'edge-tts' provides the Azure voices
# 'google-generativeai' is for the brain
# 'SpeechRecognition' is for parsing the mic
pip3 install --user SpeechRecognition pygame google-generativeai edge-tts websockets pyserial

echo "====================================="
echo "        Installation Complete         "
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Source your ROS2 environment:  source /opt/ros/humble/setup.bash"
echo "2. Build the workspace:           colcon build"
echo "3. Run the complete launch script: source install/setup.bash && ros2 launch lumi_ui all.launch.py"
