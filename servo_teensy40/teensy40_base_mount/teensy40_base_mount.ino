/*
IRIS project — Teensy 4.0
Pan-only servo controller with Person Sensor + PAJ7620U2 gesture sensor
Last revised: 2026-05-27 joe schmidt

Pin#   Label
2      Pan servo PWM
15     T3   Capacitive touch (STOP tap / LISTEN hold)
18     SDA  I2C shared bus (Person Sensor 0x62, PAJ7620U2 0x73)
19     SCL  I2C shared bus

USB serial / Pi4 integration:
- USB CDC serial to Pi4 (/dev/ttyIRIS_SERVO, baud 115200)
- Commands sent: VOL+, VOL-, STOP, LISTEN
- Pi4 hardware/base_mount_bridge.py daemon thread reads and dispatches these.
- Commands triggered by PAJ7620U2:
    UP gesture    → VOL+
    DOWN gesture  → VOL-
    LEFT gesture  → STOP
    RIGHT gesture → STOP
- Commands triggered by touch3 (pin 15):
    Short tap (<1s)  → STOP
    Long hold (>=1s) → LISTEN
*/

#include <Wire.h>
#include <ServoEasing.hpp>

extern "C" void _reboot_Teensyduino_(void);

// Person Sensor I2C address
#define PERSON_SENSOR_I2C_ADDRESS 0x62

// ===== CODEX DIAGNOSTIC INSERT BEGIN: Person Sensor packet definition =====
// The Person Sensor returns four fixed face slots in every 39-byte result packet.
#define PERSON_SENSOR_FACE_MAX 4
#define PS_EXPECTED_BYTES (4 + 1 + (PERSON_SENSOR_FACE_MAX * 8) + 2)

// Set to 0 after diagnosis to remove serial monitor output and PAN test commands.
#define SERIAL_DIAG 1
// ===== CODEX DIAGNOSTIC INSERT END: Person Sensor packet definition =====

// Pause between sensor polls (ms)
#define PERSON_SENSOR_DELAY 50

// Servo tracking constants
#define PAN_SPEED     0.02
#define PAN_DEAD_ZONE 5.0

// Face-lost timing (ms)
#define FACE_HOLD_MS   2500
#define FACE_RETURN_MS 6000

// Set to 0 to disable the Person Sensor LED, 1 to enable
#define PERSON_SENSOR_LED_ENABLED 0

// Set to 1 to print a one-time I2C scan 10s after boot (diagnostic only)
#define I2C_SCAN_DIAG 0

// PAJ7620U2 gesture sensor
#define PAJ7620_ADDR 0x73

// Touch3 LISTEN/STOP trigger (T3 = pin 15 on Teensy 4.0)
#define TOUCH3_PIN     15
#define TOUCH3_THRESH  1500   // tune: SERIAL_DIAG prints raw touchRead value each second
#define TOUCH3_HOLD_MS 1000

bool pajOk = false;

ServoEasing panServo;

float desiredPan = 90.0;
unsigned long lastFaceMs = 0;

static void paj_write(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(PAJ7620_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

static uint8_t paj_read(uint8_t reg) {
  Wire.beginTransmission(PAJ7620_ADDR);
  Wire.write(reg);
  Wire.endTransmission();
  Wire.requestFrom((uint8_t)PAJ7620_ADDR, (uint8_t)1);
  return Wire.available() ? Wire.read() : 0;
}

static bool paj7620Init() {
  // Wake device from suspend (any I2C access wakes it), then wait for ready
  Wire.beginTransmission(PAJ7620_ADDR);
  Wire.endTransmission();
  delay(700);

  // Confirm device responds at 0x73
  Wire.beginTransmission(PAJ7620_ADDR);
  if (Wire.endTransmission() != 0) return false;

  // Bank 0 config
  paj_write(0xEF, 0x00);
  paj_write(0x37, 0x07); paj_write(0x38, 0x17); paj_write(0x39, 0x06);
  paj_write(0x42, 0x01); paj_write(0x46, 0x2D); paj_write(0x47, 0x0F);
  paj_write(0x48, 0x3C); paj_write(0x49, 0x00); paj_write(0x4A, 0x1E);
  paj_write(0x4C, 0x20); paj_write(0x51, 0x10); paj_write(0x5E, 0x10);
  paj_write(0x60, 0x27); paj_write(0x80, 0x42); paj_write(0x81, 0x44);
  paj_write(0x82, 0x04); paj_write(0x8B, 0x01); paj_write(0x90, 0x06);
  paj_write(0x95, 0x0A); paj_write(0x96, 0x0C); paj_write(0x97, 0x05);
  paj_write(0x9A, 0x14); paj_write(0x9C, 0x3F); paj_write(0xA5, 0x19);
  paj_write(0xCC, 0x19); paj_write(0xCD, 0x0B); paj_write(0xCE, 0x13);
  paj_write(0xCF, 0x64); paj_write(0xD0, 0x21);

  // Bank 1 config
  paj_write(0xEF, 0x01);
  paj_write(0x02, 0x15); paj_write(0x03, 0x10); paj_write(0x04, 0x02);
  paj_write(0x25, 0x01); paj_write(0x27, 0x39); paj_write(0x28, 0x7F);
  paj_write(0x29, 0x08); paj_write(0x3E, 0xFF); paj_write(0x5E, 0xFF);
  paj_write(0x65, 0x9B); paj_write(0x67, 0x97); paj_write(0x69, 0xCD);
  paj_write(0x6A, 0x01); paj_write(0x6D, 0x2C); paj_write(0x6E, 0x01);
  paj_write(0x72, 0x01); paj_write(0x73, 0x35); paj_write(0x74, 0x00);
  paj_write(0x77, 0x01);

  // Back to bank 0, enable gesture detection
  paj_write(0xEF, 0x00);
  paj_write(0x41, 0xFF);  // unmask all gesture interrupts
  paj_write(0x42, 0x01);  // gesture mode

  return true;
}

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

#if SERIAL_DIAG
  // ===== CODEX DIAGNOSTIC INSERT BEGIN: boot status and I2C presence probe =====
  Serial.println("DIAG: boot; servo commanded center=90 on PWM pin 2");
  Wire.beginTransmission(PERSON_SENSOR_I2C_ADDRESS);
  Serial.print("DIAG: Person Sensor 0x62 ACK=");
  Serial.println(Wire.endTransmission() == 0 ? "YES" : "NO");
  Wire.beginTransmission(PAJ7620_ADDR);
  Serial.print("DIAG: PAJ7620U2 0x73 ACK=");
  Serial.println(Wire.endTransmission() == 0 ? "YES" : "NO");
  // ===== CODEX DIAGNOSTIC INSERT END: boot status and I2C presence probe =====
#endif

  pajOk = paj7620Init();
#if SERIAL_DIAG
  Serial.print("DIAG: PAJ7620U2 init=");
  Serial.println(pajOk ? "OK" : "FAIL");
#endif
}

void pollGesture() {
  if (!pajOk) return;
  paj_write(0xEF, 0x00);  // ensure bank 0
  uint8_t gest = paj_read(0x43);
  if (gest == 0) return;
  if      (gest & 0x01) Serial.println("VOL+");  // UP
  else if (gest & 0x02) Serial.println("VOL-");  // DOWN
  else if (gest & 0x04) Serial.println("STOP");  // LEFT
  else if (gest & 0x08) Serial.println("STOP");  // RIGHT
}

void pollTouch3() {
  static unsigned long holdMs = 0;
  static bool listenSent = false;
  uint16_t t3 = touchRead(TOUCH3_PIN);
#if SERIAL_DIAG
  static unsigned long lastT3DiagMs = 0;
  if (millis() - lastT3DiagMs >= 1000) {
    Serial.print("DIAG: touch3=");
    Serial.println(t3);
    lastT3DiagMs = millis();
  }
#endif
  if (t3 > TOUCH3_THRESH) {
    if (holdMs == 0) holdMs = millis();
    if (!listenSent && (millis() - holdMs >= TOUCH3_HOLD_MS)) {
      Serial.println("LISTEN");
      listenSent = true;
    }
  } else {
    if (holdMs != 0 && !listenSent) {
      Serial.println("STOP");  // short tap on release
    }
    holdMs = 0;
    listenSent = false;
  }
}

void loop() {
  // Handle incoming serial commands
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "REBOOT") {
      _reboot_Teensyduino_();
#if SERIAL_DIAG
    // ===== CODEX DIAGNOSTIC INSERT BEGIN: direct servo isolation command =====
    } else if (cmd.startsWith("PAN ")) {
      desiredPan = constrain(cmd.substring(4).toInt(), 0, 180);
      panServo.write((int)desiredPan);
      Serial.print("DIAG: manual pan target=");
      Serial.println((int)desiredPan);
    // ===== CODEX DIAGNOSTIC INSERT END: direct servo isolation command =====
#endif
    }
  }

#if I2C_SCAN_DIAG
  // One-time I2C scan 10s after boot — bridge has time to connect, output appears in journal
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
  pollTouch3();

  byte readData[PS_EXPECTED_BYTES];

#if SERIAL_DIAG
  // ===== CODEX DIAGNOSTIC INSERT BEGIN: rate limit sensor status output =====
  static unsigned long lastPsDiagMs = 0;
  // ===== CODEX DIAGNOSTIC INSERT END: rate limit sensor status output =====
#endif

  int available = Wire.requestFrom(PERSON_SENSOR_I2C_ADDRESS, PS_EXPECTED_BYTES);
  if (available < PS_EXPECTED_BYTES) {
#if SERIAL_DIAG
    // ===== CODEX DIAGNOSTIC INSERT BEGIN: failed sensor-read report =====
    if (millis() - lastPsDiagMs >= 500) {
      Serial.print("DIAG: Person Sensor read bytes=");
      Serial.println(available);
      lastPsDiagMs = millis();
    }
    // ===== CODEX DIAGNOSTIC INSERT END: failed sensor-read report =====
#endif
    delay(PERSON_SENSOR_DELAY);
    return;
  }
  for (int i = 0; i < PS_EXPECTED_BYTES; i++) {
    readData[i] = Wire.read();
  }

  int offset = 0;

  // ===== CODEX DIAGNOSTIC INSERT BEGIN: safely decode packet metadata =====
  // Skip reserved header bytes and avoid undefined multiple increments in one expression.
  offset += 2;
  uint16_t payloadBytes = readData[offset] | (static_cast<uint16_t>(readData[offset + 1]) << 8);
  offset += 2;

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

  // ===== CODEX DIAGNOSTIC INSERT BEGIN: consume the fixed four-face packet =====
  for (int i = 0; i < PERSON_SENSOR_FACE_MAX; i++) {
    faces[i].boxConfidence = readData[offset++];
    faces[i].boxLeft       = readData[offset++];
    faces[i].boxTop        = readData[offset++];
    faces[i].boxRight      = readData[offset++];
    faces[i].boxBottom     = readData[offset++];
    faces[i].idConfidence  = readData[offset++];
    faces[i].id            = readData[offset++];
    faces[i].isFacing      = readData[offset++];
  }
  // ===== CODEX DIAGNOSTIC INSERT END: consume the fixed four-face packet =====

  // Checksum
  uint16_t checksum = readData[offset] | (static_cast<uint16_t>(readData[offset + 1]) << 8);
  // ===== CODEX DIAGNOSTIC INSERT END: safely decode packet metadata =====

  // ===== CODEX DIAGNOSTIC INSERT BEGIN: reject invalid reported face count =====
  uint8_t reportedFaces = numFaces;
  if (numFaces > PERSON_SENSOR_FACE_MAX) {
    numFaces = 0;
  }
  // ===== CODEX DIAGNOSTIC INSERT END: reject invalid reported face count =====

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

#if SERIAL_DIAG
  // ===== CODEX DIAGNOSTIC INSERT BEGIN: visible face and pan telemetry =====
  if (millis() - lastPsDiagMs >= 500) {
    Serial.print("DIAG: PS bytes=");
    Serial.print(available);
    Serial.print(" reportedFaces=");
    Serial.print(reportedFaces);
    Serial.print(" acceptedFaces=");
    Serial.print(numFaces);
    Serial.print(" payloadBytes=");
    Serial.print(payloadBytes);
    Serial.print(" checksum=0x");
    Serial.print(checksum, HEX);
    if (reportedFaces > 0 && reportedFaces <= PERSON_SENSOR_FACE_MAX) {
      Serial.print(" conf=");
      Serial.print(faces[0].boxConfidence);
      Serial.print(" facing=");
      Serial.print(faces[0].isFacing);
    }
    Serial.print(" pan=");
    Serial.println((int)desiredPan);
    lastPsDiagMs = millis();
  }
  // ===== CODEX DIAGNOSTIC INSERT END: visible face and pan telemetry =====
#endif

  delay(PERSON_SENSOR_DELAY);
}
