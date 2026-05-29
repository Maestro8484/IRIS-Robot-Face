#pragma once
#include <Arduino.h>

// Servo tracking constants
#define PAN_SPEED     0.02
#define PAN_DEAD_ZONE 5.0

// Face-lost timing (ms)
#define FACE_HOLD_MS   2500
#define FACE_RETURN_MS 6000

// Pan servo rotation limits
#define PAN_MIN 45.0
#define PAN_MAX 135.0

// Current pan target (degrees). Exposed for diagnostic telemetry.
extern float desiredPan;

void setupPanServo();
void updatePanFromFace(float faceCenterX);
void updatePanIdle(unsigned long faceLostMs);

// Handles PAN / PAN? serial commands. Returns true if cmd was consumed.
// Active only when SERIAL_DIAG is enabled (matches original gating).
bool handleSerialPanCmd(String cmd);
