# IRIS Robot Face — Project Snapshot
**Date:** 2026-03-22b (late session)
**Status:** Fully operational. ElevenLabs upgraded to Starter. Teensy flashed with eye-swap + EYES:SLEEP/WAKE. PAM8403 amp installed. Volume working. LED breathing tuned. Date injection working.

---

## HOW TO RESUME IN A NEW CHAT
Say: "Read the project snapshot at `C:\Users\SuperMaster\Documents\PlatformIO\TeensyEyes-4.0-PrsnSnsrSrvoRdDisp-AI\SNAPSHOT_2026-03-22b.md` and continue from where we left off."

---

## 1. SYSTEM ARCHITECTURE

| System | IP | Credentials | Role |
|--------|----|-------------|------|
| Pi4 (Jarvis / IRIS) | 192.168.1.200 | pi / ohs | Voice pipeline, LEDs, camera, Teensy serial |
| GandalfAI | 192.168.1.3 | gandalf / 5309 | Ollama LLM, Whisper STT, Piper TTS |
| Desktop PC | 192.168.1.103 | SuperMaster | PlatformIO Teensy firmware, caption_burner.py |
| Teensy 4.0 | USB → /dev/ttyACM0 | N/A | Eye displays, emotion rendering |

Claude Desktop MCP runs on a separate laptop but filesystem MCP is scoped to Desktop PC (192.168.1.103) at C:\Users\SuperMaster\.

---

## 2. PI4 OVERLAYFS — CRITICAL

SD card is read-only. ALL SSH writes go to RAM and wiped on reboot.

**Real SD mount:** `/media/root-ro/`
**RAM overlay (wiped on boot):** `/` (apparent root)

**Persist any file change:**
```bash
sudo mount -o remount,rw /media/root-ro
cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
```

**Persist ALSA state:**
```bash
sudo /usr/sbin/alsactl store
sudo mount -o remount,rw /media/root-ro
sudo cp /var/lib/alsa/asound.state /media/root-ro/var/lib/alsa/asound.state
sudo mount -o remount,ro /media/root-ro
```

---

## 3. ALL MODIFIED FILES

### Pi4 (192.168.1.200)

| File | SD Path | Purpose |
|------|---------|---------|
| `/home/pi/assistant.py` | `/media/root-ro/home/pi/assistant.py` | Main voice pipeline |
| `/usr/local/bin/alsa-init.sh` | `/media/root-ro/usr/local/bin/alsa-init.sh` | ALSA volumes at boot: Speaker=120, HP=120, DC/AC=5 |
| `/var/lib/alsa/asound.state` | `/media/root-ro/var/lib/alsa/asound.state` | Saved ALSA state restored by alsa-restore.service |
| `/etc/systemd/system/assistant.service` | `/media/root-ro/etc/systemd/system/assistant.service` | Auto-starts Jarvis on boot |

### GandalfAI (192.168.1.3) — Windows

| File | Path | Purpose |
|------|------|---------|
| `jarvis_modelfile.txt` | `C:\Users\gandalf\jarvis_modelfile.txt` | jarvis model -- gemma3:27b base, adult personality |
| `jarvis-kids_modelfile.txt` | `C:\Users\gandalf\jarvis-kids_modelfile.txt` | jarvis-kids -- kids personality, reciprocal |

### Desktop PC (PlatformIO)

Project root: `C:\Users\SuperMaster\Documents\PlatformIO\TeensyEyes-4.0-PrsnSnsrSrvoRdDisp-AI\`

| File | Relative Path | Purpose |
|------|---------------|---------|
| `main.cpp` | `src\main.cpp` | Teensy firmware -- emotions, ANGRY flame, EYES:SLEEP/WAKE |
| `config.h` | `src\config.h` | Eye definitions, display pins, global displayLeft/displayRight pointers |
| `GC9A01A_Display.h` | `src\displays\GC9A01A_Display.h` | fillBlack() -- waits for async transfer before blanking |
| `caption_burner.py` | `C:\Users\SuperMaster\caption_burner.py` | Auto-caption pipeline for YouTube |
| `caption_burner.bat` | `C:\Users\SuperMaster\caption_burner.bat` | Drag-and-drop wrapper (py -3.11, NVENC) |

---

## 4. ASSISTANT.PY KEY CONFIG VALUES

```python
GANDALF             = "192.168.1.3"
WHISPER_PORT        = 10300
PIPER_PORT          = 10200
OLLAMA_PORT         = 11434
OWW_PORT            = 10400
OLLAMA_MODEL_ADULT  = "jarvis"
OLLAMA_MODEL_KIDS   = "jarvis-kids"
VISION_MODEL        = "jarvis"
WAKE_WORD           = "hey_jarvis"
OWW_THRESHOLD       = 0.7

# ElevenLabs -- Starter tier ($5/mo), 30k chars/month
ELEVENLABS_API_KEY  = "sk_752184d377335347d38c185ba56a1bebe9deba4da50ce082"
ELEVENLABS_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"   # Daniel legacy -- not in UI but works via API
                                                 # Eastend Steve backup: "1TE7ou3jyxHsyRehUuMB"
ELEVENLABS_MODEL    = "eleven_turbo_v2_5"
ELEVENLABS_ENABLED  = True

RECORD_SECONDS          = 6
SILENCE_SECS            = 1.5
SILENCE_RMS             = 300
KIDS_RECORD_SECONDS     = 14
KIDS_SILENCE_SECS       = 3.5
KIDS_SILENCE_RMS        = 150
KIDS_FOLLOWUP_TIMEOUT   = 15
CONTEXT_TIMEOUT_SECS    = 300

TEENSY_PORT  = "/dev/ttyACM0"
TEENSY_BAUD  = 115200
BUTTON_PIN   = 17
NUM_LEDS     = 3
```

---

## 5. AUDIO ARCHITECTURE

**Signal chain:**
```
LLM → ElevenLabs/Piper TTS → play_pcm() 3.0x central gain → wm8960 HAT → 3.5mm jack → PAM8403 amp (knob at max) → 2x 3W speakers
```

**Central gain:** `* 3.0` in `play_pcm()` -- applies equally to ALL TTS sources (ElevenLabs + Piper).
**ElevenLabs:** MP3 → miniaudio decode → unity gain → play_pcm()
**Piper:** Raw PCM → play_pcm()

**ALSA levels (persisted to SD):**
- Speaker: 120/127 (-1dB)
- Headphone: 120/127 (-1dB)
- Speaker DC Volume: 5/5
- Speaker AC Volume: 5/5

**PAM8403 amp:** Installed. Knob at max. Hardware volume ceiling reached.
If more volume needed: upgrade to TPA3116 (15W/ch).

**pyaudio device:** Default device index 6 -- handles all sample rates.
DO NOT use output_device_index=0 (wm8960 hw direct only supports 16kHz).

**Beep/double-beep rate:** 44100Hz.
**Pop fix:** 80ms silence padding prepended/appended to ElevenLabs PCM output.

---

## 6. ELEVENLABS STATUS

- **Tier:** Starter ($5/mo) -- 30k chars/month
- **Voice:** Daniel `onwK4e9ZLuTAKqWW03F9` -- legacy, not visible in UI, works via API
- **Pending:** Find replacement snarky British male voice
  - Filter on elevenlabs.io: British, Male, Middle-aged, Conversational
  - Test phrase: *"Well, I suppose I could help you with that -- though I suspect you already know the answer and simply enjoy the company."*
- **To swap voice ID on Pi:**
```bash
python3 - << 'PYEOF'
with open('/home/pi/assistant.py', 'r') as f: src = f.read()
src = src.replace('ELEVENLABS_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"', 'ELEVENLABS_VOICE_ID = "NEW_ID_HERE"')
with open('/home/pi/assistant.py', 'w') as f: f.write(src)
print("OK")
PYEOF
```
Then persist + restart as usual.

---

## 7. TEENSY FIRMWARE STATUS

**Status:** Flashed and working. fillBlack async fix confirmed deployed and reflashed.
- EMOTION:X commands → eye parameter changes
- ANGRY → flame eyes, 9s auto-revert
- EYES:SLEEP → both displays black, renderFrame halted
- EYES:WAKE → restore nordicBlue, resume rendering

**Eye sleep voice triggers:**
- Sleep: "turn off eyes", "close eyes", "eyes off", "turn off your eyes", "sleep eyes", etc.
- Wake: "turn on eyes", "open eyes", "eyes on", "wake eyes", etc.
- Auto-wake: any other voice interaction wakes eyes if sleeping

**Serial test (115200 baud, Newline):**
```
EMOTION:ANGRY    → flame eyes, 9s revert
EYES:SLEEP       → black screens
EYES:WAKE        → restore nordicBlue
```

---

## 8. KIDS MODE

- Toggle: "kids mode on" / "kids mode off"
- LED: yellow breathe (kids), cyan breathe (adult)
- Model: jarvis-kids (gemma3:27b, reciprocal conversation, encouraging, simpler)
- Extended recording/silence thresholds (14s record, 3.5s silence)
- Context history cleared on mode switch

---

## 9. EMOTION SYSTEM

LLM prepends `[EMOTION:X]` → stripped before TTS → drives Teensy serial + APA102 LEDs simultaneously.

| Emotion | Eye style | LED color | Period |
|---------|-----------|-----------|--------|
| NEUTRAL | nordicBlue | Cyan breathe | 5.0s |
| HAPPY | nordicBlue | Warm yellow | 3.0s |
| CURIOUS | nordicBlue | Bright cyan | 3.5s |
| ANGRY | flame (9s revert) | Red | 2.0s |
| SLEEPY | nordicBlue | Dim purple | 6.0s |
| SURPRISED | nordicBlue | White flash | 0.3s |
| SAD | nordicBlue | Dim blue | 6.0s |

**LED breathing (tuned):**
- Sine curve: `floor=3, peak=65, period=5.0s`, gamma exponent 1.8
- Never fully dark -- breathes between dim floor and soft peak
- Kids mode: `floor=3, peak=62, period=4.0s`

---

## 10. DATE/TIME INJECTION

Real date/time injected as system message on every Ollama call:
```python
date_inject = {
    "role": "system",
    "content": f"Current date and time: {now.strftime('%A, %B %d %Y, %I:%M %p')} (Mountain Time)."
}
messages_with_date = [date_inject] + conversation_history
```
Fixes LLM hallucinating training-data dates.

---

## 11. VISION

Single model `jarvis` (gemma3:27b) handles both chat and vision.
- VRAM: ~20GB active, 4.2GB free on RTX 3090
- Pipeline: voice trigger → rpicam-still → base64 → Ollama /api/generate with image → strip emotion tag → TTS
- Cold boot first call: ~20-30s. Subsequent: ~3s
- DO NOT use qwen3.5:27b -- 23GB VRAM, OOMs on vision

---

## 12. CAPTION BURNER (Desktop PC)

| File | Path |
|------|------|
| Script | `C:\Users\SuperMaster\caption_burner.py` |
| Launcher | `C:\Users\SuperMaster\caption_burner.bat` |

- Runtime: Python 3.11 (`py -3.11`), spaCy en_core_web_sm, openai-whisper, ffmpeg
- Pipeline: Whisper CUDA (RTX 3060) → spaCy noun/verb highlight → ASS subtitles → ffmpeg NVENC burn
- Config: `FONT_SIZE=60, OUTLINE_WIDTH=3, MARGIN_BOTTOM=80, MAX_LINE_CHARS=60, FFMPEG_THREADS=4`
- Usage: drag .mp4/.mov/.mkv onto caption_burner.bat

---

## 13. PENDING ITEMS

| Priority | Item | Notes |
|----------|------|-------|
| 1 | Find new ElevenLabs British voice | Daniel legacy still works. Filter: British, Male, conversational, snarky |
| 2 | Eye eyelid droop fix | Reduce upper eyelid droop in nordicBlue config.eye (JSON edit, no recompile) |
| 3 | Physical base redesign | Lightburn layout, caliper measurements needed |
| 4 | TPA3116 amp upgrade | PAM8403 at hardware ceiling -- TPA3116 15W/ch if more volume needed |

---

## 14. QUICK REFERENCE

**Restart Jarvis:**
```bash
pkill -f assistant.py; sleep 1; nohup python3 -u /home/pi/assistant.py > /dev/null 2>&1 < /dev/null &
```

**Persist assistant.py to SD:**
```bash
sudo mount -o remount,rw /media/root-ro && cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py && sudo mount -o remount,ro /media/root-ro && md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
```

**Live log (clean):**
```bash
journalctl -u assistant -f | grep -v "ALSA\|Jack\|pulse\|seeed\|pcm\|conf\|hdmi\|usb\|modem\|JackShm\|server"
```

**Check ALSA:**
```bash
amixer -c 0 sget Speaker && amixer -c 0 sget Headphone
```

**GandalfAI VRAM:**
```bash
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
```

**Rebuild Ollama models (on GandalfAI):**
```
ollama create jarvis -f "C:\Users\gandalf\jarvis_modelfile.txt"
ollama create jarvis-kids -f "C:\Users\gandalf\jarvis-kids_modelfile.txt"
```

**Available wakeword models on Pi:**
- hey_jarvis (current), computer_v2, alexa, hey_mycroft, hey_rhasspy, okay_nabu, hey_marvin
- To switch: change WAKE_WORD in assistant.py + update --preload-model arg in oww subprocess call

**Wakeword sensitivity:** OWW_THRESHOLD = 0.7 (lower = more sensitive, higher = stricter)
