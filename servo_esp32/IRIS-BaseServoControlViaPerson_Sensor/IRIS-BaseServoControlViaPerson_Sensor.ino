/*
IRIS project — ESP32 DevKit 1C (ESP32-WROOM-32)
Pan-only servo controller with Person Sensor + APDS-9960 gesture sensor
Last revised: 2026-05-21 joe schmidt

Pin#   Label
13     Pan servo PWM
21     SDA  I2C shared bus (Person Sensor 0x62, APDS-9960 0x39)
22     SCL  I2C shared bus

USB serial / Pi4 integration:
- USB-UART bridge to Pi4 (/dev/ttyUSB0, baud 9600)
- Commands sent: VOL_UP, VOL_DOWN, STOP, LISTEN
- Pi4 assistant.py servo_listener thread reads and dispatches these.
- Commands triggered by APDS-9960:
    UP gesture    → VOL_UP
    DOWN gesture  → VOL_DOWN
    LEFT gesture  → STOP
    RIGHT gesture → STOP
    Proximity > 150 held ~1s → LISTEN
*/

#include <Wire.h>
#include <ServoEasing.hpp>
#include <SparkFun_APDS9960.h>

// Person Sensor I2C address
#define PERSON_SENSOR_I2C_ADDRESS 0x62

// Maximum number of faces to detect
#define PERSON_SENSOR_FACE_MAX 6

// Pause between sensor polls (ms)
#define PERSON_SENSOR_DELAY 50

// Servo tracking constants
#define PAN_SPEED     0.04
#define PAN_DEAD_ZONE 2.0

// Face-lost timing (ms)
#define FACE_HOLD_MS   2500
#define FACE_RETURN_MS 8000

// Expected bytes from person sensor per poll
#define PS_EXPECTED_BYTES 18

// APDS-9960 proximity threshold and hold time for LISTEN trigger
#define PROX_LISTEN_THRESHOLD 150
#define PROX_HOLD_MS          1000

SparkFun_APDS9960 apds;
bool apdsOk = false;

ServoEasing panServo;

float desiredPan = 90.0;
unsigned long lastFaceMs = 0;

void setup() {
  Wire.begin(21, 22);

  panServo.attach(13);
  panServo.write((int)desiredPan);

  Serial.begin(9600);

  if (!apds.init()) {
    Serial.println("WARN: APDS-9960 not found");
  } else {
    apds.enableGestureSensor(true);
    apds.enableProximitySensor(false);
    apdsOk = true;
  }
}

void pollGesture() {
  if (!apdsOk) return;

  if (apds.isGestureAvailable()) {
    switch (apds.readGesture()) {
      case DIR_UP:    Serial.println("VOL_UP");  break;
      case DIR_DOWN:  Serial.println("VOL_DOWN"); break;
      case DIR_LEFT:  Serial.println("STOP");     break;
      case DIR_RIGHT: Serial.println("STOP");     break;
      default: break;
    }
  }

  // Proximity hold above threshold → LISTEN
  static unsigned long proxAboveMs = 0;
  static bool listenSent = false;
  uint8_t proxVal = 0;
  if (apds.readProximity(proxVal)) {
    if (proxVal > PROX_LISTEN_THRESHOLD) {
      if (proxAboveMs == 0) proxAboveMs = millis();
      if (!listenSent && (millis() - proxAboveMs >= PROX_HOLD_MS)) {
        Serial.println("LISTEN");
        listenSent = true;
      }
    } else {
      proxAboveMs = 0;
      listenSent = false;
    }
  }
}

void loop() {
  pollGesture();

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

    float faceCenterX = (mainFace.boxLeft + mainFace.boxRight) / 2.0;
    float panDelta = (faceCenterX - 128) * PAN_SPEED;
    if (abs(panDelta) > PAN_DEAD_ZONE / 90.0) {
      desiredPan -= panDelta;
      desiredPan = constrain(desiredPan, 0.0, 180.0);
      panServo.setEasingType(EASE_CUBIC_OUT);
      panServo.write((int)desiredPan);
    }

  } else {
    unsigned long elapsed = millis() - lastFaceMs;
    if (elapsed > FACE_RETURN_MS) {
      desiredPan += (90.0 - desiredPan) * 0.03;
      panServo.setEasingType(EASE_SINE_OUT);
      panServo.write((int)desiredPan);
    }
    // 0..FACE_HOLD_MS and FACE_HOLD_MS..FACE_RETURN_MS: hold position, do nothing
  }

  delay(PERSON_SENSOR_DELAY);
}
