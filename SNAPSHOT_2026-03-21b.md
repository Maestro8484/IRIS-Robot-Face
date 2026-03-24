# Wall-E Robot Face — Project Snapshot
**Date:** 2026-03-21b (end of session)
**Status:** Voice (ElevenLabs Daniel), vision (gemma3:27b), emotion LEDs, Teensy firmware all implemented. Teensy NOT yet flashed with eye-swap code.

---

## HOW TO RESUME IN A NEW CHAT
Say: "Read the project snapshot at `C:\Users\SuperMaster\Documents\PlatformIO\TeensyEyes-4.0-PrsnSnsrSrvoRdDisp-AI\SNAPSHOT_2026-03-21b.md` and continue from where we left off."

---

## 1. SYSTEM ARCHITECTURE

| System | IP | Credentials | Role |
|--------|----|-------------|------|
| Pi4 (Jarvis) | 192.168.1.200 | pi / ohs | Voice pipeline, LEDs, camera, Teensy serial |
| GandalfAI | 192.168.1.3 | gandalf / 5309 | Ollama LLM, Whisper STT, Piper TTS |
| Desktop PC | 192.168.1.103 | SuperMaster | PlatformIO Teensy firmware |
| Teensy 4.0 | USB → /dev/ttyACM0 | N/A | Eye displays, emotion rendering |

---

## 2. PI4 OVERLAYFS — CRITICAL

The Pi4 SD card is read-only. ALL SSH writes go to RAM and are wiped on reboot.

**Real SD mount:** `/media/root-ro/`
**RAM overlay (wiped on boot):** `/` (apparent root)

**Rule: After every file edit via SSH, run:**
```bash
cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
```

**For root-owned files:**
```bash
sudo python3 -c "open('/media/root-ro/path/file','w').write(open('/path/file').read())"
```

**Verify RAM == SD:**
```bash
md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
```

**pip installs also go to RAM.** After any pip install, persist with:
```bash
sudo cp -r /home/pi/.local /media/root-ro/home/pi/
```

---

## 3. ALL MODIFIED FILES

### Pi4 (192.168.1.200)

| File | SD Path | Purpose |
|------|---------|---------|
| `/home/pi/assistant.py` | `/media/root-ro/home/pi/assistant.py` | Main voice pipeline — all config, ElevenLabs TTS, vision, emotion, LEDs |
| `/usr/local/bin/alsa-init.sh` | `/media/root-ro/usr/local/bin/alsa-init.sh` | Sets ALSA volumes at boot: Speaker=127, Headphone=127, Capture=48 |
| `/etc/systemd/system/assistant.service` | `/media/root-ro/etc/systemd/system/assistant.service` | Auto-starts Jarvis on boot, after alsa-init.service |
| `/home/pi/.local/lib/python3.13/site-packages/` | `/media/root-ro/home/pi/.local/...` | pip packages: miniaudio, audioop-lts, cffi (persisted via cp -r) |

### GandalfAI (192.168.1.3) — Windows, no overlayfs

| File | Path | Purpose |
|------|------|---------|
| `jarvis_modelfile.txt` | `C:\Users\gandalf\jarvis_modelfile.txt` | Modelfile for jarvis model. Base: gemma3:27b. Jarvis personality + emotion tags. |
| `jarvis-kids_modelfile.txt` | `C:\Users\gandalf\jarvis-kids_modelfile.txt` | Modelfile for jarvis-kids. Same base, playful/silly tone, kids safety. |

### Desktop PC (PlatformIO project)

Project root: `C:\Users\SuperMaster\Documents\PlatformIO\TeensyEyes-4.0-PrsnSnsrSrvoRdDisp-AI\`

| File | Relative Path | Purpose |
|------|---------------|---------|
| `config.h` | `src/config.h` | Eye definitions array: index 0=nordicBlue, index 1=flame. Display pin assignments. |
| `main.cpp` | `src/main.cpp` | Full Teensy firmware. Serial protocol, emotion→eye mapping, ANGRY flame swap (9s auto-revert), tracking lockout. |
| `servo_teensy.ino` | `servo_teensy/servo_teensy.ino` | Pico pan servo sketch. NOT YET DEPLOYED to Pico. |
| `platformio.ini` | `platformio.ini` | Build config: board=teensy40, C++17 |

---

## 4. ASSISTANT.PY KEY CONFIG VALUES

All on lines 20–80 of `/home/pi/assistant.py`:

```python
# Network
GANDALF        = "192.168.1.3"
WHISPER_PORT   = 10300
PIPER_PORT     = 10200
OLLAMA_PORT    = 11434

# Models
OLLAMA_MODEL_ADULT = "jarvis"       # gemma3:27b base
OLLAMA_MODEL_KIDS  = "jarvis-kids"  # gemma3:27b base, kids personality
VISION_MODEL   = "jarvis"           # SAME model -- single model approach

# ElevenLabs TTS
ELEVENLABS_API_KEY  = "sk_752184d377335347d38c185ba56a1bebe9deba4da50ce082"
ELEVENLABS_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"   # Daniel (free tier)
                                                 # Upgrade: "1TE7ou3jyxHsyRehUuMB" (Eastend Steve, paid)
ELEVENLABS_MODEL    = "eleven_turbo_v2_5"
ELEVENLABS_ENABLED  = True

# Audio
RECORD_SECONDS      = 6
SILENCE_SECS        = 1.5
SILENCE_RMS         = 300
KIDS_RECORD_SECONDS = 14    # extended for kids speech
KIDS_SILENCE_SECS   = 3.5
KIDS_SILENCE_RMS    = 150
KIDS_FOLLOWUP_TIMEOUT = 15

# Hardware
TEENSY_PORT    = "/dev/ttyACM0"
TEENSY_BAUD    = 115200
BUTTON_PIN     = 17
NUM_LEDS       = 3

# Context
CONTEXT_TIMEOUT_SECS = 300
```

---

## 5. ELEVENLABS TTS ARCHITECTURE

Free tier always returns MP3 regardless of output_format parameter.
Pipeline: ElevenLabs API → MP3 bytes → miniaudio.decode() → s16le PCM @ 22050Hz → 4x gain boost → pyaudio stereo playback.
Fallback: if ElevenLabs fails for any reason, automatically falls back to Piper TTS.

**To change voice:** Edit ELEVENLABS_VOICE_ID in assistant.py, cp to SD, restart.
**To disable ElevenLabs:** Set ELEVENLABS_ENABLED = False.
**To adjust volume:** Change multiplier on line ~583: `* 4` (current). Try 5 if too quiet, 3 if distorting.

pip dependencies (must be persisted to SD):
- `miniaudio` -- MP3 decode
- `audioop-lts` -- Python 3.13 audioop replacement

---

## 6. VISION ARCHITECTURE

**Single model:** Both chat and vision use `jarvis` (gemma3:27b). This avoids VRAM conflict.
- gemma3:27b VRAM: ~20GB with vision active, 4.2GB free on RTX 3090
- qwen3.5:27b was rejected: ~23GB, only 75MB free, OOM on vision

Vision triggers (phrases in VISION_TRIGGERS set): "what is this", "what do you see", "look at this", etc.
Pipeline: trigger detected → rpicam-still capture → base64 encode → Ollama /api/generate with image → strip [EMOTION:X] tag → TTS.

First vision call after cold boot: ~20-30s (model loading). Subsequent calls: ~3s.

---

## 7. EMOTION SYSTEM

LLM always prepends `[EMOTION:X]` on first line of response.
`extract_emotion_from_reply()` strips it before TTS.
`emit_emotion(teensy, leds, emotion)` sends to both Teensy serial AND APA102 LEDs simultaneously.

| Emotion | Eye style | LED color | Breath rate |
|---------|-----------|-----------|-------------|
| NEUTRAL | nordicBlue | Soft cyan | 4s |
| HAPPY | nordicBlue | Warm yellow | 3s |
| CURIOUS | nordicBlue | Bright cyan | 3.5s |
| ANGRY | **flame** (9s then reverts) | Red | 2s fast |
| SLEEPY | nordicBlue | Dim purple | 6s slow |
| SURPRISED | nordicBlue | White flash→cyan | Flash |
| SAD | nordicBlue | Dim blue | 6s slow |

---

## 8. TEENSY FIRMWARE STATUS

**Code is complete and correct on disk. NOT yet flashed.**

config.h: nordicBlue default, flame for ANGRY (index 0 and 1 in eyeDefinitions array).
main.cpp: ANGRY triggers setEyeDefinition(EYE_IDX_ANGRY), 9s timer then auto-reverts. Fix applied: uses eyeDefinitions[idx] not .at(idx) to avoid dangling pointer.

**To flash:**
1. Connect Teensy 4.0 via USB to desktop PC
2. Open PlatformIO in VS Code
3. Project: `C:\Users\SuperMaster\Documents\PlatformIO\TeensyEyes-4.0-PrsnSnsrSrvoRdDisp-AI\`
4. Click Upload (right arrow) — full compile takes several minutes due to pixel data
5. Watch for SUCCESS in terminal

**To test after flash:**
Open PlatformIO Serial Monitor at 115200 baud, set line ending to Newline, type: `EMOTION:ANGRY`
Eyes should switch to flame immediately, revert after 9s.

---

## 9. OLLAMA MODELS ON GANDALF

Active models:
- `jarvis` — gemma3:27b base, adult personality + emotion tags + vision support
- `jarvis-kids` — gemma3:27b base, kids personality

Modelfile source files: `C:\Users\gandalf\jarvis_modelfile.txt` and `jarvis-kids_modelfile.txt`

**To rebuild after editing modelfile:**
```
ollama create jarvis -f "C:\Users\gandalf\jarvis_modelfile.txt"
ollama create jarvis-kids -f "C:\Users\gandalf\jarvis-kids_modelfile.txt"
```

VRAM budget: gemma3:27b = ~20GB, RTX 3090 = 24GB, 4.2GB free = vision fits.
DO NOT switch to qwen3.5:27b for primary model -- it uses 23GB and vision OOMs.
qwen3.5:27b is available on disk if needed for text-only chat.

---

## 10. ALSA VOLUME BOOT CHAIN

1. `alsa-init.service` runs `alsa-init.sh` 8s after sound.target
2. `alsa-init.sh` sets: Capture=48, Headphone=127, Speaker=127
3. `assistant.service` starts after alsa-init.service (no volume override)

Old broken state: assistant.service had ExecStartPre setting Speaker=110 — THIS HAS BEEN REMOVED.
If volume drops after reboot, check assistant.service for rogue ExecStartPre lines.

---

## 11. PENDING ITEMS

| Priority | Item | Notes |
|----------|------|-------|
| 1 | Flash Teensy with eye-swap firmware | Code done, just needs PlatformIO upload |
| 2 | Deploy Pico servo sketch | servo_teensy.ino ready, Arduino IDE upload to Pico |
| 3 | Upgrade ElevenLabs to Starter ($5/mo) | Change ELEVENLABS_VOICE_ID to 1TE7ou3jyxHsyRehUuMB (Eastend Steve) |
| 4 | Eye friendliness fix | Reduce upper eyelid droop in nordicBlue config.eye (JSON, no recompile) |
| 5 | Physical base redesign | Lightburn layout, caliper measurements needed |
| 6 | Update SNAPSHOT after next session | Save to SNAPSHOT_2026-03-21b.md or new date |

---

## 12. QUICK REFERENCE SSH COMMANDS

**Pi4:**
```bash
# Restart Jarvis
pkill -f assistant.py; sleep 1; nohup python3 -u /home/pi/assistant.py > /dev/null 2>&1 < /dev/null &

# Persist assistant.py to SD
cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py

# Verify persisted
md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py

# Persist pip packages to SD
sudo cp -r /home/pi/.local /media/root-ro/home/pi/

# Check ALSA levels
amixer -c 0 sget Speaker && amixer -c 0 sget Headphone

# Set ALSA max NOW (RAM only, resets on reboot)
amixer -c 0 sset Speaker 127 && amixer -c 0 sset Headphone 127

# Check Jarvis running
pgrep -fa python3 | grep assistant

# View live logs
journalctl -u assistant -f
```

**GandalfAI:**
```bash
# Check VRAM
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader

# Check loaded model
ollama ps

# Rebuild jarvis
ollama create jarvis -f "C:\Users\gandalf\jarvis_modelfile.txt"

# Rebuild jarvis-kids
ollama create jarvis-kids -f "C:\Users\gandalf\jarvis-kids_modelfile.txt"
```
