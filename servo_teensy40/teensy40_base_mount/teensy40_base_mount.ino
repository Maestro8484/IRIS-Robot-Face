/*
IRIS project — Teensy 4.0
Pan-only servo controller with Person Sensor + APDS-9960 gesture sensor
Last revised: 2026-05-21 joe schmidt

Pin#   Label
2      Pan servo PWM
18     SDA  I2C shared bus (Person Sensor 0x62, APDS-9960 0x39)
19     SCL  I2C shared bus

USB serial / Pi4 integration:
- USB CDC serial to Pi4 (/dev/ttyACM1, baud 115200)
- Commands sent: VOL+, VOL-, STOP, LISTEN
- Pi4 hardware/base_mount_bridge.py daemon thread reads and dispatches these.
- Commands triggered by APDS-9960:
    UP gesture    → VOL+
    DOWN gesture  → VOL-
    LEFT gesture  → STOP
    RIGHT gesture → STOP
    Proximity > 150 held ~1s → LISTEN
*/

#include <Wire.h>
#include <ServoEasing.hpp>
#include <SparkFun_APDS9960.h>

extern "C" void _reboot_Teensyduino_(void);

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

// Set to 0 to disable the Person Sensor LED, 1 to enable
#define PERSON_SENSOR_LED_ENABLED 0

// Set to 1 to print a one-time I2C scan 10s after boot (diagnostic only)
#define I2C_SCAN_DIAG 0

// APDS-9960 proximity threshold and hold time for LISTEN trigger
#define PROX_LISTEN_THRESHOLD 150
#define PROX_HOLD_MS          1000

SparkFun_APDS9960 apds;
bool apdsOk = false;

ServoEasing panServo;

float desiredPan = 90.0;
unsigned long lastFaceMs = 0;

void setup() {
  Wire.begin();

  // Disable/enable Person Sensor LED (debug mode register)
  // Register 0x07 = PERSON_SENSOR_REG_DEBUG_MODE per SparkFun docs
  // If LED still on after flash, try 0x08 instead
  Wire.beginTransmission(PERSON_SENSOR_I2C_ADDRESS);
  Wire.write(0x07);
  Wire.write(PERSON_SENSOR_LED_ENABLED);
  Wire.endTransmission();

  panServo.attach(2);
  panServo.write((int)desiredPan);

  Serial.begin(115200);
  while (!Serial && millis() < 3000) {}  // wait up to 3s for monitor to reconnect after reboot

  // Read raw chip ID from register 0x92 before library init
  Wire.beginTransmission(0x39);
  Wire.write(0x92);
  Wire.endTransmission();
  Wire.requestFrom((uint8_t)0x39, (uint8_t)1);
  if (Wire.available()) {
    Serial.print("APDS ID reg: 0x");
    Serial.println(Wire.read(), HEX);
  } else {
    Serial.println("APDS ID reg: no response");
  }

  if (!apds.init()) {
    Serial.println("WARN: APDS-9960 init failed");
  } else {
    apds.enableGestureSensor(true);
    // NOTE: do NOT call enableProximitySensor(false) here —
    // gesture mode uses the proximity engine as its trigger internally.
    // Disabling proximity silently kills gesture detection.
    apdsOk = true;
  }
}

void pollGesture() {
  if (!apdsOk) return;

  if (apds.isGestureAvailable()) {
    switch (apds.readGesture()) {
      case DIR_UP:    Serial.println("VOL+");  break;
      case DIR_DOWN:  Serial.println("VOL-"); break;
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
  // Handle incoming serial commands
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "REBOOT") {
      _reboot_Teensyduino_();
    }
  }

#if I2C_SCAN_DIAG
  // One-time I2C scan 3s after boot — bridge has time to connect, output appears in journal
  static bool _i2cScanned = false;
  if (!_i2cScanned && millis() > 10000) {
    for (byte addr = 1; addr < 127; addr++) {
      Wire.beginTransmission(addr);
      if (Wire.endTransmission() == 0) {
        Serial.print("I2C_SCAN: 0x");
        Serial.println(addr, HEX);
      }
    }
    Serial.println("I2C_SCAN_DONE");
    _i2cScanned = true;
  }
#endif

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
