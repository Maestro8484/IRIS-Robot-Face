# ChatGPT Refactor Plan — Analysis
**Date:** 2026-03-28 | **Branch:** refactor/modular-assistant

---

## OVERALL VERDICT

The ChatGPT plan is solid and disciplined. The test-between-every-step, no-combining-steps philosophy is exactly right for a production hardware system. The module boundaries are correct. The order is mostly right with a few exceptions worth discussing below.

---

## STEP-BY-STEP ANALYSIS

### Step 0: Branch
**Status: DONE.** Already created `refactor/modular-assistant`.

---

### Step 2: Create scaffold (empty files, no logic)
**Pro:** Defines module boundaries upfront. Low risk. Forces agreement on structure before touching live code.
**Con:** Ceremonial — empty files don't run or validate. No functional benefit until logic is moved.
**Verdict: Optional but fine.** Useful as a communication checkpoint.

---

### Step 4: Extract TeensyBridge (ChatGPT says FIRST)
**ChatGPT logic:** Highest-risk hardware constraint, prove serial ownership works first.
**Problem:** `TeensyBridge` uses `TEENSY_PORT` and `TEENSY_BAUD` constants that live in `assistant.py`. If you move `TeensyBridge` before extracting config, the new module either:
- Hardcodes those constants (wrong), or
- Imports from `assistant.py` (circular/messy), or
- Needs `config.py` to exist first
**Verdict: TeensyBridge should be step 2, not step 1. Config extraction should precede it.**

---

### Step 7: Extract Audio System (one step)
**ChatGPT bundles:** mic input, playback, interruption, volume control — ~300+ lines across:
`_find_mic_device_index`, `play_pcm`, `play_pcm_speaking`, `play_beep`, `play_double_beep`,
`_playback_interrupt_listener`, `record_command`, `_find_wm8960_card`, `get_volume`, `set_volume`

**Problem:** `play_pcm_speaking()` takes `teensy` as an argument and calls `teensy.send()` during playback. This means `audio_io.py` would depend on `teensy_bridge.py`. That's a valid layered dependency but it must be explicit — not an accident.

**Also:** `_playback_interrupt_listener` runs in a thread, uses `pyaudio`, and references a stop/interrupted event. Complex threading logic is higher regression risk than it appears.
**Verdict: Split into two steps — volume/hardware helpers first, then playback. Or accept the risk and do it as one with careful testing.**

---

### Step 10: Extract WakeWord
**Mostly fine.** `wait_for_wakeword_or_button()` is mostly self-contained.
**Watch for:** The button-press path inside this function touches the LED (`leds.set_all`) and sets `_ptt_mode`. If `wakeword.py` takes `leds` as a parameter, that's a hardware dep into a service module. Minor but worth noting.
**Verdict: Fine, just pass dependencies explicitly as arguments.**

---

### Steps 13, 16, 19: STT, TTS, LLM extractions
**All solid.** These are the right moves and the right order.
**TTS note:** ElevenLabs + Piper both live here along with `synthesize()` which routes between them. Keep them together in `services/tts.py`.
**LLM note:** `ask_ollama()` and `ask_vision()` both call Gandalf. Makes sense to bundle into `services/llm.py`.

---

### Step 22: StateManager (ChatGPT calls "CRITICAL FIX")
**Agreement: this is the most valuable step.** The sleep state desync bug already documented in the snapshot (wakeword handler doesn't set `_eyes_sleeping = False`) is exactly what a centralized StateManager prevents.

**State variables to centralize:**
- `_eyes_sleeping`
- `_kids_mode`
- `_speaking`
- `_interrupted`
- `_current_eye_index`
- `_follow_up_active`
- conversation history/context

**Risk: HIGHEST of all steps.** Every module touches state. Test thoroughly.
**Verdict: Correct placement (after all services extracted, before orchestrator).**

---

### Step 25: Rename assistant.py → main.py
**PROBLEM specific to this project:** The Pi4 systemctl service file (`/etc/systemd/system/assistant.service`) almost certainly references `assistant.py` by name. Renaming without updating the service unit file = production system fails to start after next reboot.

**Also:** Pi4 overlayfs. The service file change must be persisted to SD or it's lost on reboot.
**Verdict: Do this step but add: update service file + persist to SD. Do NOT skip.**

---

### Steps 29–31: Remove hardcoded secrets → .env
**ElevenLabs API key is currently hardcoded in assistant.py plaintext.** This should be done.
**PROBLEM specific to this project:** Pi4 uses overlayfs (read-only SD). A `.env` file:
1. Must be persisted to SD explicitly (not just written to RAM).
2. Won't be automatically loaded by systemctl — must be added to the service unit as `EnvironmentFile=/home/pi/.env` or equivalent.

**ChatGPT's plan assumes a normal Linux environment. This needs extra steps for Pi4.**
**Verdict: Important but Pi4-specific persistence steps must be added.**

---

### Step 32: CI Pipeline
**PROBLEM:** The proposed CI does `python -c "import main"`. The imports in assistant.py include:
- `spidev` — hardware SPI driver (not available on ubuntu-latest)
- `RPi.GPIO` — Raspberry Pi GPIO (not available on ubuntu-latest)
- `pyaudio` — audio hardware (requires system libs)
- `serial` — OK but needs `pyserial`

**The CI import test would fail immediately on GitHub Actions.**
**Verdict: CI is a good idea but needs hardware stubs or a mock-imports strategy. Lower priority for now — defer until after refactor is complete and working on Pi4.**

---

## MISSING FROM CHATGPT PLAN

| Missing Step | Why It Matters |
|---|---|
| `core/config.py` first | Every module needs constants; extract before anything else |
| `hardware/led.py` (APA102) | Completes hardware layer; LED passed around everywhere |
| `services/vision.py` | `capture_image` + `ask_vision` belong in services; ChatGPT bundles into LLM (OK but worth separating) |
| Conversation logger/watchdog | State utilities — belong in `state/` |
| CMD listener + emotion | `start_cmd_listener` + `emit_emotion` are state/orchestration; need explicit home |
| Pi4 deploy after every file move | New `.py` files on Pi4 must be persisted to SD or lost on reboot |

---

## RECOMMENDED ORDER (merged/corrected)

| # | Step | Risk | Value |
|---|---|---|---|
| 1 | Extract `core/config.py` (constants + iris_config loader) | Low | High (foundation) |
| 2 | Scaffold empty module files | None | Low (clarity) |
| 3 | Commit baseline | None | Required |
| 4 | Extract `hardware/teensy_bridge.py` | Medium | High |
| 5 | Test + commit |
| 6 | Extract `hardware/led.py` (APA102) | Low | Low |
| 7 | Commit |
| 8 | Extract `services/tts.py` (ElevenLabs + Piper + synthesize) | Medium | High |
| 9 | Test + commit |
| 10 | Extract `services/stt.py` | Low | Medium |
| 11 | Extract `services/llm.py` (ask_ollama + ask_vision) | Low | Medium |
| 12 | Test + commit |
| 13 | Extract `services/wakeword.py` | Low | Medium |
| 14 | Extract audio playback/record into `hardware/audio_io.py` | Medium-High | High |
| 15 | Test + commit |
| 16 | Extract `state/state_manager.py` + replace globals | HIGH | Highest |
| 17 | Test thoroughly (sleep, wake, desync scenarios) |
| 18 | Commit |
| 19 | Convert `assistant.py` to orchestrator (`main()` only) | Medium | High |
| 20 | Update systemctl service file if renamed; persist to Pi4 SD |
| 21 | Full system test |
| 22 | Move secrets to `.env` + update systemd EnvironmentFile | Low | Important |
| 23 | CI pipeline (with hardware mock strategy) | Low | Medium |

---

## BOTTOM LINE

ChatGPT plan: **correct structure, correct discipline, a few Pi4-specific blind spots.**

Key adjustments:
1. `config.py` before `TeensyBridge`
2. Audio split into two steps (volume helpers vs playback)
3. `main.py` rename requires service file update + SD persist
4. `.env` requires systemd `EnvironmentFile` entry + SD persist
5. CI needs hardware mock strategy, defer until after working refactor
