// Define if you wish to debug memory usage.  Only works on T4.x
//#define DEBUG_MEMORY

#include <SPI.h>
#include <array>
#include <Wire.h>
#include <Entropy.h>

#include "config.h"
#include "mouth_tft.h"
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
//   1 = flame          (ANGRY -- managed by emotion system + web UI)
//   2 = hypnoRed       (CONFUSED -- managed by emotion system + web UI)
//   3 = hazel
//   4 = blueFlame1
//   5 = dragon
//   6 = strikingBlue   (bigBlue removed)
//
// EYE:n selectable range: 0-6
//
// PERSON SENSOR: stock chrismiller behavior -- always active, eyes always
// track the largest detected face. autoMove resumes when no face is present.

static constexpr uint32_t FACE_LOST_TIMEOUT_MS =  5000;
static constexpr uint32_t FACE_COOLDOWN_MS      = 30000;
static constexpr uint32_t SERIAL_BUF_SIZE       =    40;  // SLEEP_CFG:mouthPulseAlpha=255 = 29 chars

// ANGRY eye swap: flame (index 1) held for this duration then auto-reverts
static constexpr uint32_t ANGRY_EYE_DURATION_MS   = 9000;
// CONFUSED eye swap: hypnoRed (index 2) held for this duration then auto-reverts
static constexpr uint32_t CONFUSED_EYE_DURATION_MS = 7000;

// Eye definition indices (matches eyeDefinitions array in config.h)
static constexpr uint32_t EYE_IDX_DEFAULT      = 0; // nordicBlue
static constexpr uint32_t EYE_IDX_ANGRY        = 1; // flame        (emotion swap + web UI)
static constexpr uint32_t EYE_IDX_CONFUSED     = 2; // hypnoRed     (emotion swap + web UI)
static constexpr uint32_t EYE_IDX_HAZEL        = 3; // web UI
static constexpr uint32_t EYE_IDX_BLUEFLAME1   = 4; // web UI
static constexpr uint32_t EYE_IDX_DRAGON       = 5; // web UI
static constexpr uint32_t EYE_IDX_STRIKINGBLUE = 6; // web UI (was 7; bigBlue removed)
static constexpr uint32_t EYE_IDX_COUNT        = 7; // total entries in eyeDefinitions

// ---------------------------------------------------------------------------
// EMOTION -> EYE PARAMETER MAPPING
// ---------------------------------------------------------------------------

struct EmotionParams {
  float    pupilRatio;
  bool     doBlink;
  uint32_t maxGazeMs;
};

enum EmotionID { NEUTRAL=0, HAPPY, CURIOUS, ANGRY, SLEEPY, SURPRISED, SAD, CONFUSED, AMUSED, EMOTION_COUNT };

static const EmotionParams emotionTable[EMOTION_COUNT] = {
  { 0.40f, false, 3000 }, // NEUTRAL
  { 0.75f, true,  1500 }, // HAPPY
  { 0.60f, false, 4000 }, // CURIOUS
  { 0.15f, false,  800 }, // ANGRY
  { 0.85f, true,  5000 }, // SLEEPY
  { 0.95f, true,   600 }, // SURPRISED
  { 0.25f, true,  4000 }, // SAD
  { 0.70f, true,  2000 }, // CONFUSED
  { 0.55f, false, 3000 }, // AMUSED
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

// Eyes speaking state: when true, Person Sensor position updates are suppressed
// and autoMove is active, giving smooth wandering during TTS instead of jitter.
static bool     eyesSpeaking = false;

// Mouth sleep frame throttle — min interval between frames to prevent flicker
static uint32_t srMouthLastMs = 0;
static constexpr uint32_t MOUTH_SLEEP_FRAME_MS = 60;

// Idle animation auto-start: trigger after this many ms of no serial commands
static uint32_t lastCommandMs = 0;
static constexpr uint32_t IDLE_AUTO_MS = 120000UL; // 2 min inactivity

// Decouple mouth TFT (blocking SWSPI) from the eye render loop.
// MOUTH: commands queue here; rendered after eyes->renderFrame(), rate-limited
// so TTS mouth animation never stalls the eye loop.
static uint8_t  pendingMouthIdx    = 0;
static bool     mouthUpdatePending = false;
static uint32_t lastMouthRenderMs  = 0;
static constexpr uint32_t MOUTH_RENDER_MIN_MS = 75;

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
  if (strcmp(name, "AMUSED")    == 0) return AMUSED;
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
          mouthIdleStop();
          lastCommandMs = millis();
          EmotionID id = parseEmotion(serialBuf + 8);
          Serial.print("[DBG] EMOTION cmd: ");
          Serial.print(serialBuf + 8);
          Serial.print(" -> id=");
          Serial.println(id);
          applyEmotion(id);

        } else if (strncmp(serialBuf, "EYE:", 4) == 0) {
          lastCommandMs = millis();
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
          mouthIdleStop();
          lastCommandMs = millis();
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
            // blankDisplays() drains any pending eye-engine DMA before the starfield
            // renderer takes over. Skipping it risks a DMA race on the first fillScreen.
            blankDisplays();
            mouthSetSleepIntensity();
            sleepRendererInit();
            Serial.println("[DBG] EYES:SLEEP -- starfield starting");
          }

        } else if (strncmp(serialBuf, "MOUTH:", 6) == 0) {
          mouthIdleStop();
          lastCommandMs      = millis();
          pendingMouthIdx    = (uint8_t)atoi(serialBuf + 6);
          mouthUpdatePending = true;

        } else if (strncmp(serialBuf, "MOUTH_INTENSITY:", 16) == 0) {
          mouthIdleStop();
          lastCommandMs = millis();
          uint8_t lvl = (uint8_t)constrain(atoi(serialBuf + 16), 0, 15);
          mouthSetIntensity(lvl);
          Serial.print("[DBG] MOUTH_INTENSITY: ");
          Serial.println(lvl);

        } else if (strcmp(serialBuf, "EYES:WAKE") == 0) {
          mouthIdleStop();
          lastCommandMs = millis();
          if (eyesSleeping) {
            eyesSleeping = false;
            // Restore changed-areas-only for efficient eye engine rendering.
            if (displayLeft)  displayLeft->getDriver()->updateChangedAreasOnly(true);
            if (displayRight) displayRight->getDriver()->updateChangedAreasOnly(true);
            mouthSleepReset();
            mouthRestoreIntensity();
            uint32_t saved = defIndex;
            defIndex = UINT32_MAX;
            setEyeDefinition(saved);
            applyEmotion(NEUTRAL);
            Serial.println("[DBG] EYES:WAKE -- displays restored");
          }

        } else if (strcmp(serialBuf, "EYES:SPEAKING") == 0) {
          lastCommandMs = millis();
          eyesSpeaking  = true;
          Serial.println("[DBG] EYES:SPEAKING -- tracking frozen at last position");

        } else if (strcmp(serialBuf, "EYES:SPEAKING:STOP") == 0) {
          lastCommandMs = millis();
          eyesSpeaking  = false;
          Serial.println("[DBG] EYES:SPEAKING:STOP -- tracking resumed");

        } else if (strcmp(serialBuf, "VERSION") == 0) {
          Serial.print("[VER] IRIS-EYES firmware=");
          Serial.print(FIRMWARE_VERSION);
          Serial.print(" built=");
          Serial.println(__DATE__);

        } else if (strcmp(serialBuf, "IDLE:START") == 0) {
          lastCommandMs = 0; // force auto-start timer to treat this as immediate
          mouthIdleStart();
          Serial.println("[DBG] IDLE:START");

        } else if (strcmp(serialBuf, "IDLE:STOP") == 0) {
          mouthIdleStop();
          lastCommandMs = millis();
          Serial.println("[DBG] IDLE:STOP");

        } else if (strncmp(serialBuf, "SLEEP_CFG:", 10) == 0) {
          char* eq = strchr(serialBuf + 10, '=');
          if (eq) {
            *eq = '\0';
            const char* key = serialBuf + 10;
            float val = atof(eq + 1);
            if      (strcmp(key, "speed")          == 0) sleepCfg.speed          = val;
            else if (strcmp(key, "starBrightMin")  == 0) sleepCfg.starBrightMin  = (uint8_t)val;
            else if (strcmp(key, "starBrightMax")  == 0) sleepCfg.starBrightMax  = (uint8_t)val;
            else if (strcmp(key, "starTwinkleAmp") == 0) sleepCfg.starTwinkleAmp = (uint8_t)val;
            else if (strcmp(key, "shootCount")     == 0) sleepCfg.shootCount     = (uint8_t)val;
            else if (strcmp(key, "shootSpeed")     == 0) sleepCfg.shootSpeed     = (uint8_t)val;
            else if (strcmp(key, "shootLen")       == 0) sleepCfg.shootLen       = (uint8_t)val;
            else if (strcmp(key, "shootBright")    == 0) sleepCfg.shootBright    = (uint8_t)val;
            else if (strcmp(key, "warpCount")      == 0) sleepCfg.warpCount      = (uint8_t)val;
            else if (strcmp(key, "warpSpeed")      == 0) sleepCfg.warpSpeed      = (uint8_t)val;
            else if (strcmp(key, "warpBright")     == 0) sleepCfg.warpBright     = (uint8_t)val;
            else if (strcmp(key, "moonR")          == 0) sleepCfg.moonR          = (uint8_t)val;
            else if (strcmp(key, "moonDrift")      == 0) sleepCfg.moonDrift      = (uint8_t)val;
            else if (strcmp(key, "saturnR")        == 0) sleepCfg.saturnR        = (uint8_t)val;
            else if (strcmp(key, "saturnDrift")    == 0) sleepCfg.saturnDrift    = (uint8_t)val;
            else if (strcmp(key, "nebulaAlpha")    == 0) sleepCfg.nebulaAlpha    = (uint8_t)val;
            else if (strcmp(key, "waveAmp0")       == 0) sleepCfg.waveAmp0       = (uint8_t)val;
            else if (strcmp(key, "waveAmp1")       == 0) sleepCfg.waveAmp1       = (uint8_t)val;
            else if (strcmp(key, "waveAmp2")       == 0) sleepCfg.waveAmp2       = (uint8_t)val;
            else if (strcmp(key, "waveOscAmp")     == 0) sleepCfg.waveOscAmp     = (uint8_t)val;
            else if (strcmp(key,"mouthPulseAlpha") == 0) sleepCfg.mouthPulseAlpha= (uint8_t)val;
            else if (strcmp(key, "zzzAlpha0")      == 0) sleepCfg.zzzAlpha0      = (uint8_t)val;
            else if (strcmp(key, "zzzAlpha1")      == 0) sleepCfg.zzzAlpha1      = (uint8_t)val;
            else if (strcmp(key, "zzzAlpha2")      == 0) sleepCfg.zzzAlpha2      = (uint8_t)val;
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
      // RD-030 #3: greet the arriving person (no-op unless the idle engine owns the
      // mouth, i.e. IRIS has been at rest — so it never interrupts a conversation).
      mouthGreet();
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
  Serial.print("[VER] IRIS-EYES firmware=");
  Serial.print(FIRMWARE_VERSION);
  Serial.print(" built=");
  Serial.println(__DATE__);
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
    // Pi4 holds port open → Serial wait above skips; guarantee ≥1500ms from power-on before I2C probe.
    while (millis() < 1500);
    Wire.begin();
    personSensorFound = false;
    for (int attempt = 0; attempt < 5; attempt++) {
      if (personSensor.isPresent()) { personSensorFound = true; break; }
      delay(100);
    }
    if (personSensorFound) {
      Serial.println("[DBG] Person Sensor detected");
      personSensor.enableID(false);
      personSensor.setMode(PersonSensor::Mode::Continuous);
      delay(200); // settle, then disable LED
      personSensor.enableLED(false);
    } else {
      Serial.println("[DBG] No Person Sensor found");
    }
  }

  mouthTFTInit();
  initEyes(!hasJoystick(), !hasBlinkButton(), !hasLightSensor());
  applyEmotion(NEUTRAL);
  mouthTFTShow(0); // NEUTRAL on boot
}

// ---------------------------------------------------------------------------
// MAIN LOOP
// ---------------------------------------------------------------------------

void loop() {
  processSerial();

  // Person sensor: skip during sleep to avoid I2C activity during heavy SPI load.
  if (!eyesSleeping && hasPersonSensor() && personSensor.read()) {
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
    if (!eyesSpeaking) {
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

  // When sleeping: render starfield on eyes + animate mouth, skip eye engine.
  // renderSleepFrame() is self-throttled to SR_FRAME_MS (150ms).
  // mouthSleepFrame() runs on iterations where eye renderer skips (the ~140ms
  // gaps between eye frames). When eye renderer fires it blocks ~114ms on
  // updateScreen() — mouth skips that iteration. This gives mouth ~10 calls/sec.
  if (eyesSleeping) {
    uint32_t nowMs2 = millis();
    bool eyeWillRender = (nowMs2 - srLastFrameMs >= SR_FRAME_MS);
    renderSleepFrame(displayLeft->getDriver(), displayRight->getDriver());
    if (!eyeWillRender && (nowMs2 - srMouthLastMs >= MOUTH_SLEEP_FRAME_MS)) {
      mouthSleepFrame();
      srMouthLastMs = nowMs2;
    }
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

  if (mouthUpdatePending) {
    uint32_t nowMs = millis();
    if (nowMs - lastMouthRenderMs >= MOUTH_RENDER_MIN_MS) {
      mouthTFTShow(pendingMouthIdx);
      mouthUpdatePending = false;
      lastMouthRenderMs  = nowMs;
    }
  }

  // Auto-start idle after IDLE_AUTO_MS of no serial commands
  uint32_t nowLoop = millis();
  if (!mouthIdleIsActive() && (nowLoop - lastCommandMs) >= IDLE_AUTO_MS) {
    mouthIdleStart();
    mouthApplyIdleTint(); // RD-030 #2: settle into the emotion-tinted resting face
  }
  mouthIdleTick(nowLoop);
}
