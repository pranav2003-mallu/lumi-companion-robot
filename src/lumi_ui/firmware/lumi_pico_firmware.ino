/* =========================================================
   LUMI COMPANION ROBOT — COMPLETE PICO FIRMWARE
   ---------------------------------------------------------
   Flash this with Arduino IDE onto your Raspberry Pi Pico
   ---------------------------------------------------------
   HARDWARE:
     - 4x DC Motors (2 per side) controlled through 2x L298N
     - 2x Encoders (one LEFT side, one RIGHT side)
     - 2x Servo Motors  (Left Ear: GP22, Right Ear: GP26)
     - 1x Capacitive Touch Sensor (GP27)  — OUTPUT HIGH on touch
     - LED_BUILTIN for status

   ARDUINO IDE BOARD: "Raspberry Pi Pico" (from Earle Philhower core)
     https://github.com/earlephilhower/arduino-pico

   DEPENDENCIES:
     - Built-in Servo.h (included in Pico core above)

   =========================================================
   SERIAL PROTOCOL (Pi -> Pico, newline terminated):
   -------------------------------------------------------
     F          Forward  (all 4 wheels)
     B          Backward
     L          Turn Left  (right wheels forward, left backward)
     R          Turn Right
     S          Stop
     Z          Reset encoder counts to zero
     Wnnn       Set speed 0-255  (e.g. W150)
     WIGGLE_EARS  Wiggle both ears 3 times
     Exx:yy     Move ears to angles (e.g. E120:60)

   SERIAL PROTOCOL (Pico -> Pi, newline terminated):
   -------------------------------------------------------
     LUMI:READY         Pico booted OK
     ENC:left:right     Encoder tick counts every 50 ms
     TOUCH:1            Rising-edge touch event detected

   PIN MAP:
   -------------------------------------------------------
   Motor L (Front + Rear):
     PWM_L1=2  IN1_L1=3  IN2_L1=4
     PWM_L2=5  IN1_L2=6  IN2_L2=7
   Motor R (Front + Rear):
     PWM_R1=8  IN1_R1=9  IN2_R1=10
     PWM_R2=11 IN1_R2=12 IN2_R2=13
   Encoders:
     ENC_L_A=14  ENC_L_B=15
     ENC_R_A=16  ENC_R_B=17
   Ear Servos:
     EAR_L = GP22
     EAR_R = GP26
   Touch Sensor:
     TOUCH = GP27  (HIGH when touched)
   ========================================================= */

#include <Servo.h>

// ============================================================
//  MOTOR PINS
// ============================================================
#define PWM_L1  2
#define IN1_L1  3
#define IN2_L1  4

#define PWM_L2  5
#define IN1_L2  6
#define IN2_L2  7

#define PWM_R1  8
#define IN1_R1  9
#define IN2_R1  10

#define PWM_R2  11
#define IN1_R2  12
#define IN2_R2  13

// ============================================================
//  ENCODER PINS  (2 encoders only: 1 per side)
// ============================================================
#define ENC_L_A  14
#define ENC_L_B  15
#define ENC_R_A  16
#define ENC_R_B  17

// ============================================================
//  EAR SERVO PINS
// ============================================================
#define EAR_L_PIN  22
#define EAR_R_PIN  26

// ============================================================
//  TOUCH SENSOR PIN
// ============================================================
#define TOUCH_PIN  27

// ============================================================
//  GLOBALS
// ============================================================
volatile long enc_l = 0;
volatile long enc_r = 0;

int  speedVal       = 180;        // Default motor speed (0-255)
unsigned long last_cmd_time     = 0;
unsigned long last_enc_pub      = 0;
unsigned long last_touch_check  = 0;
bool last_touch_state = false;

#define CMD_TIMEOUT_MS   500      // Stop motors if no cmd for 500 ms
#define ENC_PUB_PERIOD   50       // Publish encoders every 50 ms
#define TOUCH_POLL_MS    80       // Poll touch every 80 ms

Servo earLeft;
Servo earRight;

// ============================================================
//  ENCODER ISRs
// ============================================================
void isr_enc_l() { digitalRead(ENC_L_B) ? enc_l++ : enc_l--; }
void isr_enc_r() { digitalRead(ENC_R_B) ? enc_r++ : enc_r--; }

// ============================================================
//  MOTOR HELPER
// ============================================================
void drive_side(int pwm1, int a1, int b1,
                int pwm2, int a2, int b2,
                int speed) {
  speed = constrain(speed, -255, 255);
  bool fwd = (speed > 0);
  bool rev = (speed < 0);
  digitalWrite(a1, fwd); digitalWrite(b1, rev); analogWrite(pwm1, abs(speed));
  digitalWrite(a2, fwd); digitalWrite(b2, rev); analogWrite(pwm2, abs(speed));
}

void stop_all() {
  drive_side(PWM_L1, IN1_L1, IN2_L1, PWM_L2, IN1_L2, IN2_L2, 0);
  drive_side(PWM_R1, IN1_R1, IN2_R1, PWM_R2, IN1_R2, IN2_R2, 0);
}

// Convenience wrappers
void go_forward()  {
  drive_side(PWM_L1, IN1_L1, IN2_L1, PWM_L2, IN1_L2, IN2_L2,  speedVal);
  drive_side(PWM_R1, IN1_R1, IN2_R1, PWM_R2, IN1_R2, IN2_R2,  speedVal);
}
void go_backward() {
  drive_side(PWM_L1, IN1_L1, IN2_L1, PWM_L2, IN1_L2, IN2_L2, -speedVal);
  drive_side(PWM_R1, IN1_R1, IN2_R1, PWM_R2, IN1_R2, IN2_R2, -speedVal);
}
void turn_left()  {
  drive_side(PWM_L1, IN1_L1, IN2_L1, PWM_L2, IN1_L2, IN2_L2, -speedVal);
  drive_side(PWM_R1, IN1_R1, IN2_R1, PWM_R2, IN1_R2, IN2_R2,  speedVal);
}
void turn_right() {
  drive_side(PWM_L1, IN1_L1, IN2_L1, PWM_L2, IN1_L2, IN2_L2,  speedVal);
  drive_side(PWM_R1, IN1_R1, IN2_R1, PWM_R2, IN1_R2, IN2_R2, -speedVal);
}

// ============================================================
//  EAR ANIMATIONS
// ============================================================
void wiggle_ears(int times = 3) {
  for (int i = 0; i < times; i++) {
    earLeft.write(50);   earRight.write(130);  delay(150);
    earLeft.write(130);  earRight.write(50);   delay(150);
  }
  earLeft.write(90);
  earRight.write(90);
}

void set_ears(int left_deg, int right_deg) {
  earLeft.write(constrain(left_deg,  0, 180));
  earRight.write(constrain(right_deg, 0, 180));
}

// ============================================================
//  SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);   // LED on = powered

  // Motor pins
  int motorPins[] = {
    PWM_L1, IN1_L1, IN2_L1,
    PWM_L2, IN1_L2, IN2_L2,
    PWM_R1, IN1_R1, IN2_R1,
    PWM_R2, IN1_R2, IN2_R2
  };
  for (int i = 0; i < 12; i++) pinMode(motorPins[i], OUTPUT);

  // Encoder pins
  pinMode(ENC_L_A, INPUT_PULLUP); pinMode(ENC_L_B, INPUT_PULLUP);
  pinMode(ENC_R_A, INPUT_PULLUP); pinMode(ENC_R_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_L_A), isr_enc_l, RISING);
  attachInterrupt(digitalPinToInterrupt(ENC_R_A), isr_enc_r, RISING);

  // Touch sensor
  pinMode(TOUCH_PIN, INPUT);

  // Servos — attach and center
  earLeft.attach(EAR_L_PIN);
  earRight.attach(EAR_R_PIN);
  set_ears(90, 90);

  // Startup wiggle so you know servos are working
  delay(500);
  wiggle_ears(1);

  stop_all();

  Serial.println("LUMI:READY");
}

// ============================================================
//  LOOP
// ============================================================
void loop() {
  unsigned long now = millis();

  // ---- 1. Read & process incoming commands ----
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    last_cmd_time = now;

    // Motor commands
    if      (cmd == "F")  go_forward();
    else if (cmd == "B")  go_backward();
    else if (cmd == "L")  turn_left();
    else if (cmd == "R")  turn_right();
    else if (cmd == "S")  stop_all();

    // Reset encoders
    else if (cmd == "Z") {
      noInterrupts(); enc_l = 0; enc_r = 0; interrupts();
    }

    // Set speed: Wnnn
    else if (cmd.startsWith("W")) {
      speedVal = constrain(cmd.substring(1).toInt(), 0, 255);
    }

    // Ear wiggle
    else if (cmd == "WIGGLE_EARS") {
      wiggle_ears(3);
    }

    // Ear position: Eleft:right  e.g. E120:60
    else if (cmd.startsWith("E")) {
      int colon = cmd.indexOf(':');
      if (colon > 1) {
        int la = cmd.substring(1, colon).toInt();
        int ra = cmd.substring(colon + 1).toInt();
        set_ears(la, ra);
      }
    }
  }

  // ---- 2. Safety timeout: stop motors if no command ----
  if (now - last_cmd_time > CMD_TIMEOUT_MS) {
    stop_all();
  }

  // ---- 3. Publish encoder ticks ----
  if (now - last_enc_pub >= ENC_PUB_PERIOD) {
    noInterrupts();
    long l = enc_l;
    long r = enc_r;
    interrupts();

    Serial.print("ENC:"); Serial.print(l);
    Serial.print(":"); Serial.println(r);

    last_enc_pub = now;
  }

  // ---- 4. Poll touch sensor (edge detect) ----
  if (now - last_touch_check >= TOUCH_POLL_MS) {
    bool touched = (digitalRead(TOUCH_PIN) == HIGH);
    if (touched && !last_touch_state) {
      // Rising edge — new touch!
      Serial.println("TOUCH:1");
      digitalWrite(LED_BUILTIN, LOW);    // brief LED blink
      delay(50);
      digitalWrite(LED_BUILTIN, HIGH);
    }
    last_touch_state = touched;
    last_touch_check = now;
  }
}
