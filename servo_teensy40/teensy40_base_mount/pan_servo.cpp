#include "pan_servo.h"
#include <ServoEasing.hpp>   // ServoEasing implementation — included in exactly ONE translation unit
#include "diag.h"            // SERIAL_DIAG gating for PAN command

static ServoEasing panServo;

float desiredPan = 90.0;

void setupPanServo() {
  panServo.attach(2);
  panServo.write(desiredPan);
  panServo.setEasingType(EASE_CUBIC_IN_OUT);
  enableServoEasingInterrupt();
}

void updatePanFromFace(float faceCenterX) {
  float panDelta = (faceCenterX - 128) * PAN_SPEED;
  if (abs(panDelta) > PAN_DEAD_ZONE / 90.0) {
    desiredPan -= panDelta;
    desiredPan = constrain(desiredPan, PAN_MIN, PAN_MAX);
    if (!panServo.isMoving()) {
      panServo.startEaseToD(desiredPan, 100);
    }
  }
}

void updatePanIdle(unsigned long faceLostMs) {
  if (faceLostMs > FACE_RETURN_MS) {
    desiredPan += (90.0 - desiredPan) * 0.03;
    if (!panServo.isMoving()) {
      panServo.startEaseToD(desiredPan, 100);
    }
  }
  // 0..FACE_HOLD_MS and FACE_HOLD_MS..FACE_RETURN_MS: hold position, do nothing
}

bool handleSerialPanCmd(String cmd) {
#if SERIAL_DIAG
  // ===== CODEX DIAGNOSTIC INSERT BEGIN: direct servo isolation command =====
  if (cmd.startsWith("PAN ")) {
    desiredPan = constrain(cmd.substring(4).toFloat(), PAN_MIN, PAN_MAX);
    panServo.startEaseToD(desiredPan, 100);
    Serial.print("DIAG: manual pan target=");
    Serial.println((int)desiredPan);
    return true;
  } else if (cmd == "PAN?") {
    Serial.print("PAN=");
    Serial.println(panServo.getCurrentAngle());
    return true;
  }
  // ===== CODEX DIAGNOSTIC INSERT END: direct servo isolation command =====
#endif
  return false;
}
