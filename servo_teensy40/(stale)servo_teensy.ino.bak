// =============================================================================
// WALL-E SERVO TEENSY 4.0
// Standalone pan tracking -- no serial comms, fully autonomous
//
// Hardware:
//   - Teensy 4.0
//   - Person Sensor (Useful Sensors) on I2C (SDA/SCL, address 0x62)
//   - SG90 servo on SERVO_PIN
//
// Behavior:
//   - Continuously reads Person Sensor
//   - Pans servo to track largest facing face (X position)
//   - Exponential smoothing prevents jitter
//   - No face: slow left-right idle sweep
//   - Face lost mid-track: hold position FACE_HOLD_MS then resume sweep
// =============================================================================

#include <Arduino.h>
#include <Wire.h>
#include <Servo.h>

// ---------------------------------------------------------------------------
// TUNABLE CONSTANTS
// ---------------------------------------------------------------------------

constexpr int     SERVO_PIN       = 3;    // PWM pin for SG90
constexpr float   SERVO_CENTER    = 90.0f; // degrees -- adjust for physical center
constexpr float   SERVO_MIN       = 45.0f; // left travel limit (degrees)
constexpr float   SERVO_MAX       = 135.0f; // right travel limit (degrees)

// Smoothing: lower = slower/smoother, higher = faster/snappier
// 0.10 = gentle tracking, 0.25 = responsive tracking
constexpr float   SMOOTH_FACTOR   = 0.12f;

// Idle sweep
constexpr float   SWEEP_STEP      = 0.25f;  // degrees per loop when no face
constexpr uint32_t SWEEP_PAUSE_MS = 1500;   // ms to pause at each sweep limit

// How long to hold position after losing a face before resuming sweep
constexpr uint32_t FACE_HOLD_MS   = 3000;

// Person Sensor
constexpr uint8_t  PS_I2C_ADDR    = 0x62;
constexpr uint32_t PS_SAMPLE_MS   = 200;   // sensor updates at ~5Hz
constexpr uint8_t  PS_MIN_CONF    = 60;    // minimum box_confidence to trust

// ---------------------------------------------------------------------------
// PERSON SENSOR STRUCTS (matches Useful Sensors wire format)
// ---------------------------------------------------------------------------

typedef struct __attribute__((__packed__)) {
  uint8_t  reserved[2];
  uint16_t data_size;
} ps_header_t;

typedef struct __attribute__((__packed__)) {
  uint8_t box_confidence;
  uint8_t box_left;
  uint8_t box_top;
  uint8_t box_right;
  uint8_t box_bottom;
  int8_t  id_confidence;
  int8_t  id;
  uint8_t is_facing;
} ps_face_t;

typedef struct __attribute__((__packed__)) {
  ps_header_t header;
  int8_t      num_faces;
  ps_face_t   faces[4];
  uint16_t    checksum;
} ps_results_t;

// ---------------------------------------------------------------------------
// STATE
// ---------------------------------------------------------------------------

Servo servo;

float   currentAngle    = SERVO_CENTER;
float   targetAngle     = SERVO_CENTER;

bool    faceTracking    = false;
uint32_t faceLostTimeMs = 0;

// Sweep state
float   sweepAngle      = SERVO_CENTER;
float   sweepDir        = 1.0f; // +1 right, -1 left
bool    sweepPausing    = false;
uint32_t sweepPauseStart = 0;

elapsedMillis sampleTimer;

// ---------------------------------------------------------------------------
// PERSON SENSOR
// ---------------------------------------------------------------------------

bool psRead(ps_results_t &results) {
  Wire.requestFrom(PS_I2C_ADDR, sizeof(ps_results_t));
  if (Wire.available() != sizeof(ps_results_t)) return false;
  auto *b = (uint8_t *)&results;
  for (size_t i = 0; i < sizeof(ps_results_t); i++) {
    b[i] = Wire.read();
  }
  return true;
}

bool psPresent() {
  Wire.beginTransmission(PS_I2C_ADDR);
  return Wire.endTransmission() == 0;
}

// ---------------------------------------------------------------------------
// SERVO HELPERS
// ---------------------------------------------------------------------------

float clampAngle(float a) {
  return max(SERVO_MIN, min(SERVO_MAX, a));
}

void writeServo(float angle) {
  servo.write((int)clampAngle(angle));
}

// ---------------------------------------------------------------------------
// SETUP
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 2000);

  Wire.begin();
  delay(100);

  if (psPresent()) {
    Serial.println("[SERVO] Person Sensor detected");
    // Set continuous mode
    Wire.beginTransmission(PS_I2C_ADDR);
    Wire.write(0x01); // Mode register
    Wire.write(0x01); // Continuous
    Wire.endTransmission();
    // Disable ID recognition (not needed, saves processing)
    Wire.beginTransmission(PS_I2C_ADDR);
    Wire.write(0x02); // EnableID register
    Wire.write(0x00);
    Wire.endTransmission();
  } else {
    Serial.println("[SERVO] No Person Sensor found -- running sweep only");
  }

  servo.attach(SERVO_PIN);
  writeServo(SERVO_CENTER);
  sweepAngle = SERVO_CENTER;

  Serial.println("[SERVO] Ready");
}

// ---------------------------------------------------------------------------
// IDLE SWEEP
// ---------------------------------------------------------------------------

void updateSweep() {
  uint32_t now = millis();

  if (sweepPausing) {
    if (now - sweepPauseStart >= SWEEP_PAUSE_MS) {
      sweepPausing = false;
      sweepDir = -sweepDir; // reverse
    }
    return;
  }

  sweepAngle += sweepDir * SWEEP_STEP;

  if (sweepAngle >= SERVO_MAX) {
    sweepAngle = SERVO_MAX;
    sweepPausing = true;
    sweepPauseStart = now;
  } else if (sweepAngle <= SERVO_MIN) {
    sweepAngle = SERVO_MIN;
    sweepPausing = true;
    sweepPauseStart = now;
  }

  targetAngle = sweepAngle;
}

// ---------------------------------------------------------------------------
// MAIN LOOP
// ---------------------------------------------------------------------------

void loop() {
  bool gotFace = false;

  // Read person sensor at PS_SAMPLE_MS rate
  if (sampleTimer >= PS_SAMPLE_MS) {
    sampleTimer = 0;

    ps_results_t results{};
    if (psRead(results)) {
      // Find largest facing face
      int   maxSize = 0;
      float faceX   = 127.5f; // default center (0-255 range)

      for (int i = 0; i < results.num_faces; i++) {
        const ps_face_t &f = results.faces[i];
        if (f.is_facing && f.box_confidence >= PS_MIN_CONF) {
          int size = (f.box_right - f.box_left) * (f.box_bottom - f.box_top);
          if (size > maxSize) {
            maxSize = size;
            // Face X center in 0-255 sensor space
            faceX = f.box_left + (f.box_right - f.box_left) / 2.0f;
          }
        }
      }

      if (maxSize > 0) {
        gotFace = true;
        faceTracking = true;

        // Map face X (0-255) to servo angle (SERVO_MAX to SERVO_MIN)
        // Inverted: face on left (low X) = servo turns left (lower angle)
        // Adjust sign if servo moves wrong direction
        float mapped = SERVO_MAX - (faceX / 255.0f) * (SERVO_MAX - SERVO_MIN);
        targetAngle = mapped;

        // Update sweep anchor so if face is lost, sweep starts from here
        sweepAngle = clampAngle(mapped);
      }
    }
  }

  // Face lost handling
  if (!gotFace && faceTracking) {
    if (faceLostTimeMs == 0) {
      faceLostTimeMs = millis();
    }
    if (millis() - faceLostTimeMs >= FACE_HOLD_MS) {
      // Done holding -- return to sweep
      faceTracking   = false;
      faceLostTimeMs = 0;
      Serial.println("[SERVO] Face lost, resuming sweep");
    }
    // While holding: keep targetAngle where it is, don't sweep
  }

  if (gotFace) {
    faceLostTimeMs = 0; // reset lost timer while face is present
  }

  // If not tracking a face and not holding, run idle sweep
  if (!faceTracking && faceLostTimeMs == 0) {
    updateSweep();
  }

  // Exponential smoothing toward target
  currentAngle += (targetAngle - currentAngle) * SMOOTH_FACTOR;
  writeServo(currentAngle);

  delay(10); // ~100Hz update rate
}
