# IRIS Snapshot

> **WARNING: DO NOT USE PROJECT-ATTACHED .md FILES.**
> Read live repo via filesystem MCP only. Claude.ai project knowledge base attachments are stale (last updated S49, May 2026 -- 48 sessions behind as of S97). Any session that reads them instead of this file gets wrong hardware state, wrong serial numbers, wrong firmware version, and wrong deploy status.

**Session:** S98 | **Date:** 2026-06-02 | **Branch:** `main` | **Last commit:** S97

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **T40 mechanical damper** — servo tracking confirmed working, user tuning physically. No firmware change needed.
2. **Deploy pi4/iris_web.html + iris_web.js** — EYE:6 Striking Blue fix (3 locations). REPO-ONLY.
3. **RD-003** — Duplicate sleep log: `/home/pi/iris_sleep.log` vs `/home/pi/logs/iris_sleep.log`.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. assistant.service active. ttyIRIS_EYES → ttyACM0 (serial 13625440, T41). udev corrected + SD persisted S97. |
| GandalfAI 192.168.1.3 | Operational. iris model qwen2.5vl:32b-q4_K_M (S77). Kokoro TTS port 8004. |
| Teensy 4.1 (eyes+mouth) | **FLASHED S97.** [VER] confirmed. Bridge live, no DROPs. is_facing + confidence>60 + FACE_LOST 5000ms restored. |
| Teensy 4.0 (servo+gesture) | **FLASHED S97** (FACE_RETURN_MS 30000ms). Tracking confirmed working. Mechanical damper tuning ongoing. |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). |

---

## Active Issues

- **LOW: iris_web.html + iris_web.js deploy pending** — EYE:6 fix (3 locations). REPO-ONLY.
- **LOW: RD-003** — Duplicate sleep log paths.

---

## udev Serial Numbers — Confirmed S97

| Symlink | Serial | Device |
|---|---|---|
| `/dev/ttyIRIS_EYES` | `13625440` | Teensy 4.1 (eyes + TFT mouth) |
| `/dev/ttyIRIS_SERVO` | `12763490` | Teensy 4.0 (servo + gesture) |

S94b had these swapped. Corrected S97 by connecting T41 alone and observing which serial appeared. IRIS_ARCH.md, pi4/scripts/99-iris-teensy.rules, and live Pi4 udev rules all updated.

---

## Do Not Touch

- `iris_config.json` — gesture map + emotion map live config
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S98)

- **`SNAPSHOT_LATEST.md`** — Added stale-attachment warning block at top.
- **`HANDOFF_CURRENT.md`** — Added stale-attachment warning block at top.
- **`PRIMER.md`** — Added filesystem MCP mandate block at top (explicit prohibition on Claude.ai project knowledge base attachments).

## Previous Session Changes (S97)

- **`src/main.cpp`** — FACE_LOST_TIMEOUT_MS 500→5000ms. Gate restored: `is_facing && confidence>60`.
- **`src/config.h`** — FIRMWARE_VERSION S96j→S97.
- **`servo_teensy40/teensy40_base_mount/pan_servo.h`** — FACE_RETURN_MS 6000→30000ms.
- **`scripts/flash_t41.ps1`** + **`scripts/flash_t40.ps1`** — Fixed cross-flash bug: removed `-s`, replaced with explicit device-targeted bootloader entry via printf+python3.
- **`pi4/scripts/99-iris-teensy.rules`** — Serial numbers corrected (T41=13625440, T40=12763490). DEPLOYED+PERSISTED.
- **`IRIS_ARCH.md`** — USB Device Identity table corrected.

**T41 status:** FLASHED+VERIFIED. **T40 status:** FLASHED+VERIFIED.
