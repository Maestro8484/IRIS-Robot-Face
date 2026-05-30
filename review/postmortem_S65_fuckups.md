# S65 Post-Mortem — What Broke, Why, How to Never Repeat It
Date: 2026-05-24

---

## What Was In S65c (the build that actually ships)

These are the ONLY changes from the pre-session baseline. All verified safe:

| Change | File | Why safe |
|---|---|---|
| SWSPI → HWSPI2 (`Arduino_HWSPI(&SPI2)`) | mouth_tft.cpp | Verified working in S65 first batch before bad changes were added |
| Sleep backlight `BL_MAP[1]→BL_MAP[5]` | mouth_tft.cpp | Single analogWrite change, no display logic |
| Speed defaults `1.0→0.35`, `shootSpeed 40→15`, `warpSpeed 30→12` | sleep_renderer.h | CFG struct values only, no hardware interaction |
| `MOUTH_RENDER_MIN_MS` 500→75 | main.cpp | Rate-limit reduction, no hardware interaction |
| `MOUTH_SLEEP_FRAME_MS` 150→60 | main.cpp | Rate-limit reduction, no hardware interaction |
| Remove `-D TEENSY_OPT_SMALLEST_CODE` | platformio.ini | Compiler flag only |

These changes do NOT touch: asyncUpdates, SPI clock speed, display driver library,
DMA configuration, or any hardware-timing-sensitive code path.

---

## The Three Things That Blew Up the Hardware

### Fuckup 1 — `asyncUpdates = true` (eye DMA race condition)

**What it did:** Enabled async DMA framebuffer transfers on both GC9A01A eye displays.
The eye engine writes new pixels to the framebuffer while the previous DMA transfer is
still reading from it. Result: one eye showed static/corruption artifacts, one eye
may have been partially functional.

**The signal that this was dangerous — ignored:**
The findings document, written by Claude in the same session, said explicitly:
> "Why it was disabled: Unknown — likely a past stability issue or DMA conflict
> that was never re-investigated."

This sentence identifies an unknown failure mode and then proceeds to enable the feature
anyway. That is the definition of reckless. The correct response to "unknown stability
issue" is a test flash with serial monitoring, not a production deploy.

**Rule going forward:** Any setting that has the comment "disabled for unknown reason"
or "likely stability issue" requires isolated hardware testing before deploy.
Flash it alone, monitor serial output, confirm no corruption over 10+ minutes.
Never bundle it with other changes.

---

### Fuckup 2 — `ILI9341_t3` replacing `Arduino_GFX + HWSPI` (wrong SPI bus, white screen)

**What it did:** Replaced the working `Arduino_GFX + Arduino_HWSPI(&SPI2)` mouth driver
with the Teensyduino built-in `ILI9341_t3` library. The ILI9341_t3 bundled with
Teensyduino 1.159 (framework-arduinoteensy 1.59) auto-detects the SPI bus from MOSI/SCK
pin numbers. It did not correctly select SPI2 from pins 35/37 on this specific framework
version. Result: the mouth TFT received garbage initialization (or SPI0 traffic intended
for the right eye), producing a solid white screen at full brightness.

**What was verified before deploying:** That `ILI9341_t3.h` exists in the framework.
That the constructor accepts MOSI and SCK parameters. That it compiles without errors.

**What was NOT verified:** That SPI2 is actually selected at runtime. That the display
initializes correctly. That it doesn't conflict with SPI0 (right eye bus). None of
this was checked on hardware.

**The correct approach that was skipped:**
The right library was always `mjs513/ILI9341_t3n` (per IRIS_ARCH.md). The built-in
`ILI9341_t3` was chosen specifically to avoid adding a lib_deps entry. That was
laziness masquerading as engineering. `ILI9341_t3n` has explicit SPI2 support, proper
DMA, and is already used for GC9A01A_t3n in this codebase (same author, same pattern).
Using the wrong library to save one line in platformio.ini caused hours of damage.

**Rule going forward:** Library substitutions require:
1. Confirm the library explicitly documents support for the target SPI bus on the
   target MCU (not just "should work from pin numbers").
2. Test flash with ONLY the library change. Print "INIT OK" over serial after
   `begin()`. Confirm display clears to black. Nothing else in the flash.
3. If the arch doc names a specific library (ILI9341_t3n), use that library.
   Do not substitute.

---

### Fuckup 3 — `SPI_SPEED 20 MHz → 40 MHz` (untested signal integrity)

**What it did:** Doubled the SPI clock for both eye displays. Physical wire runs,
connector quality, and PCB trace capacitance determine the maximum reliable SPI speed
for a specific installation. These were never measured or characterized.

**Why it was done:** The GC9A01A datasheet says 80 MHz max. Therefore 40 MHz "should
be fine." This is theoretical reasoning applied to a physical system without measurement.

**The cost:** Even if 40 MHz didn't directly cause visible corruption on its own, it
was bundled with the DMA change and ILI9341_t3 change, making it impossible to isolate
which failure caused which symptom.

**Rule going forward:** SPI clock changes must be tested alone, incrementally:
20 MHz (known good) → 30 MHz → 40 MHz. Each step: flash alone, run for 5 minutes,
inspect displays for any pixel artifacts or glitches at the edges of the display.
Never bundle a clock speed change with a driver change or DMA change.

---

## The Root Fuckup That Enabled All Three

**Batching unverified hardware changes into a single flash.**

The user said "resolve all findings." The correct interpretation was:
- Apply safe changes (rate limits, speed values, build flags, backlight level) → flash → verify
- Test async DMA alone → flash → monitor → verify
- Test SPI speed increase alone → flash → inspect → verify
- Test ILI9341_t3n (correct library) alone → flash → serial confirm → verify

The actual interpretation was: apply everything at once, build once, flash once.
When three different hardware-sensitive changes all have unknown failure modes,
batching them guarantees that a failure cannot be diagnosed.

The findings document even categorized changes by risk:
> "Items 1–4 are each a single-line change and compile-safe.
> Item 5 needs stability testing after items 1–4 are flashed."

That statement was written and then immediately ignored.

---

## What "Needs Hardware Testing" Means — Checklist

Before deploying any change in these categories, it must be tested in isolation:

**SPI clock speed changes:**
- [ ] Flash with ONLY the clock change
- [ ] Run both displays for 5 minutes
- [ ] No pixel corruption, no glitching at display edges
- [ ] Serial shows no updateScreenAsync() failures

**Async DMA changes:**
- [ ] Flash with ONLY the asyncUpdates change
- [ ] Run eye engine for 10 minutes with motion (tracking, blinking)
- [ ] No artifacts, no corruption, no lockup
- [ ] Serial shows no "updateScreenAsync() failed" messages

**Library substitutions (any display driver):**
- [ ] Flash with ONLY the library change
- [ ] Print "INIT OK" to serial after begin()
- [ ] Display clears to black (not white, not random)
- [ ] At least one draw operation (fillRect) executes correctly
- [ ] Confirm correct SPI bus in use (no conflict with other displays)

**DMA + other changes together:**
- [ ] Never. DMA changes ship alone, verified, then other changes build on top.

---

## Changes That Remain Deferred (correct but untested)

These are real improvements that should be done properly:

### async DMA on eye displays
Correct approach: enable `asyncUpdates=true` on ONE eye first. Monitor for 10 minutes.
If clean, enable second eye. If clean, add `updateScreenAsync()` to sleep renderer.
Each step is a separate flash.

### SPI speed increase
Correct approach: 20 → 30 MHz first. Flash alone. 5-minute visual check. If clean,
try 40 MHz. Flash alone. 5-minute visual check.

### ILI9341_t3n for mouth TFT
Correct approach: Add `https://github.com/mjs513/ILI9341_t3n` to lib_deps.
Rewrite mouthTFTInit() to use it. Flash ALONE with a test sketch that just inits
the display and clears to black. Confirm serial prints INIT OK. Then integrate.

---

## Rollback Reference

| Commit | State |
|---|---|
| `a0dd17c` | Pre-session baseline (S64) |
| `091b42a` | S65c — current shipping build (safe changes only) |

To revert to pre-session: `git reset --hard a0dd17c && git push --force`
Then reflash via PlatformIO env:eyes.
