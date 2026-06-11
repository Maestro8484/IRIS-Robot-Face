# Sleep-Mode Failure Diagnosis — S128 (2026-06-11)

Task: IRIS fails to fully return to sleep after the designated evening sleep time.
Mouth TFT → darkened backlight, no visible animation. Eyes → stay awake when woken.
Goal: resolve + harden the scheduled sleep activation.

## Live evidence gathered (read-only, this session)

- User crontab (pi): `0 21 * * *` → `iris_sleep.py`; `30 7 * * *` → `iris_wake.py`.
  Crontab **is persisted to SD** (`/var/spool/cron/crontabs/pi` md5 == `/media/root-ro/...` md5).
  → Scheduled trigger survives reboot. NOT the failure.
- `iris_sleep.py` (cron) sends `EYES:SLEEP` via UDP to assistant CMD listener → `_do_sleep()`.
- Jun 10 logs: 21:00 scheduled sleep AND 22:26 wake-quip-then-resleep BOTH fired
  `EYES:SLEEP -- starfield starting` at the firmware. Eyes DID re-sleep at the firmware level.
  Every sleep event pushed `MOUTH_INTENSITY:1`.

## ROOT CAUSE 1 — Mouth blank (PRIMARY, fully confirmed)

Live `/home/pi/iris_config.json` overrides `MOUTH_INTENSITY_SLEEP = 1`.
Firmware `BL_MAP[1] = 2/255 ≈ 0.8%` backlight → screen lit but starfield invisible.
= exactly "darkened but still-activated backlight, no animation."

- Firmware `EYES:SLEEP` handler ALREADY sets a sane visible sleep backlight
  (`mouthSetSleepIntensity()` → `BL_MAP[5] = 16/255 ≈ 6%`, main.cpp:243).
- But `_do_sleep()` (assistant.py:664-665) then sends `MOUTH:8` + `MOUTH_INTENSITY:1`,
  clobbering the firmware's good value back to blank.
- Repo `core/config.py:211` ALREADY corrects the default to `5`
  ("was 1 (≈0.8%, appeared blank)") — but the live `iris_config.json` override (=1) wins.

FIX: set `MOUTH_INTENSITY_SLEEP` to `5` in live `iris_config.json` (or delete the override
so config.py's 5 applies). `iris_config.json` is a PROTECTED file → needs explicit user OK.

## ROOT CAUSE 2 — Eyes stay awake (state desync, intermittent)

`state.eyes_sleeping` (state_manager.py:27) is in-memory, defaults `False`, and is NOT
seeded from `/tmp/iris_sleep_mode` at startup. An assistant.py restart during the sleep
window (one happened today 06:36) leaves Pi state=`False` while the flag file says asleep
and the Teensy is still showing starfield → desync.

The voice eye commands are GUARDED by this flaky flag:
- assistant.py:1001 `EYES_SLEEP`: `if not state.eyes_sleeping:` → if state wrongly True, "go to
  sleep" is a silent no-op, eyes stay awake.
- assistant.py:1008 `EYES_WAKE`, :971 auto-wake: same guard pattern.

Firmware `EYES:SLEEP` is guarded by `if (!eyesSleeping)` (main.cpp:230), BUT the firmware is
self-consistent: the main render loop renders the starfield every frame **whenever**
`eyesSleeping` is true (main.cpp:446), and the awake eye engine only when false. So the eyes
cannot visually desync from the firmware flag, and `EYES:SLEEP` always sleeps awake eyes.
=> NO firmware change is required. The eyes-awake symptom is entirely the Pi-side state-guard
no-op. (Firmware flash skipped — would only add a redundant double-init/flash risk.)

The robust flag-file wake path (assistant.py:829) re-sleeps correctly (matches Jun 10 log);
the STATE-guarded paths are the fragile ones.

## SECONDARY — Piper goodnight broken

`iris_sleep.py:34` calls `/usr/local/bin/piper` which does not exist
(`bash: /usr/local/bin/piper: No such file or directory` in iris_sleep.log).
"Goodnight." announcement never plays. Non-fatal but part of "harden."

## OBSERVATIONS / hardening opportunities

- Sleep/wake cron entries live ONLY in the pi user crontab — not version-controlled in the
  repo (only `iris-logs.cron` is). Should be captured under `pi4/scripts/` for reproducibility.
- Firmware [VER] is WARN/absent in POST → cannot positively confirm flashed firmware == repo
  S101. Recommend a VERSION check before trusting firmware-internal behavior.
- `in_sleep_window()` end hour = 8 but wake cron = 7:30 → 30-min window (07:30-08:00) where a
  wake-quip immediately re-sleeps. Cosmetic, low priority.

## Proposed fix set

Pi-side (DEPLOY):
1. `iris_config.json`: `MOUTH_INTENSITY_SLEEP` 1 → 5  (PROTECTED — needs OK).
2. assistant.py: seed `state.eyes_sleeping` from `/tmp/iris_sleep_mode` at startup; make the
   voice `EYES_SLEEP`/`EYES_WAKE` branches reassert hardware unconditionally (drop the state
   guard so the command is always authoritative/idempotent).
3. iris_sleep.py: fix/replace the broken Piper goodnight call.

Firmware:
4. NONE NEEDED — render loop is gated on `eyesSleeping`, so firmware is already
   self-consistent (see Root Cause 2).

Repo hygiene:
5. Add the sleep/wake cron entries to `pi4/scripts/` for version control.

## STATUS — DEPLOYED + VERIFIED (S128, 2026-06-11)

- iris_config.json `MOUTH_INTENSITY_SLEEP` 1->5 — live + SD (md5 RAM==SD).
- assistant.py voice EYES_SLEEP/EYES_WAKE -> authoritative `_do_sleep`/`_do_wake`;
  startup sleep-state reconcile added — live + SD (md5 RAM==SD).
- iris_sleep.py broken Piper goodnight -> optional /home/pi/sounds/goodnight.wav — live + SD.
- POST after restart: 20/23 PASS, 3 WARN, 0 FAIL -> AUTHORIZED.
- Live functional test (10:57): EYES:SLEEP via CMD port -> `MOUTH_INTENSITY: 5` (was 1),
  `starfield starting`; EYES:WAKE -> `MOUTH_INTENSITY: 10`, displays restored.
- Full 21:00 scheduled-sleep reconcile path exercises tonight (first live sleep window after deploy).
