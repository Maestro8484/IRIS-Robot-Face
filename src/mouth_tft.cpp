// mouth_tft.cpp — ILI9341 2.8" TFT mouth driver (Arduino_GFX SWSPI, Teensy 4.1)
// Bit-bang SPI on pins 35/37/36 — no hardware SPI, no DMA, no collision with GC9A01A_t3n.
// Pins: MOSI=35, SCK=37, CS=36, DC=8, RST=4, BL=5

#include "mouth_tft.h"
#include "sleep_cfg.h"
#include <Arduino_GFX_Library.h>

static constexpr uint8_t MOUTH_TFT_CS   = 36;
static constexpr uint8_t MOUTH_TFT_DC   =  8;
static constexpr uint8_t MOUTH_TFT_RST  =  4;
static constexpr uint8_t MOUTH_TFT_MOSI = 35;
static constexpr uint8_t MOUTH_TFT_SCK  = 37;
static constexpr uint8_t MOUTH_TFT_BL   =  5;  // GPIO5 — PWM dimming, wired to ILI9341 BL

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
static constexpr uint16_t MTFT_AMBER   = 0xFD20;  // AMUSED — reserved, needs dedicated expression index

// ── Backlight lookup table (logarithmic, level 0-15 → PWM 0-255) ─────────────
// intensity 0=off, 1=barely visible, 8=comfortable idle, 15=full
static const uint8_t BL_MAP[16] = {
    0, 2, 4, 7, 11, 16, 22, 30, 40, 55, 75, 100, 135, 175, 210, 255
};

// ── Backlight + expression state (tracked for idle engine) ───────────────────
static uint8_t _currentBLLevel  = 14; // matches init (BL_MAP[14]=210)
static uint8_t _currentMouthIdx = 0;

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
    analogWrite(MOUTH_TFT_BL, BL_MAP[14]); // level 14 = 210/255
}

void mouthTFTShow(uint8_t idx) {
    if (!_tft) return;
    if (idx > 8) idx = 0;
    _currentMouthIdx = idx;
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

// Intensity / backlight control — BL on pin 5, PWM via BL_MAP lookup
void mouthSetSleepIntensity() {
    if (!_tft) return;
    _tft->fillScreen(MTFT_BLACK);
    analogWrite(MOUTH_TFT_BL, BL_MAP[5]); // level 5 = 16/255 — dim but visible during sleep
}

void mouthRestoreIntensity() {
    if (!_tft) return;
    analogWrite(MOUTH_TFT_BL, BL_MAP[_currentBLLevel]);
}

void mouthSetIntensity(uint8_t level) {
    if (!_tft) return;
    if (level > 15) level = 15;
    _currentBLLevel = level;
    analogWrite(MOUTH_TFT_BL, BL_MAP[level]);
}

// Sleep animation state — file-scope so mouthSleepReset() can zero it
static uint32_t _sleepFrameCount = 0;

void mouthSleepReset() {
    _sleepFrameCount = 0;
}

void mouthSleepFrame() {
    if (!_tft) return;

    // Frame timing reference — slow oscillation period
    float phase = (float)_sleepFrameCount * 0.018f;  // ~0.018 rad/frame

    // ── ZZZ region (top area): clear then draw symmetric pairs ────────────
    // y=4..70 cleared each frame; 3 Z-pairs (large/med/small), left+right.
    _tft->fillRect(0, 4, 320, 67, MTFT_BLACK);

    // ZZZ pair definitions: {xRight, xLeft, baseY, w, h, driftAmp, phaseOffset}
    struct ZPair { int16_t xR, xL, baseY, w, h; float da, ph; };
    static const ZPair ZP[3] = {
        { 246, 38, 44, 34, 28, 11.0f, 0.00f },  // large (outermost)
        { 222, 58, 35, 26, 22,  8.5f, 0.70f },  // medium
        { 202, 78, 27, 20, 17,  6.0f, 1.40f },  // small (innermost)
    };

    // Map zzzAlpha to 3-step color brightness
    auto zCol = [](uint8_t alpha) -> uint16_t {
        if (alpha > 170) return 0x07FF;  // bright cyan
        if (alpha > 120) return 0x0466;  // mid cyan
        return 0x0244;                    // dim cyan
    };
    static const uint8_t* alphaPtr[3] = {
        &sleepCfg.zzzAlpha0, &sleepCfg.zzzAlpha1, &sleepCfg.zzzAlpha2
    };

    for (int i = 0; i < 3; i++) {
        const ZPair& z = ZP[i];
        int16_t drift = (int16_t)(z.da * sinf(phase * 0.38f + z.ph));
        int16_t ty = z.baseY + drift;
        if (ty >= 5 && ty + z.h < 71) {
            uint16_t col = zCol(*alphaPtr[i]);
            _draw_Z(z.xR, ty, z.w, z.h, col);  // right-side Z
            _draw_Z(z.xL, ty, z.w, z.h, col);  // left-side Z (symmetric)
        }
    }

    // ── Waveform band: 3 layered sine waves ───────────────────────────────
    // cy oscillates based on sleepCfg.waveOscAmp; constrained to keep waves in band.
    float oscAmp = (float)sleepCfg.waveOscAmp;
    if (oscAmp > 14.0f) oscAmp = 14.0f;  // SWSPI band constraint
    float oscY = sinf(phase * 0.22f) * oscAmp;

    int16_t cy0 = 116 + (int16_t)oscY;          // primary wave center (blue)
    int16_t cy1 = cy0 - 22;                      // secondary (purple, above)
    int16_t cy2 = cy0 + 20;                      // tertiary (teal, below)

    float amp0 = (float)sleepCfg.waveAmp0;
    float amp1 = (float)sleepCfg.waveAmp1;
    float amp2 = (float)sleepCfg.waveAmp2;

    static constexpr int16_t BAND_Y0 = 76;
    static constexpr int16_t BAND_Y1 = 162;
    static constexpr int16_t S0 = 6;   // primary half-stroke (blue)
    static constexpr int16_t S1 = 4;   // secondary half-stroke (purple)
    static constexpr int16_t S2 = 3;   // tertiary half-stroke (teal)

    // Wave colors: blue / purple / dim teal — matches HTML v8 hues 210/270/185
    static constexpr uint16_t W_BLUE   = 0x001F;  // hue 210 → pure blue
    static constexpr uint16_t W_PURPLE = 0x780F;  // hue 270 → purple
    static constexpr uint16_t W_TEAL   = 0x0318;  // hue 185 → dim teal

    for (int16_t x = 0; x < 320; x++) {
        float dx = (float)x;
        // Each wave: primary + secondary harmonic (0.35× amplitude, 1.7× frequency)
        float ph0 = phase * 0.85f;
        float ph1 = phase * 1.22f;
        float ph2 = phase * 1.70f;
        int16_t sy0 = cy0 + (int16_t)(amp0 * sinf(0.028f * dx + ph0)
                                    + amp0 * 0.35f * sinf(0.028f * 1.7f * dx + ph0 * 1.3f));
        int16_t sy1 = cy1 + (int16_t)(amp1 * sinf(0.031f * dx + ph1 + 0.9f)
                                    + amp1 * 0.35f * sinf(0.031f * 1.7f * dx + ph1 * 1.3f));
        int16_t sy2 = cy2 + (int16_t)(amp2 * sinf(0.052f * dx + ph2 + 1.8f)
                                    + amp2 * 0.35f * sinf(0.052f * 1.7f * dx + ph2 * 1.3f));

        for (int16_t y = BAND_Y0; y <= BAND_Y1; y++) {
            uint16_t col = MTFT_BLACK;
            if      (y >= sy0 - S0 && y <= sy0 + S0) col = W_BLUE;
            else if (y >= sy1 - S1 && y <= sy1 + S1) col = W_PURPLE;
            else if (y >= sy2 - S2 && y <= sy2 + S2) col = W_TEAL;
            _tft->drawPixel(x, y, col);
        }
    }

    _sleepFrameCount++;
}

// ── Idle animation engine ─────────────────────────────────────────────────────
//
// Anim IDs:
//   0 = BREATHE   — BL sine pulse, 45s block
//   1 = DRIFT     — subtle BL pulse, 20s block
//   2 = TWITCH    — smirk (idx 2) for 400ms
//   3 = BLINK     — BL off for 150ms
//   4 = YAWN      — surprised oval (idx 5) + BL bump for 600ms
//   5 = SIDESMIRK — smirk (idx 2) + BL bump for 800ms
//
// Interruption: mouthIdleStop() restores saved mouth/BL immediately.
// Does not use delay() — all timing via millis() in mouthIdleTick().

static bool     _idleActive    = false;
static uint8_t  _idleAnim      = 0xFF; // 0xFF = none running
static uint8_t  _idlePhase     = 0;
static uint32_t _idlePhaseMs   = 0;
static uint32_t _idleNextMs    = 0;
static uint8_t  _idleSavedMouth = 0;

static void _idleRestore(uint32_t nowMs) {
    bool restoreMouth = (_idleAnim == 2 || _idleAnim == 4 || _idleAnim == 5);
    _idleAnim  = 0xFF;
    _idlePhase = 0;
    analogWrite(MOUTH_TFT_BL, BL_MAP[_currentBLLevel]);
    if (restoreMouth && _tft) mouthTFTShow(_idleSavedMouth);
    // Gap between animations: 20-60s
    _idleNextMs = nowMs + 20000UL + (uint32_t)random(40000);
}

void mouthIdleTick(uint32_t nowMs) {
    if (!_idleActive || !_tft) return;

    // Pick next animation when slot is empty and timer has fired
    if (_idleAnim == 0xFF) {
        if (nowMs < _idleNextMs) return;
        // Weighted pick: blink/twitch common, yawn rare
        uint8_t r = (uint8_t)random(10);
        if      (r < 2) _idleAnim = 0; // BREATHE
        else if (r < 4) _idleAnim = 3; // BLINK
        else if (r < 6) _idleAnim = 2; // TWITCH
        else if (r < 8) _idleAnim = 5; // SIDESMIRK
        else if (r < 9) _idleAnim = 1; // DRIFT
        else            _idleAnim = 4; // YAWN (rare)
        _idlePhase    = 0;
        _idlePhaseMs  = nowMs;
        _idleSavedMouth = _currentMouthIdx;
        // Start expression-changing anims immediately
        switch (_idleAnim) {
            case 2: // TWITCH
                mouthTFTShow(2);
                break;
            case 4: // YAWN
                mouthTFTShow(5);
                analogWrite(MOUTH_TFT_BL,
                    BL_MAP[(uint8_t)constrain((int)_currentBLLevel + 3, 0, 15)]);
                break;
            case 5: // SIDESMIRK
                mouthTFTShow(2);
                analogWrite(MOUTH_TFT_BL,
                    BL_MAP[(uint8_t)constrain((int)_currentBLLevel + 2, 0, 15)]);
                break;
            default: break;
        }
        return;
    }

    uint32_t el = nowMs - _idlePhaseMs;

    switch (_idleAnim) {
        case 0: { // BREATHE — 4s sine, 45s total
            float frac = (sinf(2.0f * M_PI * (float)el / 4000.0f) + 1.0f) * 0.5f;
            uint8_t lo = BL_MAP[2];
            uint8_t hi = BL_MAP[_currentBLLevel];
            analogWrite(MOUTH_TFT_BL, lo + (uint8_t)(frac * (hi - lo)));
            if (el >= 45000UL) _idleRestore(nowMs);
            break;
        }
        case 1: { // DRIFT — gentler pulse, 6s sine, 20s total
            float frac = (sinf(2.0f * M_PI * (float)el / 6000.0f) + 1.0f) * 0.5f;
            uint8_t lo = BL_MAP[(uint8_t)constrain((int)_currentBLLevel - 2, 0, 15)];
            uint8_t hi = BL_MAP[_currentBLLevel];
            analogWrite(MOUTH_TFT_BL, lo + (uint8_t)(frac * (hi - lo)));
            if (el >= 20000UL) _idleRestore(nowMs);
            break;
        }
        case 2: // TWITCH — smirk held 400ms
            if (el >= 400) _idleRestore(nowMs);
            break;
        case 3: // BLINK — BL off 150ms, no fillScreen
            if (_idlePhase == 0) {
                analogWrite(MOUTH_TFT_BL, 0);
                _idlePhase = 1;
            }
            if (el >= 150) _idleRestore(nowMs);
            break;
        case 4: // YAWN — surprised oval held 600ms
            if (el >= 600) _idleRestore(nowMs);
            break;
        case 5: // SIDESMIRK — smirk + BL bump held 800ms
            if (el >= 800) _idleRestore(nowMs);
            break;
    }
}

void mouthIdleStart() {
    if (_idleActive) return;
    _idleActive  = true;
    _idleAnim    = 0xFF;
    _idleNextMs  = millis() + 5000UL; // first anim fires 5s after start
}

void mouthIdleStop() {
    if (!_idleActive) return;
    _idleActive = false;
    if (_idleAnim != 0xFF) {
        bool restoreMouth = (_idleAnim == 2 || _idleAnim == 4 || _idleAnim == 5);
        _idleAnim  = 0xFF;
        _idlePhase = 0;
        analogWrite(MOUTH_TFT_BL, BL_MAP[_currentBLLevel]);
        if (restoreMouth && _tft) mouthTFTShow(_idleSavedMouth);
    }
}

bool mouthIdleIsActive() { return _idleActive; }
