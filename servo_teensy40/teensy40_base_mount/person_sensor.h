#pragma once
#include <Arduino.h>

// Person Sensor I2C address
#define PERSON_SENSOR_I2C_ADDRESS 0x62

// ===== CODEX DIAGNOSTIC INSERT BEGIN: Person Sensor packet definition =====
// The Person Sensor returns four fixed face slots in every 39-byte result packet.
#define PERSON_SENSOR_FACE_MAX 4
#define PS_EXPECTED_BYTES (4 + 1 + (PERSON_SENSOR_FACE_MAX * 8) + 2)
// ===== CODEX DIAGNOSTIC INSERT END: Person Sensor packet definition =====

// Pause between sensor polls (ms)
#define PERSON_SENSOR_DELAY 50

// Set to 0 to disable the Person Sensor LED, 1 to enable
#define PERSON_SENSOR_LED_ENABLED 0

// Result of one poll cycle.
//   ok          = a full valid packet was read this cycle. When false the
//                 caller must skip pan dispatch entirely (matches the original
//                 short-read early-return: pan is held, not driven).
//   faceVisible = an accepted, facing, high-confidence face is present.
struct PersonResult {
  bool    ok;
  bool    faceVisible;
  float   faceCenterX;
  uint8_t confidence;
  bool    isFacing;
};

void setupPersonSensor();
PersonResult pollPersonSensor();
