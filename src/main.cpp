// Define if you wish to debug memory usage.  Only works on T4.x
//#define DEBUG_MEMORY

#include <SPI.h>
#include <array>
#include <Wire.h>
#include <Entropy.h>

#include "config.h"
#include "util/logging.h"
#include "sensors/LightSensor.h"
#include "sensors/PersonSensor.h"

// ---------------------------------------------------------------------------
// JARVIS SERIAL BRIDGE CONFIG
// ---------------------------------------------------------------------------
// Serial (USB) is used to communicate with Pi4 assistant.py.
// Pi4 -> Teensy:  "EMOTION:HAPPY\n", "EMOTION:NEUTRAL\n", etc.
//                 "EYES:SLEEP\n"  -- blank both displays (black)
//                 "EYES:WAKE\n"   -- restore current eye definition
// Teensy -> Pi4:  "FACE:1\n" (face locked), "FACE:0\n" (face lost)
//
// TRACKING LOCKOUT:
// Face tracking is only active during a voice interaction window.
// When jarvis is not actively speaking/listening, the eyes wander
// randomly (autoMove) and ignore the person sensor. This prevents
// the robot from staring at people who haven't engaged with it.
//
// The Pi4 controls this via emotion commands:
//   Any non-NEUTRAL emotion => tracking unlocked for TRACKING_WINDOW_MS
//   NEUTRAL (idle reset)    => tracking locked immediately

static constexpr uint32_t TRACKING_WINDOW_MS   = 15000;
static constexpr uint32_t FACE_LOST_TIMEOUT_MS =  5000;
static constexpr uint32_t FACE_COOLDOWN_MS      = 30000;
static constexpr uint32_t SERIAL_BUF_SIZE       =    32;

// ANGRY eye swap: flame definition (index 1) held for this duration then auto-reverts
static constexpr uint32_t ANGRY_EYE_DURATION_MS = 9000;

// Eye definition indices (matches eyeDefinitions array in config.h)
static constexpr uint32_t EYE_IDX_DEFAULT = 0; // nordicBlue
static constexpr uint32_t EYE_IDX_ANGRY   = 1; // flame

// ---------------------------------------------------------------------------
// EMOTION -> EYE PARAMETER MAPPING
// ---------------------------------------------------------------------------

struct EmotionParams {
  float    pupilRatio;
  bool     doBlink;
  uint32_t maxGazeMs;
};

enum EmotionID { NEUTRAL=0, HAPPY, CURIOUS, ANGRY, SLEEPY, SURPRISED, SAD, EMOTION_COUNT };

static const EmotionParams emotionTable[EMOTION_COUNT] = {
  { 0.40f, false, 3000 }, // NEUTRAL
  { 0.75f, true,  1500 }, // HAPPY
  { 0.60f, false, 4000 }, // CURIOUS
  { 0.15f, false,  800 }, // ANGRY
  { 0.85f, true,  5000 }, // SLEEPY
  { 0.95f, true,   600 }, // SURPRISED
  { 0.25f, true,  4000 }, // SAD
};

// ---------------------------------------------------------------------------
// STATE
// ---------------------------------------------------------------------------

static uint32_t defIndex{EYE_IDX_DEFAULT};

LightSensor  lightSensor(LIGHT_PIN);
PersonSensor personSensor(Wire);
bool         personSensorFound = USE_PERSON_SENSOR;

static bool     trackingActive      = false;
static uint32_t trackingWindowStart = 0;

static bool     faceWasPresent  = false;
static uint32_t lastFace1SentMs = 0;

static char    serialBuf[SERIAL_BUF_SIZE];
static uint8_t serialBufLen = 0;

// Angry eye revert timer
static bool     angryEyeActive  = false;
static uint32_t angryEyeStartMs = 0;

// Eyes sleep state: when true, displays are blanked and renderFrame is skipped
static bool     eyesSleeping = false;

// ---------------------------------------------------------------------------
// HELPERS
// ---------------------------------------------------------------------------

bool hasBlinkButton() { return BLINK_PIN >= 0; }
bool hasLightSensor() { return LIGHT_PIN >= 0; }
bool hasJoystick()    { return JOYSTICK_X_PIN >= 0 && JOYSTICK_Y_PIN >= 0; }
bool hasPersonSensor(){ return personSensorFound; }

static void setEyeDefinition(uint32_t idx) {
  if (idx != defIndex) {
    defIndex = idx;
    eyes->updateDefinitions(eyeDefinitions[defIndex]);
  }
}

// Blank both displays using each display's own SPI bus via fillBlack().
// displayLeft and displayRight are stored globally in config.h after initEyes().
// This is safe for dual-SPI setups -- no raw SPI bus assumptions.
static void blankDisplays() {
#ifdef USE_GC9A01A
  if (displayLeft)  displayLeft->fillBlack();
  if (displayRight) displayRight->fillBlack();
#endif
  Serial.println("[DBG] EYES:SLEEP -- displays blanked");
}

static EmotionID parseEmotion(const char *name) {
  if (strcmp(name, "HAPPY")     == 0) return HAPPY;
  if (strcmp(name, "CURIOUS")   == 0) return CURIOUS;
  if (strcmp(name, "ANGRY")     == 0) return ANGRY;
  if (strcmp(name, "SLEEPY")    == 0) return SLEEPY;
  if (strcmp(name, "SURPRISED") == 0) return SURPRISED;
  if (strcmp(name, "SAD")       == 0) return SAD;
  return NEUTRAL;
}

static void applyEmotion(EmotionID id) {
  const EmotionParams &p = emotionTable[id];
  eyes->setTargetPupil(p.pupilRatio, 300);
  eyes->setMaxGazeMs(p.maxGazeMs);
  if (p.doBlink) eyes->blink();

  if (id == ANGRY) {
    setEyeDefinition(EYE_IDX_ANGRY);
    angryEyeActive  = true;
    angryEyeStartMs = millis();
  } else {
    if (angryEyeActive) {
      setEyeDefinition(EYE_IDX_DEFAULT);
      angryEyeActive = false;
    }
  }

  if (id == NEUTRAL) {
    trackingActive = false;
    eyes->setAutoMove(true);
  } else {
    trackingActive      = true;
    trackingWindowStart = millis();
  }
}

static void processSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialBufLen > 0) {
        serialBuf[serialBufLen] = '\0';
        serialBufLen = 0;

        if (strncmp(serialBuf, "EMOTION:", 8) == 0) {
          EmotionID id = parseEmotion(serialBuf + 8);
          Serial.print("[DBG] EMOTION cmd: ");
          Serial.print(serialBuf + 8);
          Serial.print(" -> id=");
          Serial.println(id);
          applyEmotion(id);

        } else if (strcmp(serialBuf, "EYES:SLEEP") == 0) {
          if (!eyesSleeping) {
            eyesSleeping   = true;
            angryEyeActive = false;
            blankDisplays();
          }

        } else if (strcmp(serialBuf, "EYES:WAKE") == 0) {
          if (eyesSleeping) {
            eyesSleeping = false;
            uint32_t saved = defIndex;
            defIndex = UINT32_MAX;
            setEyeDefinition(saved);
            applyEmotion(NEUTRAL);
            Serial.println("[DBG] EYES:WAKE -- displays restored");
          }
        }
      }
    } else {
      if (serialBufLen < SERIAL_BUF_SIZE - 1) {
        serialBuf[serialBufLen++] = c;
      }
    }
  }
}

static void reportFaceState(bool facePresent) {
  uint32_t now = millis();
  if (facePresent && !faceWasPresent) {
    if ((now - lastFace1SentMs) >= FACE_COOLDOWN_MS) {
      Serial.println("FACE:1");
      lastFace1SentMs = now;
    }
    faceWasPresent = true;
  } else if (!facePresent && faceWasPresent) {
    Serial.println("FACE:0");
    faceWasPresent = false;
  }
}

// ---------------------------------------------------------------------------
// SETUP
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 2000);
  delay(200);
  DumpMemoryInfo();
  Serial.println("[DBG] Init -- nordicBlue default, flame on ANGRY");
  Serial.flush();
  Entropy.Initialize();
  randomSeed(Entropy.random());

  if (hasBlinkButton()) pinMode(BLINK_PIN, INPUT_PULLUP);
  if (hasJoystick()) {
    pinMode(JOYSTICK_X_PIN, INPUT);
    pinMode(JOYSTICK_Y_PIN, INPUT);
  }

  if (hasPersonSensor()) {
    Wire.begin();
    personSensorFound = personSensor.isPresent();
    if (personSensorFound) {
      Serial.println("[DBG] Person Sensor detected");
      personSensor.enableID(false);
      personSensor.setMode(PersonSensor::Mode::Continuous);
    } else {
      Serial.println("[DBG] No Person Sensor found");
    }
  }

  initEyes(!hasJoystick(), !hasBlinkButton(), !hasLightSensor());
  applyEmotion(NEUTRAL);
}

// ---------------------------------------------------------------------------
// MAIN LOOP
// ---------------------------------------------------------------------------

void loop() {
  processSerial();

  // When sleeping, skip all eye logic -- displays stay black
  if (eyesSleeping) return;

  if (trackingActive && (millis() - trackingWindowStart) >= TRACKING_WINDOW_MS) {
    trackingActive = false;
    eyes->setAutoMove(true);
  }

  // Angry eye revert: flame -> nordicBlue after ANGRY_EYE_DURATION_MS
  if (angryEyeActive && (millis() - angryEyeStartMs) >= ANGRY_EYE_DURATION_MS) {
    setEyeDefinition(EYE_IDX_DEFAULT);
    angryEyeActive = false;
    Serial.println("[DBG] ANGRY revert -> nordicBlue");
  }

  if (hasBlinkButton() && digitalRead(BLINK_PIN) == LOW) eyes->blink();

  if (hasJoystick()) {
    auto x = analogRead(JOYSTICK_X_PIN);
    auto y = analogRead(JOYSTICK_Y_PIN);
    eyes->setPosition((x - 512) / 512.0f, (y - 512) / 512.0f);
  }

  if (hasLightSensor()) {
    lightSensor.readDamped([](float value) {
      eyes->setPupil(value);
    });
  }

  if (hasPersonSensor() && personSensor.read()) {
    int maxSize = 0;
    person_sensor_face_t maxFace{};

    for (int i = 0; i < personSensor.numFacesFound(); i++) {
      const person_sensor_face_t face = personSensor.faceDetails(i);
      if (face.is_facing && face.box_confidence > 60) {
        int size = (face.box_right - face.box_left) * (face.box_bottom - face.box_top);
        if (size > maxSize) {
          maxSize = size;
          maxFace = face;
        }
      }
    }

    bool facePresent = (maxSize > 0);
    reportFaceState(facePresent);

    if (trackingActive) {
      if (facePresent) {
        eyes->setAutoMove(false);
        float targetX = -((static_cast<float>(maxFace.box_left) +
                           static_cast<float>(maxFace.box_right - maxFace.box_left) / 2.0f) /
                          127.5f - 1.0f);
        float targetY = (static_cast<float>(maxFace.box_top) +
                         static_cast<float>(maxFace.box_bottom - maxFace.box_top) / 3.0f) /
                        127.5f - 1.0f;
        eyes->setTargetPosition(targetX, targetY);
      } else if (personSensor.timeSinceFaceDetectedMs() > FACE_LOST_TIMEOUT_MS &&
                 !eyes->autoMoveEnabled()) {
        eyes->setAutoMove(true);
      }
    }
  }

  eyes->renderFrame();
}
