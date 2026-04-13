# Mouth TFT — Full Attempt History for Handoff
**Date:** 2026-04-12  
**Branch:** `feat/teensy41-spi2-mouth`  
**Status:** Build clean. Physical T4.1 swap + first flash NEVER done. Display not yet smoke-tested.

---

## Hardware

| Pin | Signal | Notes |
|-----|--------|-------|
| 35  | MOSI   | SPI2 hw |
| 37  | SCK    | SPI2 hw |
| 36  | CS     | SPI2 |
| 8   | DC     | — |
| 4   | RST    | — |
| 14  | BL     | PWM: 220 boot/wake, 40 sleep |

**Display:** ILI9341 2.8" TFT (320×240), landscape (rotation=1)  
**Board in use so far:** Teensy 4.0 (T4.1 purchased but not yet swapped in)

---

## Attempt Timeline

### Attempt 1 — Adafruit_ILI9341 with &SPI2 (commit 3ceff67, ~Apr 8 S4)
- **Library:** `adafruit/Adafruit ILI9341` + `Adafruit BusIO` + `Adafruit GFX Library`
- **Constructor:** `Adafruit_ILI9341 _tft(&SPI2, DC, CS, RST)`
- **Outcome:** Build failed. The installed Adafruit_ILI9341 version does not have a valid
  constructor taking a `SPIClass*` pointer. Null/bus-pointer constructor not supported.
- **Never flashed.**

### Attempt 2 — Arduino_GFX SWSPI (commit 732b067, Apr 8 S6)
- **Library:** `moononournation/GFX Library for Arduino @ ^1.4.9`
- **Constructor:** `Arduino_SWSPI bus(DC, CS, SCK, MOSI, -1)` + `Arduino_ILI9341 _tft(&bus)`
- **Pins at this stage:** bit-bang on pins 5/6/7 (MOSI/SCK/CS — shared with MAX7219)
- **Outcome:** Build confirmed clean. Never flashed. Pin conflict with MAX7219 (pins 5/6/7)
  was a concern — not resolved before this approach was abandoned.

### Attempt 3 — ILI9341_t3 hardware SPI2, T4.1 migration (commit 1012907, Apr 11 S9)
- **Board change:** teensy40 → teensy41
- **Library:** `paulstoffregen/ILI9341_t3` (native Teensy hardware SPI)
- **Pins moved to dedicated SPI2:** MOSI=35, SCK=37, CS=36 (DC/RST/BL unchanged)
- **Constructor:** `ILI9341_t3 _tft(CS, DC, RST, MOSI, SCK)`
- **Problem discovered this session (S11):** `platformio.ini` still had all three stale
  Adafruit libs as leftover dead weight. `mouth_tft.cpp` still `#include <Adafruit_ILI9341.h>`
  and used `Adafruit_ILI9341` type — the file was not actually updated in commit 1012907
  despite the commit message saying it was. Build was failing silently.

### Attempt 4 — Actual fix (S11, 2026-04-12) ← CURRENT STATE
- **platformio.ini:** removed `adafruit/Adafruit BusIO`, `adafruit/Adafruit GFX Library`,
  `adafruit/Adafruit ILI9341`; confirmed only `paulstoffregen/ILI9341_t3` in lib_deps
- **mouth_tft.cpp:**
  - `#include <Adafruit_ILI9341.h>` → `#include <ILI9341_t3.h>`
  - `static Adafruit_ILI9341 _tft(&SPI2, DC, CS, RST)` →
    `static ILI9341_t3 _tft(CS, DC, RST, MOSI, SCK)`
- **Build result:** `[SUCCESS] Took 6.57 seconds` — confirmed clean
- **Still not flashed.** T4.1 has not been physically swapped in.

---

## Current mouth_tft.cpp state (confirmed in build)

```cpp
#include <ILI9341_t3.h>

static constexpr uint8_t MOUTH_TFT_CS   = 36;
static constexpr uint8_t MOUTH_TFT_DC   =  8;
static constexpr uint8_t MOUTH_TFT_RST  =  4;
static constexpr uint8_t MOUTH_TFT_MOSI = 35;
static constexpr uint8_t MOUTH_TFT_SCK  = 37;
static constexpr uint8_t MOUTH_TFT_BL   = 14;

static ILI9341_t3 _tft(MOUTH_TFT_CS, MOUTH_TFT_DC, MOUTH_TFT_RST,
                        MOUTH_TFT_MOSI, MOUTH_TFT_SCK);
```

`mouthTFTInit()` calls `_tft.begin()`, `setRotation(1)`, `fillScreen(BLACK)`, `analogWrite(BL, 220)`.

---

## platformio.ini lib_deps (current)

```ini
lib_deps =
  https://github.com/PaulStoffregen/Wire
  https://github.com/PaulStoffregen/ST7735_t3
  https://github.com/mjs513/GC9A01A_t3n
  paulstoffregen/ILI9341_t3
```

---

## What needs to happen next

1. **Physical T4.1 swap** — replace T4.0 in enclosure with T4.1
2. **Wire SPI2 mouth pins** per pin table above (MOSI=35, SCK=37, CS=36; DC=8, RST=4, BL=14)
3. **Flash** — user clicks PlatformIO upload button (USB to Desktop PC). Claude runs `pio run` only.
4. **Smoke test** — send `MOUTH:0` through `MOUTH:8` via serial from Pi4, confirm all 9
   expressions render on the TFT
5. **If blank/garbage:** check SPI2 bus assignment in ILI9341_t3 — may need
   `_tft.setSPI(SPI2)` or similar if the library doesn't auto-detect from pin numbers

---

## Key files

| File | Role |
|------|------|
| `src/mouth_tft.cpp` | TFT driver — expressions 0–8 |
| `src/mouth_tft.h` | Public API |
| `platformio.ini` | lib_deps |
| `src/main.cpp` | Serial `MOUTH:n` handler calls `mouthTFTShow(n)` |
