# IRIS Robot Face — Chat Session Snapshot
**Date:** 2026-03-24
**For use in:** Claude Desktop Chat tab

Paste this entire document at the start of a new Chat session to restore full context.

---

## HOW TO RESUME
Paste this snapshot and say: "Read this snapshot and continue IRIS development from where we left off."

---

## 1. PROJECT IDENTITY

**Project:** IRIS -- AI Robot Face
**Status:** Fully operational as of 2026-03-22b
**GitHub:** https://github.com/Maestro8484/IRIS-Robot-Face (private)
**Local path:** `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face`
**Git branch:** `iris-ai-integration`
**Push command:** `git push origin HEAD`

---

## 2. SYSTEM ARCHITECTURE

| System | IP | Credentials | Role |
|---|---|---|---|
| Pi4 (IRIS voice) | 192.168.1.200 | pi / ohs | Voice pipeline, LEDs, camera, Teensy serial |
| GandalfAI | 192.168.1.3 | gandalf / 5309 | Ollama LLM, Whisper STT, Piper TTS, RTX 3090 |
| Desktop PC | 192.168.1.103 | SuperMaster | PlatformIO Teensy firmware, VS Code, Claude Desktop |
| Teensy 4.0 | USB → /dev/ttyACM0 | N/A | Eye displays, emotion rendering |

**Claude Desktop MCP filesystem scope:** `C:\Users\SuperMaster`
**SSH tools:** ssh-pi4 (Pi4 192.168.1.200), ssh-gandalf (GandalfAI 192.168.1.3)

---

## 3. PI4 OVERLAYFS -- CRITICAL

SD card is read-only. ALL SSH writes go to RAM -- wiped on reboot unless persisted.

**Persist any file:**
```bash
sudo mount -o remount,rw /media/root-ro
cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
```

---

## 4. KEY FILES

### Pi4 (192.168.1.200)
| File | SD Path | Purpose |
|---|---|---|
| `/home/pi/assistant.py` | `/media/root-ro/home/pi/assistant.py` | Main voice pipeline |
| `/usr/local/bin/alsa-init.sh` | same under root-ro | ALSA volumes at boot |
| `/etc/systemd/system/assistant.service` | same under root-ro | Auto-starts on boot |

### GandalfAI (192.168.1.3)
| File | Path | Purpose |
|---|---|---|
| `jarvis_modelfile.txt` | `C:\Users\gandalf\jarvis_modelfile.txt` | jarvis model (gemma3:27b) |
| `jarvis-kids_modelfile.txt` | `C:\Users\gandalf\jarvis-kids_modelfile.txt` | kids model |

### Desktop PC
| File | Path | Purpose |
|---|---|---|
| `main.cpp` | `IRIS-Robot-Face\src\main.cpp` | Teensy firmware |
| `config.h` | `IRIS-Robot-Face\src\config.h` | Eye definitions, display pins |
| `GC9A01A_Display.h` | `IRIS-Robot-Face\src\displays\GC9A01A_Display.h` | fillBlack async fix |
| `caption_burner.py` | `C:\Users\SuperMaster\caption_burner.py` | YouTube caption pipeline |

---

## 5. ASSISTANT.PY KEY CONFIG

```python
GANDALF             = "192.168.1.3"
ELEVENLABS_API_KEY  = "sk_752184d377335347d38c185ba56a1bebe9deba4da50ce082"
ELEVENLABS_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"   # Daniel legacy
ELEVENLABS_MODEL    = "eleven_turbo_v2_5"
ELEVENLABS_ENABLED  = True
OLLAMA_MODEL_ADULT  = "jarvis"
OLLAMA_MODEL_KIDS   = "jarvis-kids"
VISION_MODEL        = "jarvis"
WAKE_WORD           = "hey_jarvis"
OWW_THRESHOLD       = 0.7
TEENSY_PORT         = "/dev/ttyACM0"
TEENSY_BAUD         = 115200
BUTTON_PIN          = 17
```

---

## 6. AUDIO ARCHITECTURE

```
LLM -> ElevenLabs/Piper TTS -> play_pcm() 3.0x gain -> wm8960 HAT -> 3.5mm -> PAM8403 amp -> 2x 3W speakers
```
- ElevenLabs: MP3 -> miniaudio decode -> play_pcm()
- Piper: raw PCM -> play_pcm()
- ALSA: Speaker=120, HP=120, DC/AC=5
- pyaudio device index: 6 (default). DO NOT use index 0.
- Beep rate: 44100Hz. Pop fix: 80ms silence padding on ElevenLabs output.

---

## 7. TEENSY FIRMWARE STATUS

Flashed and working. fillBlack async fix deployed.

**Serial commands (115200 baud):**
- `EMOTION:ANGRY` → flame eyes, 9s auto-revert
- `EMOTION:HAPPY/CURIOUS/SLEEPY/SURPRISED/SAD/NEUTRAL` → eye params change
- `EYES:SLEEP` → both displays black, rendering halted
- `EYES:WAKE` → restore nordicBlue, resume rendering
- Teensy → Pi4: `FACE:1` (locked), `FACE:0` (lost)

**Eye definitions:**
- Index 0: nordicBlue (default)
- Index 1: flame (ANGRY)

---

## 8. EMOTION SYSTEM

LLM prepends `[EMOTION:X]` → stripped before TTS → drives Teensy serial + APA102 LEDs.

| Emotion | LED color | Period |
|---|---|---|
| NEUTRAL | Cyan breathe | 5.0s |
| HAPPY | Warm yellow | 3.0s |
| CURIOUS | Bright cyan | 3.5s |
| ANGRY | Red | 2.0s |
| SLEEPY | Dim purple | 6.0s |
| SURPRISED | White flash | 0.3s |
| SAD | Dim blue | 6.0s |

LED breathing: `floor=3, peak=65, period=5.0s`, gamma 1.8

---

## 9. PENDING ITEMS

| Priority | Item | Notes |
|---|---|---|
| 1 | New ElevenLabs British voice | Daniel legacy still works. Filter: British, Male, conversational, snarky |
| 2 | Eye eyelid droop fix | Reduce upper eyelid droop in nordicBlue config.eye (JSON edit, no recompile) |
| 3 | Pico servo deploy | Physical pan servo not yet wired to Pico |
| 4 | Physical base redesign | Lightburn layout, caliper measurements needed |
| 5 | Teensy reflash | fillBlack async fix confirmed but verify on latest build |

---

## 10. QUICK REFERENCE

**Restart Jarvis:**
```bash
pkill -f assistant.py; sleep 1; nohup python3 -u /home/pi/assistant.py > /dev/null 2>&1 < /dev/null &
```

**Persist assistant.py:**
```bash
sudo mount -o remount,rw /media/root-ro && cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py && sudo mount -o remount,ro /media/root-ro && md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
```

**Live log:**
```bash
journalctl -u assistant -f | grep -v "ALSA\|Jack\|pulse\|seeed\|pcm\|conf\|hdmi\|usb\|modem\|JackShm\|server"
```

**GandalfAI VRAM:**
```bash
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
```

**Rebuild Ollama models:**
```
ollama create jarvis -f "C:\Users\gandalf\jarvis_modelfile.txt"
ollama create jarvis-kids -f "C:\Users\gandalf\jarvis-kids_modelfile.txt"
```

**Git commit and push:**
```powershell
cd "C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face"
git add -A
git commit -m "describe what changed"
git push origin HEAD
```

---

## 11. GITHUB / CONTENT

- GitHub: https://github.com/Maestro8484 (profile README live)
- YouTube: https://www.youtube.com/@schm3116
- Content strategy: every project milestone documented for Reddit/Hackster/YouTube
- IRIS-Robot-Face repo: private for now, go public when ready to post

---

## 12. HOME LAB NETWORK

| Host | IP | Credentials |
|---|---|---|
| GandalfAI | 192.168.1.3 | gandalf/5309 |
| Pi4 IRIS/Jarvis | 192.168.1.200 | pi/ohs |
| Pi5 Batocera | 192.168.1.67 | root/linux |
| Proxmox | 192.168.1.5 | root |
| Home Assistant | 192.168.1.22 | root/ohs |
| Synology NAS | 192.168.1.102 | -- |
| Desktop PC | 192.168.1.103 | SuperMaster |
