/*
reviewed revised 5.20.2026 joe schmidt
IRIS project

Rasp pi pico W
physical pin  GPIO   Label
1             0      Pan servo PWM
2             1      Tilt servo PWM
9             6      SDA  I2C person sensor
10            7      SCL  I2C person sensor
20            15     TTP223B touch sensor OUT
21            GND    TTP223B touch sensor GND
*/

#include <Wire.h>
#include <ServoEasing.hpp>

// The person sensor has the I2C ID of hex 62, or decimal 98.
#define PERSON_SENSOR_I2C_ADDRESS 0x62

// The maximum number of faces to detect.
#define PERSON_SENSOR_FACE_MAX 6

// How long to pause between sensor polls.
#define PERSON_SENSOR_DELAY 50

// Controls how fast the servos track.
#define PAN_SPEED  0.04
#define TILT_SPEED 0.04

// Dead zone: ignore movement smaller than this (degrees equivalent — tune up if jittery)
#define PAN_DEAD_ZONE  2.0
#define TILT_DEAD_ZONE 2.0

// Face-lost timing (ms)
#define FACE_HOLD_MS   2500   // hold position after face is lost
#define FACE_RETURN_MS 8000   // begin slow center-return after this long without a face

// Expected bytes from person sensor per poll
#define PS_EXPECTED_BYTES 18

// TTP223B capacitive touch toggle (GPIO 15, physical pin 20)
#define TOUCH_PIN 15

ServoEasing panServo;
ServoEasing tiltServo;

float desiredPan  = 90.0;
float desiredTilt = 90.0;

unsigned long lastFaceMs = 0;
bool servoEnabled = false;

void setup() {
  Wire.setSDA(6);
  Wire.setSCL(7);
  Wire.begin();

  panServo.attach(0);
  panServo.write((int)desiredPan);

  tiltServo.attach(1);
  tiltServo.write((int)desiredTilt);

  pinMode(TOUCH_PIN, INPUT);

  Serial.begin(9600);
}

void loop() {
  static bool lastTouch = false;
  bool touch = digitalRead(TOUCH_PIN);
  if (touch && !lastTouch) servoEnabled = !servoEnabled;
  lastTouch = touch;
  if (!servoEnabled) { delay(PERSON_SENSOR_DELAY); return; }

  byte readData[PS_EXPECTED_BYTES];

  int available = Wire.requestFrom(PERSON_SENSOR_I2C_ADDRESS, PS_EXPECTED_BYTES);
  if (available < PS_EXPECTED_BYTES) {
    delay(PERSON_SENSOR_DELAY);
    return;
  }
  for (int i = 0; i < PS_EXPECTED_BYTES; i++) {
    readData[i] = Wire.read();
  }

  int offset = 0;

  // Unpack header
  uint8_t pad1 = readData[offset++];
  uint8_t pad2 = readData[offset++];
  uint16_t payloadBytes = (readData[offset++] << 8) | readData[offset++];

  // Number of faces
  uint8_t numFaces = readData[offset++];

  struct Face {
    uint8_t boxConfidence;
    uint8_t boxLeft;
    uint8_t boxTop;
    uint8_t boxRight;
    uint8_t boxBottom;
    int8_t  idConfidence;
    uint8_t id;
    uint8_t isFacing;
  } faces[PERSON_SENSOR_FACE_MAX];

  for (int i = 0; i < numFaces && i < PERSON_SENSOR_FACE_MAX; i++) {
    faces[i].boxConfidence = readData[offset++];
    faces[i].boxLeft       = readData[offset++];
    faces[i].boxTop        = readData[offset++];
    faces[i].boxRight      = readData[offset++];
    faces[i].boxBottom     = readData[offset++];
    faces[i].idConfidence  = readData[offset++];
    faces[i].id            = readData[offset++];
    faces[i].isFacing      = readData[offset++];
  }

  // Checksum
  uint16_t checksum = (readData[offset++] << 8) | readData[offset++];

  // Confidence + facing gate: reject low-confidence or non-facing detections
  if (numFaces > 0) {
    if (faces[0].boxConfidence < 60 || !faces[0].isFacing) {
      numFaces = 0;
    }
  }

  if (numFaces > 0) {
    lastFaceMs = millis();
    Face& mainFace = faces[0];

    // Pan
    float faceCenterX = (mainFace.boxLeft + mainFace.boxRight) / 2.0;
    float panDelta = (faceCenterX - 128) * PAN_SPEED;
    if (abs(panDelta) > PAN_DEAD_ZONE / 90.0) {
      desiredPan -= panDelta;
      desiredPan = constrain(desiredPan, 0.0, 180.0);
      panServo.setEasingType(EASE_CUBIC_OUT);
      panServo.write((int)desiredPan);
    }

    // Tilt
    float faceCenterY = (mainFace.boxTop + mainFace.boxBottom) / 2.0;
    float tiltDelta = (faceCenterY - 128) * TILT_SPEED;
    if (abs(tiltDelta) > TILT_DEAD_ZONE / 90.0) {
      desiredTilt -= tiltDelta;
      desiredTilt = constrain(desiredTilt, 0.0, 180.0);
      tiltServo.setEasingType(EASE_CUBIC_OUT);
      tiltServo.write((int)desiredTilt);
    }

  } else {
    unsigned long elapsed = millis() - lastFaceMs;
    if (elapsed > FACE_RETURN_MS) {
      // Slowly drift back to center
      desiredPan  += (90.0 - desiredPan)  * 0.03;
      desiredTilt += (90.0 - desiredTilt) * 0.03;
      panServo.setEasingType(EASE_SINE_OUT);
      tiltServo.setEasingType(EASE_SINE_OUT);
      panServo.write((int)desiredPan);
      tiltServo.write((int)desiredTilt);
    }
    // 0..FACE_HOLD_MS and FACE_HOLD_MS..FACE_RETURN_MS: hold position, do nothing
  }

  delay(PERSON_SENSOR_DELAY);
}
