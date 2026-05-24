// sleep_renderer.h — Deep space starfield on both TFTs when eyesSleeping.
// renderSleepFrame() called from main loop() instead of the eye engine.
// v2: amplified stars (40/eye, 4 layers), 4 shooting stars/eye with long trails,
//     bigger crescent moon with glow, Earth planet + warp streaks replaces green circle.
// Backup: sleep_renderer_backup.h (original v1)
#pragma once
#include <Arduino.h>
#include <math.h>
#include <GC9A01A_t3n.h>

// ---------------------------------------------------------------------------
// COLORS (RGB565)
// ---------------------------------------------------------------------------
static constexpr uint16_t SR_BLACK       = 0x0000;
static constexpr uint16_t SR_WARM_WHITE  = 0xE71F;
static constexpr uint16_t SR_BLUE_WHITE  = 0xAD7F;
static constexpr uint16_t SR_ICE_BLUE    = 0x9CDF;
static constexpr uint16_t SR_GOLD        = 0xFD40;  // golden giant star
static constexpr uint16_t SR_MOON        = 0xE79F;  // brighter blue-white moon
static constexpr uint16_t SR_MOON_GLOW   = 0x2104;  // very faint blue glow ring
static constexpr uint16_t SR_NEBULA_PUR  = 0x2801;  // dim purple nebula
static constexpr uint16_t SR_NEBULA_BLU  = 0x0003;  // dim blue nebula
static constexpr uint16_t SR_NEBULA_MAG  = 0x2001;  // faint magenta wisp
static constexpr uint16_t SR_ZZZ         = 0x0003;
// Earth palette
static constexpr uint16_t SR_EARTH_OCEAN = 0x09F1;  // deep blue ocean
static constexpr uint16_t SR_EARTH_LAND  = 0x1B22;  // dark green continent
static constexpr uint16_t SR_EARTH_DESERT= 0x6223;  // brown/desert landmass
static constexpr uint16_t SR_EARTH_POLAR = 0xEF7D;  // polar ice cap
static constexpr uint16_t SR_EARTH_ATMOS = 0x647F;  // pale blue atmosphere ring
static constexpr uint16_t SR_WARP_STREAK = 0x4A7F;  // hyperspace blue-white line

// ---------------------------------------------------------------------------
// DISPLAY SIZE
// ---------------------------------------------------------------------------
static constexpr int SR_W  = 240;
static constexpr int SR_H  = 240;
static constexpr int SR_CX = 120;
static constexpr int SR_CY = 120;

// ---------------------------------------------------------------------------
// STARS — 40 per display, 4 layers
// Layer 0: 4 giant stars   (r=4, fast twinkle 1.8–2.4s)
// Layer 1: 8 big stars     (r=3, period 2.2–3.0s)
// Layer 2: 12 medium stars (r=2, period 3.0–4.2s)
// Layer 3: 16 small dim    (r=1, period 4.0–6.0s)
// ---------------------------------------------------------------------------
struct SrStar {
    uint8_t  x, y;
    uint8_t  r;
    uint16_t period;
    uint16_t phase;
    uint16_t color;
};

static constexpr int SR_STAR_COUNT = 40;

static constexpr SrStar SR_STARS_L[40] = {
    // Layer 0 — 4 giant stars
    {  32,  18, 4, 1800,    0, SR_WARM_WHITE },
    { 210, 155, 4, 2200,  700, SR_ICE_BLUE   },
    {  60, 195, 4, 2000,  350, SR_BLUE_WHITE },
    { 175,  30, 4, 2400, 1100, SR_GOLD       },
    // Layer 1 — 8 big stars
    { 195,  40, 3, 2300,  200, SR_BLUE_WHITE },
    {  70, 200, 3, 2500, 1500, SR_WARM_WHITE },
    {  50,  90, 3, 2700,  400, SR_BLUE_WHITE },
    { 170,  25, 3, 2600, 1000, SR_ICE_BLUE   },
    { 115,  50, 3, 2400,  600, SR_GOLD       },
    { 230, 100, 3, 2800,  900, SR_WARM_WHITE },
    {  18, 155, 3, 2200,  150, SR_ICE_BLUE   },
    { 145, 205, 3, 2900, 1300, SR_BLUE_WHITE },
    // Layer 2 — 12 medium stars
    { 100,  55, 2, 3000,  250, SR_WARM_WHITE },
    { 148, 190, 2, 3400, 1000, SR_BLUE_WHITE },
    {  20, 145, 2, 3600,  700, SR_ICE_BLUE   },
    { 220,  90, 2, 3800, 1500, SR_WARM_WHITE },
    {  60, 230, 2, 3200,  350, SR_BLUE_WHITE },
    { 185, 210, 2, 4000, 1100, SR_ICE_BLUE   },
    {  90, 170, 2, 3500,  850, SR_WARM_WHITE },
    { 230,  50, 2, 3700, 1300, SR_BLUE_WHITE },
    { 130,  80, 2, 3300,  500, SR_ICE_BLUE   },
    {  80, 115, 2, 4200,  200, SR_GOLD       },
    { 200, 175, 2, 3900,  800, SR_WARM_WHITE },
    {  45,  30, 2, 3100, 1200, SR_BLUE_WHITE },
    // Layer 3 — 16 small stars
    {  15,  60, 1, 4000,  150, SR_ICE_BLUE   },
    { 200, 130, 1, 4800,  750, SR_BLUE_WHITE },
    {  45, 180, 1, 5400, 1400, SR_ICE_BLUE   },
    { 165,  75, 1, 4400,  950, SR_WARM_WHITE },
    { 235, 200, 1, 5600,  300, SR_ICE_BLUE   },
    {  80,  30, 1, 4600, 1600, SR_BLUE_WHITE },
    { 120, 220, 1, 5000,  550, SR_ICE_BLUE   },
    { 225, 160, 1, 4300,  100, SR_WARM_WHITE },
    {  30, 115, 1, 5200,  850, SR_ICE_BLUE   },
    { 155,  35, 1, 4500, 1250, SR_BLUE_WHITE },
    { 190,  80, 1, 5800,  450, SR_GOLD       },
    {  10, 200, 1, 4700,  700, SR_ICE_BLUE   },
    { 110, 140, 1, 5100, 1100, SR_WARM_WHITE },
    {  65,  12, 1, 4900,  300, SR_ICE_BLUE   },
    { 140,   8, 1, 5300, 1500, SR_BLUE_WHITE },
    { 215,  22, 1, 6000,  600, SR_ICE_BLUE   },
};

static constexpr SrStar SR_STARS_R[40] = {
    // Layer 0 — 4 giant stars
    {  45,  30, 4, 1900,  300, SR_WARM_WHITE },
    { 185,  55, 4, 2100,  900, SR_GOLD       },
    {  25, 160, 4, 2300,  600, SR_ICE_BLUE   },
    { 215, 140, 4, 2000, 1500, SR_BLUE_WHITE },
    // Layer 1 — 8 big stars
    { 160,  18, 3, 2500, 1100, SR_ICE_BLUE   },
    { 110,  65, 3, 2600,  400, SR_WARM_WHITE },
    {  35, 100, 3, 2800,  650, SR_ICE_BLUE   },
    { 215,  80, 3, 2400, 1600, SR_WARM_WHITE },
    {  70, 225, 3, 2200,  250, SR_BLUE_WHITE },
    { 190, 205, 3, 2900, 1200, SR_ICE_BLUE   },
    { 100, 165, 3, 2700,  700, SR_WARM_WHITE },
    { 235,  45, 3, 2300, 1350, SR_BLUE_WHITE },
    // Layer 2 — 12 medium stars
    { 140,  90, 2, 3200,  500, SR_ICE_BLUE   },
    {  20,  50, 2, 4000,  100, SR_ICE_BLUE   },
    { 205, 120, 2, 4600,  800, SR_BLUE_WHITE },
    { 120, 175, 2, 5200, 1450, SR_ICE_BLUE   },
    { 175,  70, 2, 4400, 1000, SR_WARM_WHITE },
    { 230, 195, 2, 5400,  350, SR_ICE_BLUE   },
    {  90,  25, 2, 4600, 1550, SR_BLUE_WHITE },
    { 125, 215, 2, 4900,  600, SR_ICE_BLUE   },
    { 220, 150, 2, 4300,  150, SR_WARM_WHITE },
    {  40, 105, 2, 5000,  900, SR_ICE_BLUE   },
    { 150,  40, 2, 4500, 1300, SR_BLUE_WHITE },
    {  75, 135, 2, 3800,  450, SR_GOLD       },
    // Layer 3 — 16 small stars
    {  10,  75, 1, 4100,  200, SR_ICE_BLUE   },
    { 210,  40, 1, 4800,  700, SR_BLUE_WHITE },
    {  50, 150, 1, 5500, 1200, SR_ICE_BLUE   },
    { 170, 100, 1, 4300,  950, SR_WARM_WHITE },
    { 235, 175, 1, 5700,  400, SR_ICE_BLUE   },
    {  95,  45, 1, 4600, 1600, SR_BLUE_WHITE },
    { 130, 225, 1, 5100,  550, SR_ICE_BLUE   },
    { 215, 155, 1, 4200,  100, SR_WARM_WHITE },
    {  30, 120, 1, 5300,  850, SR_ICE_BLUE   },
    { 155,  35, 1, 4400, 1250, SR_BLUE_WHITE },
    { 185,  90, 1, 5900,  450, SR_GOLD       },
    {  15,  30, 1, 4700,  700, SR_ICE_BLUE   },
    { 110, 140, 1, 5100, 1100, SR_WARM_WHITE },
    {  65,  20, 1, 4900,  300, SR_ICE_BLUE   },
    { 145,  10, 1, 5300, 1500, SR_BLUE_WHITE },
    { 220,  25, 1, 6000,  600, SR_ICE_BLUE   },
};

// ---------------------------------------------------------------------------
// STATE
// ---------------------------------------------------------------------------
static bool     srInitialized = false;
static uint32_t srLastFrameMs = 0;
static constexpr uint32_t SR_FRAME_MS = 130; // ~7.7fps — relaxed pace

// Moon
static constexpr int SR_MOON_CX      = 120;
static constexpr int SR_MOON_CY_L    = 80;   // left eye
static constexpr int SR_MOON_CY_R    = 83;   // right eye
static constexpr int SR_MOON_R       = 26;   // was 18 — bigger moon
static constexpr int SR_MOON_BITE_R  = 22;   // was 15 — deep crescent
static constexpr int SR_MOON_BITE_DX = 13;   // was 9
static constexpr int SR_MOON_BITE_DY = -4;   // was -3

// Pulse rings — 3 expanding rings around screen center
static constexpr float SR_RING_SPEED = 0.6f;
static constexpr float SR_RING_MIN   = 30.0f;
static constexpr float SR_RING_MAX   = 68.0f;
static float srRingR[3] = { 30.0f, 41.0f, 51.0f };

// Shooting stars — 4 per display (was 2)
static constexpr int      SR_SHOOT_COUNT    = 4;
static constexpr uint32_t SR_SHOOT_INTERVAL = 4000; // ms per traverse
static constexpr int      SR_SHOOT_TRAIL    = 38;   // trail length px
static uint32_t srShootTimerL[4] = {0, 0, 0, 0};
static uint32_t srShootTimerR[4] = {0, 0, 0, 0};

// Left eye shooting star paths: {x0, y0, x1, y1}
static constexpr int SR_SHOOT_L[4][4] = {
    {  18,  42,  90,  18 },
    { 128, 162, 178, 142 },
    { 210,  68, 155,  38 },
    { 185, 215, 230, 195 },
};
// Right eye shooting star paths
static constexpr int SR_SHOOT_R[4][4] = {
    { 222,  35, 148,  12 },
    {  52, 168,  15, 148 },
    {  28,  88,  72,  55 },
    { 198, 218, 152, 200 },
};

// Earth planet position — right eye, bottom-left
static constexpr int SR_EARTH_CX = 58;
static constexpr int SR_EARTH_CY = 192;
static constexpr int SR_EARTH_R  = 38;

// ZZZ
static constexpr uint32_t SR_ZZZ_CYCLE  = 3800;
static constexpr uint32_t SR_ZZZ_GAP    = 1270;
static const uint8_t      SR_ZZZ_SIZE[3]= {2, 1, 1};
static constexpr int SR_ZZZ_ORIGIN_X = SR_MOON_CX + SR_MOON_R + 4; // 150
static constexpr int SR_ZZZ_ORIGIN_Y = SR_MOON_CY_L - SR_MOON_R - 10; // 44

// ---------------------------------------------------------------------------
// HELPERS
// ---------------------------------------------------------------------------

static inline float srBrightness(uint32_t nowMs, uint16_t period, uint16_t phase) {
    float t = (float)((nowMs + phase) % period) / (float)period;
    float s = 0.5f + 0.5f * sinf(t * 6.2832f);
    return s * s;
}

static void srDrawStar(GC9A01A_t3n* d, const SrStar& s, uint32_t nowMs) {
    float b = srBrightness(nowMs, s.period, s.phase);
    if (b < 0.04f) return;
    uint16_t c = s.color;
    uint8_t r5 = ((c >> 11) & 0x1F);
    uint8_t g6 = ((c >> 5)  & 0x3F);
    uint8_t b5 = (c & 0x1F);
    r5 = (uint8_t)(min(r5 * b * 1.5f, 31.0f));
    g6 = (uint8_t)(min(g6 * b * 1.5f, 63.0f));
    b5 = (uint8_t)(min(b5 * b * 1.5f, 31.0f));
    if (r5 == 0 && g6 == 0 && b5 == 0) return;
    uint16_t col = ((uint16_t)r5 << 11) | ((uint16_t)g6 << 5) | b5;
    if (s.r <= 1) {
        d->drawPixel(s.x, s.y, col);
    } else if (s.r == 2) {
        d->drawPixel(s.x,   s.y,   col);
        d->drawPixel(s.x+1, s.y,   col);
        d->drawPixel(s.x,   s.y+1, col);
        d->drawPixel(s.x+1, s.y+1, col);
    } else {
        d->fillCircle(s.x, s.y, s.r, col);
        // Cross flare on bright giant stars
        if (s.r >= 4 && b > 0.55f) {
            d->drawPixel(s.x - s.r - 1, s.y, col);
            d->drawPixel(s.x + s.r + 1, s.y, col);
            d->drawPixel(s.x, s.y - s.r - 1, col);
            d->drawPixel(s.x, s.y + s.r + 1, col);
        }
    }
}

static void srDrawMoon(GC9A01A_t3n* d, int baseCY) {
    uint32_t t = millis();
    int cy = baseCY + (int)roundf(3.0f * sinf((float)t / 5000.0f));
    // Glow rings before filling body
    d->drawCircle(SR_MOON_CX, cy, SR_MOON_R + 5, SR_MOON_GLOW);
    d->drawCircle(SR_MOON_CX, cy, SR_MOON_R + 3, SR_MOON_GLOW);
    d->drawCircle(SR_MOON_CX, cy, SR_MOON_R + 1, 0x4228);  // brighter inner glow
    // Moon body
    d->fillCircle(SR_MOON_CX, cy, SR_MOON_R, SR_MOON);
    // Deep crescent bite
    d->fillCircle(SR_MOON_CX + SR_MOON_BITE_DX,
                  cy + SR_MOON_BITE_DY,
                  SR_MOON_BITE_R, SR_BLACK);
}

static void srDrawRings(GC9A01A_t3n* d, int frameNum) {
    for (int i = 0; i < 3; i++) {
        int ri = (int)srRingR[i];
        float fade = 1.0f - (srRingR[i] - SR_RING_MIN) / (SR_RING_MAX - SR_RING_MIN);
        if (fade < 0.2f && (frameNum & 1)) continue;
        uint16_t color = (fade > 0.5f) ? 0x0005 : 0x0002;
        d->drawCircle(SR_CX, SR_CY, ri, color);
    }
}

static void srAdvanceRings() {
    for (int i = 0; i < 3; i++) {
        srRingR[i] += SR_RING_SPEED;
        if (srRingR[i] > SR_RING_MAX) srRingR[i] = SR_RING_MIN;
    }
}

// Draw one shooting star segment. progress 0.0→1.0 across path.
static void srDrawShootStar(GC9A01A_t3n* d, const int path[4], float progress) {
    float x0 = path[0], y0 = path[1];
    float x1 = path[2], y1 = path[3];
    float dx = x1 - x0, dy = y1 - y0;
    float len = sqrtf(dx*dx + dy*dy);
    if (len < 1.0f) return;
    float ux = dx/len, uy = dy/len;

    float headDist = progress * len;
    float segStart = headDist - (float)SR_SHOOT_TRAIL;
    if (segStart < 0.0f) segStart = 0.0f;

    for (float s = segStart; s <= headDist; s += 1.0f) {
        int px = (int)(x0 + ux * s);
        int py = (int)(y0 + uy * s);
        float intensity = (s - segStart) / (float)SR_SHOOT_TRAIL;
        uint16_t col;
        if      (intensity > 0.88f) col = 0xFFFF;          // pure white head
        else if (intensity > 0.70f) col = 0xD6FF;          // warm white
        else if (intensity > 0.50f) col = 0xAD7F;          // blue-white
        else if (intensity > 0.28f) col = 0x647F;          // pale blue
        else                        col = 0x2316;          // dim blue tail
        if (px >= 0 && px < SR_W && py >= 0 && py < SR_H) {
            d->drawPixel(px, py, col);
            // Widen head for brighter section
            if (intensity > 0.80f) {
                if (px+1 < SR_W) d->drawPixel(px+1, py, 0xBDF7);
                if (py+1 < SR_H) d->drawPixel(px, py+1, 0xBDF7);
            }
        }
    }
}

static void srHandleShootingStars(GC9A01A_t3n* left, GC9A01A_t3n* right, uint32_t nowMs) {
    for (int i = 0; i < SR_SHOOT_COUNT; i++) {
        // Left eye
        if (nowMs >= srShootTimerL[i]) {
            uint32_t elapsed = nowMs - srShootTimerL[i];
            if (elapsed < SR_SHOOT_INTERVAL) {
                float progress = (float)elapsed / (float)SR_SHOOT_INTERVAL;
                srDrawShootStar(left, SR_SHOOT_L[i], progress);
            } else {
                srShootTimerL[i] = nowMs + SR_SHOOT_INTERVAL + (uint32_t)(i * 650);
            }
        }
        // Right eye
        if (nowMs >= srShootTimerR[i]) {
            uint32_t elapsed = nowMs - srShootTimerR[i];
            if (elapsed < SR_SHOOT_INTERVAL) {
                float progress = (float)elapsed / (float)SR_SHOOT_INTERVAL;
                srDrawShootStar(right, SR_SHOOT_R[i], progress);
            } else {
                srShootTimerR[i] = nowMs + SR_SHOOT_INTERVAL + (uint32_t)(i * 650);
            }
        }
    }
}

// Draw Earth-like planet with hyperspace warp streaks.
// Position: SR_EARTH_CX/CY/R on the right eye (bottom-left quadrant).
static void srDrawEarth(GC9A01A_t3n* d) {
    int cx = SR_EARTH_CX, cy = SR_EARTH_CY, r = SR_EARTH_R;

    // Atmosphere glow
    d->drawCircle(cx, cy, r + 5, SR_EARTH_ATMOS);
    d->drawCircle(cx, cy, r + 3, 0x2452);
    d->drawCircle(cx, cy, r + 1, 0x4493);

    // Ocean base
    d->fillCircle(cx, cy, r, SR_EARTH_OCEAN);

    // Continent patches
    d->fillCircle(cx - 10, cy -  8, 14, SR_EARTH_LAND);    // main landmass
    d->fillCircle(cx + 12, cy - 12, 10, SR_EARTH_LAND);    // northern continent
    d->fillCircle(cx +  5, cy + 14,  8, SR_EARTH_DESERT);  // desert region
    d->fillCircle(cx - 16, cy + 10,  7, SR_EARTH_LAND);    // western islands

    // Polar ice caps
    d->fillCircle(cx,       cy - r + 5, 7, SR_EARTH_POLAR);
    d->fillCircle(cx,       cy + r - 5, 5, SR_EARTH_POLAR);
}

// Draw one ZZZ character. cyclePhase: 0.0→1.0 within SR_ZZZ_CYCLE.
static bool srDrawOneZzz(GC9A01A_t3n* d, int startX, int startY,
                          uint8_t sz, float cyclePhase, bool driftRight) {
    if (cyclePhase < 0.0f || cyclePhase >= 1.0f) return false;
    float fade;
    if      (cyclePhase < 0.1f) fade = cyclePhase / 0.1f;
    else if (cyclePhase < 0.9f) fade = 1.0f;
    else                         fade = (1.0f - cyclePhase) / 0.1f;
    if (fade < 0.05f) return false;

    float driftX = cyclePhase * (driftRight ? 14.0f : -14.0f);
    float driftY = cyclePhase * -30.0f;
    int cx = startX + (int)driftX;
    int cy = startY + (int)driftY;

    uint16_t col = (fade > 0.5f) ? SR_ZZZ : 0x0001;
    if (cx >= 0 && cx < SR_W - sz*6 && cy >= 0 && cy < SR_H - sz*8) {
        d->drawChar(cx, cy, 'Z', col, SR_BLACK, sz, sz);
    }
    return true;
}

static void srDrawZzz(GC9A01A_t3n* left, GC9A01A_t3n* right, uint32_t nowMs) {
    uint32_t t = nowMs % (SR_ZZZ_CYCLE + SR_ZZZ_GAP * 3);
    for (int i = 0; i < 3; i++) {
        uint32_t zStart   = i * SR_ZZZ_GAP;
        int32_t  zElapsed = (int32_t)t - (int32_t)zStart;
        float    phase    = (float)zElapsed / (float)SR_ZZZ_CYCLE;
        int      originY  = SR_ZZZ_ORIGIN_Y - i * (SR_ZZZ_SIZE[i] * 9);
        srDrawOneZzz(left,  SR_ZZZ_ORIGIN_X, originY, SR_ZZZ_SIZE[i], phase, true);
        srDrawOneZzz(right, SR_W - SR_ZZZ_ORIGIN_X - SR_ZZZ_SIZE[i]*6,
                            originY, SR_ZZZ_SIZE[i], phase, false);
    }
}

// ---------------------------------------------------------------------------
// INIT — called once on sleep entry (after blankDisplays)
// ---------------------------------------------------------------------------
static inline void sleepRendererInit() {
    srInitialized = true;
    srLastFrameMs = 0;
    srRingR[0] = 30.0f;
    srRingR[1] = 41.0f;
    srRingR[2] = 51.0f;
    uint32_t now = millis();
    // Stagger 4 shooting stars per eye — first fires at 800ms
    for (int i = 0; i < SR_SHOOT_COUNT; i++) {
        srShootTimerL[i] = now + 800  + (uint32_t)(i * 875);
        srShootTimerR[i] = now + 1200 + (uint32_t)(i * 875);
    }
}

// ---------------------------------------------------------------------------
// RENDER — called every loop() iteration while sleeping
// ---------------------------------------------------------------------------
static uint32_t srFrameCount = 0;

static inline void renderSleepFrame(GC9A01A_t3n* left, GC9A01A_t3n* right) {
    if (!left || !right) return;

    uint32_t nowMs = millis();
    if (nowMs - srLastFrameMs < SR_FRAME_MS) return;
    srLastFrameMs = nowMs;
    srFrameCount++;
    if ((srFrameCount % 10) == 0) {
        Serial.print("[SR] frame=");
        Serial.println(srFrameCount);
    }

    // ── Left eye ──────────────────────────────────────────────────
    left->fillScreen(SR_BLACK);
    // Nebula clouds
    left->fillCircle( 55, 185, 55, SR_NEBULA_PUR);
    left->fillCircle(185, 190, 45, SR_NEBULA_BLU);
    left->fillCircle(175,  45, 30, SR_NEBULA_MAG);  // magenta wisp top-right
    for (int i = 0; i < SR_STAR_COUNT; i++) srDrawStar(left, SR_STARS_L[i], nowMs);
    srDrawMoon(left, SR_MOON_CY_L);
    srDrawRings(left, (int)srFrameCount);

    // ── Right eye ─────────────────────────────────────────────────
    right->fillScreen(SR_BLACK);
    // Nebula top-right; Earth replaces old teal green circle bottom-left
    right->fillCircle(180,  55, 50, SR_NEBULA_PUR);
    right->fillCircle(185,  60, 28, SR_NEBULA_BLU);  // blue wisp overlay
    for (int i = 0; i < SR_STAR_COUNT; i++) srDrawStar(right, SR_STARS_R[i], nowMs);
    srDrawMoon(right, SR_MOON_CY_R);
    srDrawRings(right, (int)srFrameCount);
    srDrawEarth(right);  // Earth planet

    // ── Shared elements ───────────────────────────────────────────
    srHandleShootingStars(left, right, nowMs);
    srDrawZzz(left, right, nowMs);

    srAdvanceRings();

    left->updateScreen();
    right->updateScreen();
}
