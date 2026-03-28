// Define if you wish to debug memory usage.  Only works on T4.x
//#define DEBUG_MEMORY

#include <SPI.h>
#include <array>
#include <Wire.h>
#include <Entropy.h>

#include "config.h"
#include "mouth.h"
#include "sleep_renderer.h"
#include "util/logging.h"
#include "sensors/LightSensor.h"
#include "sensors/PersonSensor.h"

// ---------------------------------------------------------------------------
// JARVIS SERIAL BRIDGE CONFIG
// ---------------------------------------------------------------------------
// Serial (USB) is used to communicate with Pi4 assistant.py.
// Pi4 -> Teensy:  "EMOTION:HAPPY\n", "EMOTION:NEUTRAL\n", etc.
//                 "EYES:SLEEP\n"      -- blank both displays (black)
//                 "EYES:WAKE\n"       -- restore current eye definition
//                 "EYE:n\n"           -- switch default eye to index n (web UI)
// Teensy -> Pi4:  "FACE:1\n" (face locked), "FACE:0\n" (face lost)
//
// EYE INDEX MAP (matches eyeDefinitions in config.h):
//   0 = nordicBlue  (default)
//   1 = flame       (ANGRY -- managed by emotion system + web UI)
//   2 = hypnoRed    (CONFUSED -- managed by emotion system + web UI)
//   3 = hazel
//   4 = blueFlame1
//   5 = dragon
//   6 = bigBlue
//
// EYE:n selectable range: 0-6
//
// PERSON SENSOR: stock chrismiller behavior -- always active, eyes always
// track the largest detected face. autoMove resumes when no face is present.

static constexpr uint32_t FACE_LOST_TIMEOUT_MS =  5000;
static constexpr uint32_t FACE_COOLDOWN_MS      = 30000;
static constexpr uint32_t SERIAL_BUF_SIZE       =    32;

// ANGRY eye swap: flame (index 1) held for this duration then auto-reverts
static constexpr uint32_t ANGRY_EYE_DURATION_MS   = 9000;
// CONFUSED eye swap: hypnoRed (index 2) held for this duration then auto-reverts
static constexpr uint32_t CONFUSED_EYE_DURATION_MS = 7000;

// Eye definition indices (matches eyeDefinitions array in config.h)
static constexpr uint32_t EYE_IDX_DEFAULT      = 0; // nordicBlue
static constexpr uint32_t EYE_IDX_ANGRY        = 1; // flame       (emotion swap + web UI)
static constexpr uint32_t EYE_IDX_CONFUSED     = 2; // hypnoRed    (emotion swap + web UI)
static constexpr uint32_t EYE_IDX_HAZEL        = 3; // web UI
static constexpr uint32_t EYE_IDX_BLUEFLAME1   = 4; // web UI
static constexpr uint32_t EYE_IDX_DRAGON       = 5; // web UI
static constexpr uint32_t EYE_IDX_BIGBLUE      = 6; // web UI
static constexpr uint32_t EYE_IDX_COUNT        = 7; // total entries in eyeDefinitions

// ---------------------------------------------------------------------------
// EMOTION -> EYE PARAMETER MAPPING
// ---------------------------------------------------------------------------

struct EmotionParams {
  float    pupilRatio;
  bool     doBlink;
  uint32_t maxGazeMs;
};

enum EmotionID { NEUTRAL=0, HAPPY, CURIOUS, ANGRY, SLEEPY, SURPRISED, SAD, CONFUSED, EMOTION_COUNT };

static const EmotionParams emotionTable[EMOTION_COUNT] = {
  { 0.40f, false, 3000 }, // NEUTRAL
  { 0.75f, true,  1500 }, // HAPPY
  { 0.60f, false, 4000 }, // CURIOUS
  { 0.15f, false,  800 }, // ANGRY
  { 0.85f, true,  5000 }, // SLEEPY
  { 0.95f, true,   600 }, // SURPRISED
  { 0.25f, true,  4000 }, // SAD
  { 0.70f, true,  2000 }, // CONFUSED
};

// ---------------------------------------------------------------------------
// STATE
// ---------------------------------------------------------------------------

// userDefaultEye tracks the web UI selection -- the eye to revert to after
// emotion eye swaps end. Starts at nordicBlue, updated by EYE:n command.
static uint32_t userDefaultEye{EYE_IDX_DEFAULT};
static uint32_t defIndex{EYE_IDX_DEFAULT};

LightSensor  lightSensor(LIGHT_PIN);
PersonSensor personSensor(Wire);
bool         personSensorFound = USE_PERSON_SENSOR;

static bool     faceWasPresent  = false;
static uint32_t lastFace1SentMs = 0;

static char    serialBuf[SERIAL_BUF_SIZE];
static uint8_t serialBufLen = 0;

// Angry eye revert timer
static bool     angryEyeActive  = false;
static uint32_t angryEyeStartMs = 0;

// Confused eye revert timer
static bool     confusedEyeActive  = false;
static uint32_t confusedEyeStartMs = 0;

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
  if (strcmp(name, "CONFUSED")  == 0) return CONFUSED;
  return NEUTRAL;
}

static void applyEmotion(EmotionID id) {
  const EmotionParams &p = emotionTable[id];
  eyes->setTargetPupil(p.pupilRatio, 300);
  eyes->setMaxGazeMs(p.maxGazeMs);
  if (p.doBlink) eyes->blink();

  if (id == ANGRY) {
    setEyeDefinition(EYE_IDX_ANGRY);
    angryEyeActive    = true;
    angryEyeStartMs   = millis();
    confusedEyeActive = false;
  } else if (id == CONFUSED) {
    setEyeDefinition(EYE_IDX_CONFUSED);
    confusedEyeActive  = true;
    confusedEyeStartMs = millis();
    angryEyeActive     = false;
  } else {
    if (angryEyeActive || confusedEyeActive) {
      setEyeDefinition(userDefaultEye);
      angryEyeActive    = false;
      confusedEyeActive = false;
    }
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

        } else if (strncmp(serialBuf, "EYE:", 4) == 0) {
          uint32_t idx = (uint32_t)atoi(serialBuf + 4);
          if (idx < EYE_IDX_COUNT) {
            userDefaultEye = idx;
            if (!angryEyeActive && !confusedEyeActive) {
              setEyeDefinition(idx);
            }
            Serial.print("[DBG] EYE cmd: switched default to index ");
            Serial.println(idx);
          } else {
            Serial.print("[DBG] EYE cmd: invalid index ");
            Serial.println(idx);
          }

        } else if (strcmp(serialBuf, "EYES:SLEEP") == 0) {
          if (!eyesSleeping) {
            eyesSleeping      = true;
            angryEyeActive    = false;
            confusedEyeActive = false;
            // Disable changed-areas-only so the sleep renderer always sends full
            // frames. With updateChangedAreasOnly(true), fillScreen(black) on an
            // already-black framebuffer marks zero dirty areas, causing the SPI
            // DMA to receive an empty/corrupt region set and lock up the Teensy.
            if (displayLeft)  displayLeft->getDriver()->updateChangedAreasOnly(false);
            if (displayRight) displayRight->getDriver()->updateChangedAreasOnly(false);
            blankDisplays();
            mouthSetSleepIntensity();
            sleepRendererInit();
          }

        } else if (strncmp(serialBuf, "MOUTH:", 6) == 0) {
          uint8_t idx = (uint8_t)atoi(serialBuf + 6);
          mouthShow(idx);
          Serial.print("[DBG] MOUTH cmd: idx=");
          Serial.println(idx);

        } else if (strcmp(serialBuf, "EYES:WAKE") == 0) {
          if (eyesSleeping) {
            eyesSleeping = false;
            // Restore changed-areas-only for efficient eye engine rendering.
            if (displayLeft)  displayLeft->getDriver()->updateChangedAreasOnly(true);
            if (displayRight) displayRight->getDriver()->updateChangedAreasOnly(true);
            mouthRestoreIntensity();
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
  Serial.println("[DBG] Init -- nordicBlue default, flame/ANGRY, hypnoRed/CONFUSED, web eyes 3-7");
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

  mouthInit();
  initEyes(!hasJoystick(), !hasBlinkButton(), !hasLightSensor());
  applyEmotion(NEUTRAL);
  mouthShow(0); // NEUTRAL on boot
}

// ---------------------------------------------------------------------------
// MAIN LOOP
// ---------------------------------------------------------------------------

void loop() {
  processSerial();

  // Person sensor: exact stock chrismiller tracking + IRIS reportFaceState.
  if (hasPersonSensor() && personSensor.read()) {
    int maxSize = 0;
    person_sensor_face_t maxFace{};
    for (int i = 0; i < personSensor.numFacesFound(); i++) {
      const person_sensor_face_t face = personSensor.faceDetails(i);
      if (face.is_facing && face.box_confidence > 60) {
        int size = (face.box_right - face.box_left) * (face.box_bottom - face.box_top);
        if (size > maxSize) { maxSize = size; maxFace = face; }
      }
    }
    reportFaceState(maxSize > 0);
    if (eyesSleeping && maxSize > 0) {
      static uint32_t lastSleepDbg = 0;
      uint32_t _now = millis();
      if (_now - lastSleepDbg > 3000) {
        Serial.println("[SLEEP] face detected - eyesSleeping=true, guard holding");
        lastSleepDbg = _now;
      }
    }
    if (!eyesSleeping) {
      if (maxSize > 0) {
        eyes->setAutoMove(false);
        float targetX = -((static_cast<float>(maxFace.box_left) + static_cast<float>(maxFace.box_right - maxFace.box_left) / 2.0f) / 127.5f - 1.0f);
        float targetY = (static_cast<float>(maxFace.box_top) + static_cast<float>(maxFace.box_bottom - maxFace.box_top) / 3.0f) / 127.5f - 1.0f;
        eyes->setTargetPosition(targetX, targetY);
      } else if (personSensor.timeSinceFaceDetectedMs() > FACE_LOST_TIMEOUT_MS && !eyes->autoMoveEnabled()) {
        eyes->setAutoMove(true);
      }
    }
  }

  // When sleeping: render starfield + snore mouth, skip eye engine
  if (eyesSleeping) {
    renderSleepFrame(displayLeft->getDriver(), displayRight->getDriver());
    mouthSleepFrame();
    return;
  }

  // Angry eye revert: flame -> userDefaultEye after ANGRY_EYE_DURATION_MS
  if (angryEyeActive && (millis() - angryEyeStartMs) >= ANGRY_EYE_DURATION_MS) {
    setEyeDefinition(userDefaultEye);
    angryEyeActive = false;
    Serial.println("[DBG] ANGRY revert -> userDefaultEye");
  }

  // Confused eye revert: hypnoRed -> userDefaultEye after CONFUSED_EYE_DURATION_MS
  if (confusedEyeActive && (millis() - confusedEyeStartMs) >= CONFUSED_EYE_DURATION_MS) {
    setEyeDefinition(userDefaultEye);
    confusedEyeActive = false;
    Serial.println("[DBG] CONFUSED revert -> userDefaultEye");
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

  eyes->renderFrame();
}
