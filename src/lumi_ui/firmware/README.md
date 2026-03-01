# Lumi Firmware — Flash Instructions

## Location
The Pico firmware file is at:
```
lumi_ws/src/lumi_ui/firmware/lumi_pico_firmware.ino
```

## Step 1 — Install Arduino IDE Board Core
1. Open Arduino IDE
2. Go to **File → Preferences → Additional Board URLs** and add:
   ```
   https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
   ```
3. Go to **Tools → Board Manager**, search for `rp2040`, install **"Raspberry Pi Pico/RP2040 by Earle F. Philhower"**

## Step 2 — Open Firmware
1. In Arduino IDE: **File → Open** → navigate to `lumi_pico_firmware.ino`
2. Select Board: **Tools → Board → Raspberry Pi Pico**
3. Select Port: the `/dev/ttyACM0` or `/dev/ttyUSB0` port for your Pico

## Step 3 — Flash
Click **Upload** (→ button). Done!

## Pin Reference
| Pin | Function |
|-----|----------|
| GP2-7  | Left motor (L298N) |
| GP8-13 | Right motor (L298N) |
| GP14,15 | Left encoder A/B |
| GP16,17 | Right encoder A/B |
| GP22 | Left ear servo |
| GP26 | Right ear servo |
| GP27 | Touch sensor (HIGH = touched) |

## Serial Test (without ROS2)
Open Arduino Serial Monitor at **115200 baud** and type:
- `F` → Forward
- `S` → Stop
- `WIGGLE_EARS` → Ears wiggle
- `E60:120` → Move ears to custom angles
