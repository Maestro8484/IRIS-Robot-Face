// mouth.h — MAX7219 32x8 LED matrix mouth driver (bit-bang SPI)
// 4 chained MAX7219 modules. Header end = chip3 in array (physically leftmost).
// Chain is reversed: chip0 = physically rightmost panel.
// Physical row 0 = BOTTOM of display, so bitmaps are sent in reverse row order.
// Pins: DATA=5, CLK=6, CS=7
//
// Expression index:
//   0=NEUTRAL  1=HAPPY  2=CURIOUS  3=ANGRY
//   4=SLEEPY   5=SURPRISED  6=SAD  7=CONFUSED  8=SLEEP/OFF
//
// delayMicroseconds(2) on clock edges reduces bit-bang EMI into audio.

#pragma once
#include <Arduino.h>

static constexpr uint8_t MOUTH_DATA_PIN  = 5;
static constexpr uint8_t MOUTH_CLK_PIN   = 6;
static constexpr uint8_t MOUTH_CS_PIN    = 7;
static constexpr uint8_t MOUTH_NUM_CHIPS = 4;

// ---------------------------------------------------------------------------
// BITMAPS  [9 expressions][8 rows][4 chips]
// Row 0 = top of intended display output (sent to physical bottom row first).
// chip0..chip3 = left to right on physical display.
// MSB of each byte = leftmost column of that chip.
// ---------------------------------------------------------------------------

static const uint8_t MOUTH_BITMAPS[9][8][4] = {

  // 0: NEUTRAL — solid 2-row line across full width
  {
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0xFF, 0xFF, 0xFF, 0xFF },
    { 0xFF, 0xFF, 0xFF, 0xFF },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
  },

  // 1: HAPPY — arc, corners rise to top, center stays low
  {
    { 0xF0, 0x00, 0x00, 0x0F },
    { 0x0C, 0x00, 0x00, 0x30 },
    { 0x03, 0x00, 0x00, 0xC0 },
    { 0x00, 0xC0, 0x03, 0x00 },
    { 0x00, 0x30, 0x0C, 0x00 },
    { 0x00, 0x0C, 0x30, 0x00 },
    { 0x00, 0x03, 0xC0, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
  },

  // 2: CURIOUS — diagonal smirk, left high, right low
  {
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0xFF, 0x00, 0x00, 0x00 },
    { 0x00, 0xFF, 0x00, 0x00 },
    { 0x00, 0x00, 0xFF, 0x00 },
    { 0x00, 0x00, 0x00, 0xFF },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
  },

  // 3: ANGRY — frown, corners drop to bottom
  {
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x03, 0xC0, 0x00 },
    { 0x00, 0x0C, 0x30, 0x00 },
    { 0x00, 0x30, 0x0C, 0x00 },
    { 0x00, 0xC0, 0x03, 0x00 },
    { 0x03, 0x00, 0x00, 0xC0 },
    { 0x0C, 0x00, 0x00, 0x30 },
    { 0xF0, 0x00, 0x00, 0x0F },
  },

  // 4: SLEEPY — flat left, droops down on right
  {
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0xFF, 0xFF, 0x00, 0x00 },
    { 0xFF, 0xFF, 0xFF, 0x00 },
    { 0x00, 0x00, 0xFF, 0xFF },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
  },

  // 5: SURPRISED — hollow oval centered on chips 1+2
  {
    { 0x00, 0xFF, 0xFF, 0x00 },
    { 0x00, 0x80, 0x01, 0x00 },
    { 0x00, 0x80, 0x01, 0x00 },
    { 0x00, 0x80, 0x01, 0x00 },
    { 0x00, 0x80, 0x01, 0x00 },
    { 0x00, 0x80, 0x01, 0x00 },
    { 0x00, 0x80, 0x01, 0x00 },
    { 0x00, 0xFF, 0xFF, 0x00 },
  },

  // 6: SAD — center high, outer edges droop to bottom corners
  {
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x3C, 0x3C, 0x00 },
    { 0x00, 0xC3, 0xC3, 0x00 },
    { 0x03, 0x00, 0x00, 0xC0 },
    { 0x0C, 0x00, 0x00, 0x30 },
    { 0x30, 0x00, 0x00, 0x0C },
    { 0xC0, 0x00, 0x00, 0x03 },
    { 0x00, 0x00, 0x00, 0x00 },
  },

  // 7: CONFUSED — zigzag line left to right
  {
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0xF0, 0x00, 0x00, 0x00 },
    { 0x0F, 0xF0, 0x00, 0x00 },
    { 0x00, 0x0F, 0xF0, 0x00 },
    { 0x00, 0x00, 0x0F, 0xF0 },
    { 0x00, 0x00, 0x00, 0x0F },
    { 0x00, 0x00, 0x00, 0x00 },
  },

  // 8: SLEEP/OFF — all pixels off
  {
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
    { 0x00, 0x00, 0x00, 0x00 },
  },
};

// ---------------------------------------------------------------------------
// DRIVER
// ---------------------------------------------------------------------------

static inline void _shiftByte(uint8_t b) {
  for (int i = 7; i >= 0; i--) {
    digitalWrite(MOUTH_CLK_PIN, LOW);
    digitalWrite(MOUTH_DATA_PIN, (b >> i) & 1 ? HIGH : LOW);
    delayMicroseconds(2);
    digitalWrite(MOUTH_CLK_PIN, HIGH);
    delayMicroseconds(2);
  }
}

static inline void _writeAll(uint8_t reg, uint8_t data) {
  digitalWrite(MOUTH_CS_PIN, LOW);
  for (uint8_t i = 0; i < MOUTH_NUM_CHIPS; i++) {
    _shiftByte(reg);
    _shiftByte(data);
  }
  digitalWrite(MOUTH_CS_PIN, HIGH);
}

static inline void _writeRow(uint8_t rowReg, const uint8_t data[4]) {
  digitalWrite(MOUTH_CS_PIN, LOW);
  for (uint8_t chip = 0; chip < MOUTH_NUM_CHIPS; chip++) {
    _shiftByte(rowReg);
    _shiftByte(data[chip]);
  }
  digitalWrite(MOUTH_CS_PIN, HIGH);
}

inline void mouthInit() {
  pinMode(MOUTH_DATA_PIN, OUTPUT);
  pinMode(MOUTH_CLK_PIN,  OUTPUT);
  pinMode(MOUTH_CS_PIN,   OUTPUT);
  digitalWrite(MOUTH_CS_PIN,  HIGH);
  digitalWrite(MOUTH_CLK_PIN, LOW);
  delayMicroseconds(10);

  _writeAll(0x0F, 0x00); // display-test OFF
  _writeAll(0x09, 0x00); // BCD decode OFF
  _writeAll(0x0A, 0x05); // intensity 5/15 (~33%) -- matches mouthRestoreIntensity
  _writeAll(0x0B, 0x07); // scan all 8 rows
  _writeAll(0x0C, 0x01); // shutdown OFF

  const uint8_t z[4] = {0, 0, 0, 0};
  for (uint8_t r = 1; r <= 8; r++) _writeRow(r, z);
}

inline void mouthShow(uint8_t idx) {
  if (idx > 8) idx = 0;
  // Send rows in reverse order -- physical row 0 is at bottom of display
  for (uint8_t r = 0; r < 8; r++) {
    _writeRow(r + 1, MOUTH_BITMAPS[idx][7 - r]);
  }
}

// ---------------------------------------------------------------------------
// SLEEP MOUTH — snore breathing animation. Call from loop() when sleeping.
// 12s cycle: inhale (0-4.2s), hold (4.2-7.8s), exhale/snore wave (7.8-12s).
// Call mouthSetSleepIntensity() on EYES:SLEEP, mouthRestoreIntensity() on wake.
// ---------------------------------------------------------------------------

inline void mouthSetSleepIntensity() {
  _writeAll(0x0A, 0x01); // very dim (3/32 duty cycle) for sleep
}

inline void mouthRestoreIntensity() {
  _writeAll(0x0A, 0x05); // normal brightness
}

inline void mouthSleepFrame() {
  uint32_t t = millis() % 12000;
  uint8_t pixels[8][4] = {};

  if (t < 4200) {
    // INHALE: flat line at rows 3-4, brightness ramps up
    float bright = 0.08f + (t / 4200.0f) * 0.55f;
    uint8_t center = (uint8_t)(bright * 255);
    uint8_t mid    = center * 6 / 10;
    uint8_t outer  = center * 3 / 10;
    pixels[3][0] = outer; pixels[3][1] = mid;
    pixels[3][2] = mid;   pixels[3][3] = outer;
    pixels[4][0] = outer * 7 / 10; pixels[4][1] = mid * 7 / 10;
    pixels[4][2] = mid * 7 / 10;   pixels[4][3] = outer * 7 / 10;

  } else if (t < 7800) {
    // HOLD: dim flat line
    pixels[3][0]=0x18; pixels[3][1]=0x3C; pixels[3][2]=0x3C; pixels[3][3]=0x18;
    pixels[4][0]=0x10; pixels[4][1]=0x28; pixels[4][2]=0x28; pixels[4][3]=0x10;

  } else {
    // EXHALE/SNORE: sine wave rolls left to right
    float exT  = (t - 7800) / 4200.0f;
    float phase = exT * 3.14159f * 2.8f;
    for (int c = 0; c < 32; c++) {
      float wave  = sinf(phase + c * 0.45f) * 2.5f;
      int   row   = (int)roundf(3.5f + wave);
      float edge  = 1.0f - fabsf(c - 15.5f) / 15.5f * 0.45f;
      uint8_t br  = (uint8_t)(0.60f * edge * 255);
      int chip = c / 8, bit = 7 - (c % 8);
      if (row >= 0 && row < 8)
        pixels[row][chip] |= (br > 64) ? (1 << bit) : 0;
      int row2 = row + (wave > 0 ? 1 : -1);
      if (row2 >= 0 && row2 < 8)
        pixels[row2][chip] |= (br > 128) ? (1 << bit) : 0;
    }
  }

  for (uint8_t r = 0; r < 8; r++) {
    _writeRow(r + 1, pixels[7 - r]);
  }
}
