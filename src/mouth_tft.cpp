// mouth_tft.cpp — ILI9341 2.8" TFT mouth driver (Arduino_GFX SWSPI, Teensy 4.1)
// Bit-bang SPI on pins 35/37/36 — no hardware SPI, no DMA, no collision with GC9A01A_t3n.
// Pins: MOSI=35, SCK=37, CS=36, DC=8, RST=4, BL=14

#include "mouth_tft.h"
#include <Arduino_GFX_Library.h>

static constexpr uint8_t MOUTH_TFT_CS   = 36;
static constexpr uint8_t MOUTH_TFT_DC   =  8;
static constexpr uint8_t MOUTH_TFT_RST  =  4;
static constexpr uint8_t MOUTH_TFT_MOSI = 35;
static constexpr uint8_t MOUTH_TFT_SCK  = 37;
static constexpr uint8_t MOUTH_TFT_BL   = 14;

// ── Colors (RGB565) matching assistant.py emotion palette ────────────────────
static constexpr uint16_t MTFT_BLACK   = 0x0000;
static constexpr uint16_t MTFT_CYAN    = 0x07FF;  // NEUTRAL, CURIOUS
static constexpr uint16_t MTFT_YELLOW  = 0xFFE0;  // HAPPY
static constexpr uint16_t MTFT_RED     = 0xF800;  // ANGRY
static constexpr uint16_t MTFT_PURPLE  = 0x780F;  // SLEEPY
static constexpr uint16_t MTFT_WHITE   = 0xFFFF;  // SURPRISED
static constexpr uint16_t MTFT_BLUE    = 0x001F;  // SAD
static constexpr uint16_t MTFT_MAGENTA = 0xF81F;  // CONFUSED
static constexpr uint16_t MTFT_BLUSH   = 0xFBCC;  // HAPPY cheek blush (light pink)

static Arduino_DataBus *_bus = nullptr;
static Arduino_GFX     *_tft = nullptr;

// ── Draw primitives ───────────────────────────────────────────────────────────

// Thick arc: center (cx,cy), radius r, angles a0..a1 radians.
// Screen-coord angles: 0=right, PI/2=down, PI=left, 3PI/2=up.
// Stroke via fillRect at each parametric step (~1px apart).
static void _arc(int16_t cx, int16_t cy, int16_t r,
                 float a0, float a1, uint16_t color, int16_t t) {
    float step = (r > 0) ? (1.0f / r) : 0.02f;
    for (float a = a0; a <= a1; a += step) {
        int16_t x = cx + (int16_t)(r * cosf(a));
        int16_t y = cy + (int16_t)(r * sinf(a));
        _tft->fillRect(x - t / 2, y - t / 2, t, t, color);
    }
}

// Thick quadratic bezier from P0→control→P2
static void _bezier(int16_t x0, int16_t y0, int16_t xc, int16_t yc,
                    int16_t x2, int16_t y2, uint16_t color, int16_t t) {
    for (float f = 0.0f; f <= 1.0f; f += 0.004f) {
        float m = 1.0f - f;
        int16_t x = (int16_t)(m * m * x0 + 2.0f * m * f * xc + f * f * x2);
        int16_t y = (int16_t)(m * m * y0 + 2.0f * m * f * yc + f * f * y2);
        _tft->fillRect(x - t / 2, y - t / 2, t, t, color);
    }
}

// Thick sine wave with optional linear downward drift
static void _sine(int16_t x0, int16_t x1, int16_t cy,
                  float amp, float freq, float drift_per_px,
                  uint16_t color, int16_t t) {
    for (int16_t x = x0; x <= x1; x++) {
        float dx  = (float)(x - x0);
        int16_t y = (int16_t)(cy + dx * drift_per_px + amp * sinf(freq * dx));
        _tft->fillRect(x - t / 2, y - t / 2, t, t, color);
    }
}

// Draw a single 'Z' character as three line segments (for SLEEPY ZZZ)
// top-left corner (tx, ty), width w, height h
static void _draw_Z(int16_t tx, int16_t ty, int16_t w, int16_t h, uint16_t color) {
    int16_t t = 4;  // stroke width
    // top horizontal
    _tft->fillRect(tx, ty, w, t, color);
    // diagonal (approximate with a bezier/line scan)
    int16_t steps = w + h;
    for (int16_t i = 0; i <= steps; i++) {
        int16_t x = tx + w - (int16_t)((float)i / steps * w);
        int16_t y = ty + (int16_t)((float)i / steps * h);
        _tft->fillRect(x - t / 2, y - t / 2, t, t, color);
    }
    // bottom horizontal
    _tft->fillRect(tx, ty + h - t, w, t, color);
}

// ── Expression draw functions ─────────────────────────────────────────────────

// 0: NEUTRAL — very shallow upward curve (near-flat), cyan
static void _draw_neutral() {
    _arc(160, -600, 730, 1.35f, 1.79f, MTFT_CYAN, 10);
}

// 1: HAPPY — large smile arc + cheek blush circles, yellow/pink
static void _draw_happy() {
    _arc(160, 20, 130, 0.50f, 2.64f, MTFT_YELLOW, 12);
    _tft->fillCircle(60,  155, 22, MTFT_BLUSH);
    _tft->fillCircle(260, 155, 22, MTFT_BLUSH);
}

// 2: CURIOUS — asymmetric smirk (flat left, rises right), cyan
static void _draw_curious() {
    _bezier(40, 135, 160, 145, 285, 95, MTFT_CYAN, 10);
}

// 3: ANGRY — downward frown arc, red
static void _draw_angry() {
    _arc(160, 220, 120, 3.77f, 5.65f, MTFT_RED, 12);
}

// 4: SLEEPY — drooping sine wave with downward drift + ZZZ glyphs, purple
static void _draw_sleepy() {
    _sine(30, 290, 105, 18.0f, 0.030f, 0.10f, MTFT_PURPLE, 10);
    _draw_Z(200, 20, 24, 20, MTFT_PURPLE);  // large Z
    _draw_Z(228, 30, 18, 15, MTFT_PURPLE);  // medium Z
    _draw_Z(250, 38, 14, 11, MTFT_PURPLE);  // small Z
}

// 5: SURPRISED — thick hollow oval, white
static void _draw_surprised() {
    const int16_t cx = 160, cy = 120, rx = 58, ry = 48, t = 12;
    for (float a = 0.0f; a < 6.2832f; a += 0.020f) {
        int16_t x = cx + (int16_t)(rx * cosf(a));
        int16_t y = cy + (int16_t)(ry * sinf(a));
        _tft->fillRect(x - t / 2, y - t / 2, t, t, MTFT_WHITE);
    }
}

// 6: SAD — deep frown arc + vertical quiver lines, blue
static void _draw_sad() {
    _arc(160, 200, 145, 3.87f, 5.55f, MTFT_BLUE, 12);
    for (int8_t i = 0; i < 5; i++) {
        int16_t x = 120 + i * 20;
        _tft->drawFastVLine(x,     148, 18, MTFT_BLUE);
        _tft->drawFastVLine(x + 2, 151, 13, MTFT_BLUE);
    }
}

// 7: CONFUSED — squiggly multi-period sine wave (~2.7 cycles), magenta
static void _draw_confused() {
    _sine(30, 290, 120, 28.0f, 0.065f, 0.0f, MTFT_MAGENTA, 10);
}

// 8: SLEEP/OFF — black screen only (cleared by mouthTFTShow before switch)
static void _draw_sleep() {}

// ── Public API ────────────────────────────────────────────────────────────────

void mouthTFTInit() {
    _bus = new Arduino_SWSPI(MOUTH_TFT_DC, MOUTH_TFT_CS,
                              MOUTH_TFT_SCK, MOUTH_TFT_MOSI, -1);
    _tft = new Arduino_ILI9341(_bus, MOUTH_TFT_RST, 3);
    _tft->begin();
    _tft->fillScreen(0x0000);
    pinMode(MOUTH_TFT_BL, OUTPUT);
    analogWrite(MOUTH_TFT_BL, 220);
}

void mouthTFTShow(uint8_t idx) {
    if (!_tft) return;
    if (idx > 8) idx = 0;
    _tft->fillScreen(MTFT_BLACK);
    switch (idx) {
        case 0: _draw_neutral();   break;
        case 1: _draw_happy();     break;
        case 2: _draw_curious();   break;
        case 3: _draw_angry();     break;
        case 4: _draw_sleepy();    break;
        case 5: _draw_surprised(); break;
        case 6: _draw_sad();       break;
        case 7: _draw_confused();  break;
        case 8: _draw_sleep();     break;
    }
}

// Intensity / backlight control — BL on pin 14, PWM via analogWrite
void mouthSetSleepIntensity() {
    if (!_tft) return;
    _tft->fillScreen(MTFT_BLACK);
    analogWrite(MOUTH_TFT_BL, 8);  // mouthSleepFrame breathes from here
}

void mouthRestoreIntensity() {
    if (!_tft) return;
    analogWrite(MOUTH_TFT_BL, 220);  // restore normal brightness
}

void mouthSetIntensity(uint8_t level) {
    if (!_tft) return;
    analogWrite(MOUTH_TFT_BL, (uint16_t)level * 17);
}

// Sleep animation state — file-scope so mouthSleepReset() can zero it
static uint32_t _sleepFrameCount = 0;

void mouthSleepReset() {
    _sleepFrameCount = 0;
}

void mouthSleepFrame() {
    if (!_tft) return;

    // Erase previous frame with targeted fillRect (avoids full-screen flicker at dim BL)
    _tft->fillRect(25, 88, 270, 62, MTFT_BLACK);   // sine band
    _tft->fillRect(110, 5, 100, 95, MTFT_BLACK);   // Z drift zone

    // Backlight: breathe 8→22→8 starting at floor (center=15, amp=7)
    float bl_f = -cosf(2.0f * M_PI * (float)_sleepFrameCount / 120.0f);
    analogWrite(MOUTH_TFT_BL, (uint8_t)(15.0f + 7.0f * bl_f));

    // Sine: cy oscillates ±10px around 115, amp=8, freq=0.028, stroke=5
    int16_t cy = 115 + (int16_t)(10.0f * sinf(2.0f * M_PI * (float)_sleepFrameCount / 200.0f));
    _sine(30, 290, cy, 8.0f, 0.028f, 0.0f, MTFT_PURPLE, 5);

    // Z: drifts upward over 60 frames, repeats every 150 frames
    uint32_t zp = _sleepFrameCount % 150;
    if (zp < 60) {
        int16_t ty = 68 - (int16_t)zp;
        uint16_t zcolor = (zp < 15 || zp > 45) ? (uint16_t)0x3806 : MTFT_PURPLE;
        _draw_Z(142, ty, 36, 30, zcolor);
    }

    _sleepFrameCount++;
}
