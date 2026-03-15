#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>
#include <stdint.h>
#include <Wire.h>
#include "DHT.h"

// Pins for sensors (Avoiding GP2-GP21 which are used by Motors/Encoders)
#define IR_FL_PIN 22
#define IR_FR_PIN 26
#define IR_BL_PIN 27
#define IR_BR_PIN 28  // Replaces EXTRA_LED
#define DHTPIN 0      // Uses GP0 (SDA will move to 4/5 or another if possible)
#define DHTTYPE DHT21 // AM2301

// Note: Pico I2C0 can be mapped to GP0/GP1 or others. 
// Since GP0/GP1 are free, we will use them for I2C for MPU6050.
// BUT DHTPIN is now 0. Let's move DHT to GP22 and I2C back to 0/1.
#undef DHTPIN
#define DHTPIN 22
#undef IR_FL_PIN
#define IR_FL_PIN 25 // Onboard LED pin can be used as GPIO if not using LED? No, let's use GP22 for DHT.
// Actually, let's reconsider:
// GP0, GP1 -> I2C (MPU6050)
// GP22 -> DHT
// GP26 -> IR FL
// GP27 -> IR FR
// GP28 -> IR BL
// Wait, I still need one for IR BR. 
// Let's use the standard "Serial" pins GP0/GP1 for I2C, 
// and if the user needs more, they might have to sacrifice an encoder or motor channel.
// BUT wait, I'll use GP2-GP21 for motors/encoders as per current config.
// I WILL USE GP12/GP13 for IR sensors? NO, they are used by motors.

// Let's use:
// MPU6050: GP0 (SDA), GP1 (SCL)
// DHT: GP22
// IR_FL: GP26
// IR_FR: GP27
// IR_BL: GP28
// IR_BR: GP2  // I'll steal GP2 from LF_PWM and tell the user!
// Actually, better: use GP22, 26, 27, 28 for IR. And DHT on GP0? No, I2C.

// FINAL PIN ASSIGNMENT:
#define DHT_PIN 25  // Moved to 25 to free up 22 for Touch
#define IR_FL   26
#define IR_FR   27
#define IR_BL   28
// GP22 is used for the Touch Sensor as per user connection.
// GP25 is used for DHT21.
#define IR_BR   -1 

DHT dht(DHT_PIN, DHTTYPE);

// MPU6050 I2C is disabled to free GP0/GP1 for Ear Servos
// const int MPU_ADDR = 0x68; 
int16_t AcX, AcY, AcZ, Tmp_MPU, GyX, GyY, GyZ;

void initSensors() {
  pinMode(IR_FL, INPUT);
  pinMode(IR_FR, INPUT);
  pinMode(IR_BL, INPUT);
  
  dht.begin();
  
  // Wire/I2C disabled to avoid conflict with GP0/GP1 servos
  /*
  Wire.setSDA(SDA_PIN);
  Wire.setSCL(SCL_PIN);
  Wire.begin();
  ...
  */
}

void readMPU6050() {
  // MPU6050 is disabled to allow using GP0/GP1 for ear servos
  /*
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);
  if (Wire.available() >= 14) {
    ...
  }
  */
}

int Ping(int pin) { return 0; }

#endif
