#pragma once
#include <Arduino.h>

// Servo tracking constants
// PAN_SPEED: legacy delta scale used by updatePanFromFace; movement speed now governed by PAN_TRACK_SPEED
#define PAN_SPEED      0.02
#define PAN_TRACK_SPEED  8.0   // deg/sec — startEaseTo() for tracking and PAN serial command
#define PAN_FILTER_ALPHA 0.15  // low-pass weight per loop tick — smooths direction reversals
#define PAN_DEAD_ZONE    5.0

// Face-lost timing (ms)
#define FACE_HOLD_MS   2500
#define FACE_RETURN_MS 30000

// Pan servo rotation limits
#define PAN_MIN 65.0
#define PAN_MAX 115.0

// Current pan target (degrees). Exposed for diagnostic telemetry.
extern float desiredPan;

void setupPanServo();
void updatePanFromFace(float faceCenterX);
void updatePanIdle(unsigned long faceLostMs);

// Handles PAN / PAN? serial commands. Returns true if cmd was consumed.
// Active only when SERIAL_DIAG is enabled (matches original gating).
bool handleSerialPanCmd(String cmd);
