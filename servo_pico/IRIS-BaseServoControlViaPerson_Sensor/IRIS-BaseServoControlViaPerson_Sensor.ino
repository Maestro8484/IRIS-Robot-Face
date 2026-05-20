/*
reviewed revised 5.20.2026 joe schmidt
IRIS project

Rasp pi pico W
physical pin  GPIO   Label
1             0      Pan servo PWM
9             6      SDA  I2C person sensor
10            7      SCL  I2C person sensor
17            13     Momentary button — volume (GPIO 13, GND + INPUT_PULLUP)
19            14     Momentary button — TTS/wakeword (GPIO 14, GND + INPUT_PULLUP)
20            15     Momentary button — reserved (GPIO 15, wired unassigned)
18/21         GND    Button GND (shared)

USB serial / Pi4 integration:
- USB CDC serial to Pi4 (/dev/ttyACM1, baud 9600)
- Commands sent: VOL_UP, VOL_DOWN, STOP, LISTEN
- Pi4 assistant.py pico_listener thread reads and dispatches these.
*/

#include <Wire.h>
#include <ServoEasing.hpp>

// The person sensor has the I2C ID of hex 62, or decimal 98.
#define PERSON_SENSOR_I2C_ADDRESS 0x62

// The maximum number of faces to detect.
#define PERSON_SENSOR_FACE_MAX 6

// How long to pause between sensor polls.
#define PERSON_SENSOR_DELAY 50

// Controls how fast the servo tracks.
#define PAN_SPEED  0.04

// Dead zone: ignore movement smaller than this (degrees equivalent — tune up if jittery)
#define PAN_DEAD_ZONE  2.0

// Face-lost timing (ms)
#define FACE_HOLD_MS   2500   // hold position after face is lost
#define FACE_RETURN_MS 8000   // begin slow center-return after this long without a face

// Expected bytes from person sensor per poll
#define PS_EXPECTED_BYTES 18

// Momentary pushbuttons (active-low, INPUT_PULLUP, one terminal to GND)
#define TOUCH1_PIN 15   // reserved — wired, unassigned
#define TOUCH2_PIN 13   // volume hold-toggle
#define TOUCH3_PIN 14   // TTS interrupt / wakeword trigger

ServoEasing panServo;

float desiredPan = 90.0;

unsigned long lastFaceMs = 0;

void setup() {
  Wire.setSDA(6);
  Wire.setSCL(7);
  Wire.begin();

  panServo.attach(0);
  panServo.write((int)desiredPan);

  pinMode(TOUCH1_PIN, INPUT_PULLUP);
  pinMode(TOUCH2_PIN, INPUT_PULLUP);
  pinMode(TOUCH3_PIN, INPUT_PULLUP);

  Serial.begin(9600);
}

void loop() {
  // ── Touch 1 — reserved (GPIO 15, TTP223B wired but unassigned) ──────────

  // ── Touch 2 — volume hold-toggle ─────────────────────────────────────────
  static bool lastTouch2      = false;
  static bool volIncreasing   = false;  // false→first hold flips true (increasing)
  static unsigned long lastVolTickMs = 0;

  bool touch2 = !digitalRead(TOUCH2_PIN);
  if (touch2 && !lastTouch2) {
    volIncreasing = !volIncreasing;   // reverse direction on each new hold
  }
  if (touch2 && (millis() - lastVolTickMs > 200)) {
    lastVolTickMs = millis();
    Serial.println(volIncreasing ? "VOL_UP" : "VOL_DOWN");
  }
  lastTouch2 = touch2;

  // ── Touch 3 — TTS interrupt (short tap) / wakeword trigger (long hold) ───
  static bool lastTouch3 = false;
  static unsigned long touch3PressMs = 0;

  bool touch3 = !digitalRead(TOUCH3_PIN);
  if (touch3 && !lastTouch3) touch3PressMs = millis();
  if (!touch3 && lastTouch3) {
    unsigned long held = millis() - touch3PressMs;
    Serial.println(held < 1000 ? "STOP" : "LISTEN");
  }
  lastTouch3 = touch3;

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
