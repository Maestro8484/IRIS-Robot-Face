// mouth.h — MAX7219 8x8 LED matrix mouth driver (bit-bang SPI)
// Pins: DATA=5, CLK=6, CS=7
// 8 mouth shapes indexed 0-7, matching EMOTION order:
//   0=NEUTRAL  1=HAPPY  2=CURIOUS  3=ANGRY
//   4=SLEEPY   5=SURPRISED  6=SAD  7=CONFUSED
// Call mouthInit() in setup(), mouthShow(idx) on MOUTH:x serial command.

#pragma once
#include <Arduino.h>

static constexpr uint8_t MOUTH_DATA_PIN = 5;
static constexpr uint8_t MOUTH_CLK_PIN  = 6;
static constexpr uint8_t MOUTH_CS_PIN   = 7;

// 8 bitmaps × 8 rows. MSB = left column, row 0 = top of matrix.
static const uint8_t MOUTH_BITMAPS[8][8] = {
  // 0: NEUTRAL — flat centre line
  { 0x00, 0x00, 0x00, 0x7E, 0x00, 0x00, 0x00, 0x00 },
  // 1: HAPPY — smile (corners up, middle dips)
  { 0x00, 0x00, 0x42, 0x24, 0x18, 0x00, 0x00, 0x00 },
  // 2: CURIOUS — smirk (left corner raised)
  { 0x00, 0x00, 0x20, 0x5C, 0x00, 0x00, 0x00, 0x00 },
  // 3: ANGRY — frown (corners down)
  { 0x00, 0x18, 0x24, 0x42, 0x00, 0x00, 0x00, 0x00 },
  // 4: SLEEPY — narrow drooping open
  { 0x00, 0x00, 0x00, 0x3C, 0x42, 0x00, 0x00, 0x00 },
  // 5: SURPRISED — open O
  { 0x00, 0x3C, 0x42, 0x42, 0x42, 0x3C, 0x00, 0x00 },
  // 6: SAD — soft frown, slight open
  { 0x00, 0x18, 0x24, 0x42, 0x42, 0x00, 0x00, 0x00 },
  // 7: CONFUSED — wavy/asymmetric
  { 0x00, 0x00, 0x02, 0x1C, 0x20, 0x40, 0x00, 0x00 },
};

static inline void _max7219_write(uint8_t reg, uint8_t data) {
  digitalWrite(MOUTH_CS_PIN, LOW);
  for (int i = 7; i >= 0; i--) {
    digitalWrite(MOUTH_CLK_PIN, LOW);
    digitalWrite(MOUTH_DATA_PIN, (reg  >> i) & 1 ? HIGH : LOW);
    digitalWrite(MOUTH_CLK_PIN, HIGH);
  }
  for (int i = 7; i >= 0; i--) {
    digitalWrite(MOUTH_CLK_PIN, LOW);
    digitalWrite(MOUTH_DATA_PIN, (data >> i) & 1 ? HIGH : LOW);
    digitalWrite(MOUTH_CLK_PIN, HIGH);
  }
  digitalWrite(MOUTH_CS_PIN, HIGH);
}

inline void mouthInit() {
  pinMode(MOUTH_DATA_PIN, OUTPUT);
  pinMode(MOUTH_CLK_PIN,  OUTPUT);
  pinMode(MOUTH_CS_PIN,   OUTPUT);
  digitalWrite(MOUTH_CS_PIN, HIGH);
  _max7219_write(0x0F, 0x00); // display-test off
  _max7219_write(0x09, 0x00); // no BCD decode
  _max7219_write(0x0A, 0x08); // intensity 8/15
  _max7219_write(0x0B, 0x07); // scan limit: all 8 rows
  _max7219_write(0x0C, 0x01); // shutdown off (normal operation)
  for (uint8_t r = 1; r <= 8; r++) _max7219_write(r, 0x00); // clear
}

inline void mouthShow(uint8_t idx) {
  if (idx >= 8) idx = 0;
  for (uint8_t r = 0; r < 8; r++) {
    _max7219_write(r + 1, MOUTH_BITMAPS[idx][r]);
  }
}
