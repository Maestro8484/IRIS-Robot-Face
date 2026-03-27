# IRIS — Local AI Robot Face

> Fully local interactive AI robot face. Voice-activated, emotion-driven,
> runs entirely on your LAN. No cloud required except optional ElevenLabs TTS.

---

## What Is IRIS?

IRIS is a conversational AI robot face built from scratch on a Raspberry Pi 4
and Teensy 4.0. It listens for a wake word, processes speech, queries a local
LLM, speaks a response, and animates its eyes and mouth in real time based on
the detected emotion -- all within a few seconds on consumer hardware.

Two conversation modes: **adult** (snarky British personality) and **kids**
(encouraging, patient, age-appropriate). Switch by voice. Full context history
per session. Camera input for visual Q&A. Deep space sleep display at night.

---

## Demo

> *(video + photos -- add when ready)*

---

## Feature Overview

| Feature | Details |
|---|---|
| Wake word | `hey_jarvis` via OpenWakeWord |
| Speech-to-text | Wyoming Whisper (GPU-accelerated, RTX 3090) |
| LLM | Ollama `gemma3:27b` -- fully local, no data leaves LAN |
| TTS | ElevenLabs Starter + Piper local fallback |
| Eyes | Dual 1.28" round GC9A01A TFTs, 9 eye styles, Teensy 4.0 |
| Mouth | MAX7219 32x8 LED matrix, 9 expressions + snore animation |
| Emotion system | LLM tags drive eyes, mouth, and LEDs simultaneously |
| Face tracking | I2C Person Sensor -- eyes follow detected faces |
| Vision | Camera snapshot sent to LLM for visual Q&A |
| Kids mode | Separate LLM personality, extended recording thresholds |
| Sleep mode | Deep space TFT display + snore mouth animation 9PM-7:30AM |
| Wake-on-LAN | GandalfAI auto-wakes when wakeword fires during sleep |
| Web UI | Full config + diagnostic panel at http://[pi4]:5000 |
| Interruptible TTS | Stop phrase kills playback mid-sentence |

---

## Hardware

| Component | Details |
|---|---|
| Raspberry Pi 4 | Voice pipeline, LEDs, camera, Teensy serial bridge |
| Teensy 4.0 | Dual GC9A01A eyes + MAX7219 mouth matrix |
| ReSpeaker 2-Mic Pi HAT | Dual mic, WM8960 codec, 3x APA102 LEDs |
| GC9A01A displays x2 | 1.28" round 240x240 TFT -- animated eyes |
| MAX7219 32x8 LED matrix | 4-module chained mouth display |
| APA102 LEDs x3 | Emotion status indicator |
| Person Sensor (I2C) | Face detection and tracking |
| Arducam IMX708 | Vision input for camera queries |
| PAM8403 amp | Audio output to 2x 3W speakers |
| GandalfAI (Windows PC) | RTX 3090 -- Ollama, Whisper, Piper |

---

## Eye System

Built on [chrismiller's TeensyEyes](https://github.com/chrismiller/TeensyEyes)
for Teensy 4.x with GC9A01A displays. 9 eye definitions compiled in,
switchable at runtime via serial command or web UI.

| Index | Name | Trigger |
|---|---|---|
| 0 | nordicBlue | Default idle |
| 1 | flame | ANGRY emotion (auto-reverts 9s) |
| 2 | hypnoRed | CONFUSED emotion (auto-reverts 7s) |
| 3 | hazel | Web UI / EYE:3 |
| 4 | blueFlame1 | Web UI / EYE:4 |
| 5 | leopard | Web UI / EYE:5 |
| 6 | snake | Web UI / EYE:6 |
| 7 | dragon | Web UI / EYE:7 |
| 8 | bigBlue | Web UI / EYE:8 |

Eye parameters (pupil size, blink rate, gaze speed) adjust per detected
emotion. Face tracking via Person Sensor is always active -- eyes follow the
largest detected face, auto-wander when no face present.

---

## Mouth Matrix

MAX7219 32x8 LED matrix (4-module chained PCB) driven by Teensy 4.0 via
bit-bang SPI (pins 5/6/7). 9 static expression bitmaps mapped to the emotion
system, plus a slow animated snore pattern during sleep mode.

| Index | Expression | Emotion |
|---|---|---|
| 0 | Flat line | NEUTRAL |
| 1 | Wide smile | HAPPY |
| 2 | Diagonal smirk | CURIOUS |
| 3 | Frown | ANGRY |
| 4 | Right droop | SLEEPY |
| 5 | Oval | SURPRISED |
| 6 | Downturn | SAD |
| 7 | Zigzag | CONFUSED |
| 8 | Off | SLEEP |

---

## Emotion System

The LLM prepends `[EMOTION:X]` to every response. The Pi4 strips the tag
before TTS and uses it to simultaneously drive:

- Teensy eye parameters (pupil ratio, blink, gaze speed)
- Teensy eye swap (flame for ANGRY, hypnoRed for CONFUSED)
- MAX7219 mouth expression
- APA102 LED color and breathing animation

| Emotion | Eyes | LED | Mouth |
|---|---|---|---|
| NEUTRAL | nordicBlue, pupil 0.40 | Cyan breathe 5s | Flat line |
| HAPPY | nordicBlue, pupil 0.75, blink | Warm yellow 3s | Wide smile |
| CURIOUS | nordicBlue, pupil 0.60 | Bright cyan 3.5s | Diagonal smirk |
| ANGRY | flame 9s, pupil 0.15 | Red 2s | Frown |
| SLEEPY | nordicBlue, pupil 0.85, blink | Dim purple 6s | Right droop |
| SURPRISED | nordicBlue, pupil 0.95, blink | White flash 0.3s | Oval |
| SAD | nordicBlue, pupil 0.25, blink | Dim blue 6s | Downturn |
| CONFUSED | hypnoRed 7s, pupil 0.70 | Magenta 2.5s | Zigzag |

---

## LLM Models

Two Ollama modelfiles in `/ollama/`, both running `gemma3:27b`:

**`jarvis` (adult mode)**
Snarky British personality. Concise spoken answers, 3 sentences max, no
markdown. Reciprocal conversational tone. Emits `[EMOTION:X]` tags. Real-time
date/time injected as system message on every call.

**`jarvis-kids` (kids mode)**
Encouraging, patient, age-appropriate vocabulary. Reciprocal and engaging for
children. Extended recording/silence thresholds (14s record, 3.5s silence).
APA102 shows yellow breathe while active.

Switch by voice: *"kids mode on"* / *"kids mode off"*
Context history clears on mode switch.

---

## Sleep Mode

**9:00 PM (cron)** -- IRIS enters sleep:
- Both TFT displays render a deep space scene: crescent moon with slow drift,
  3-depth star field with twinkling, nebula color washes, expanding pulse rings,
  shooting stars, drifting ZZZ chain
- MAX7219 mouth plays 12s snore animation at minimum brightness
  (inhale -- flat line brightens, hold, exhale -- sine wave rolls left to right)
- APA102 breathes dim indigo
- Wakeword listener stays active -- `hey_jarvis` wakes GandalfAI via
  Wake-on-LAN and resumes full assistant mode

**7:30 AM (cron)** -- Full assistant resumes automatically.

---

## Voice Pipeline
```
hey_jarvis  (OpenWakeWord, port 10400)
  → Wake-on-LAN to GandalfAI if sleeping  (MAC: A4:BB:6D:CA:83:20)
  → Wyoming Whisper STT  (port 10300)
  → Person Sensor recognition  (background thread, cooldown 300s)
  → Ollama gemma3:27b  (port 11434) -- jarvis or jarvis-kids
  → Strip [EMOTION:X]  → drive eyes + mouth + LEDs simultaneously
  → ElevenLabs TTS (Starter tier)  /  Piper fallback
  → play_pcm() 3x gain → wm8960 HAT → PAM8403 → 2x 3W speakers
```

**Interruptible playback** -- stop phrase detection kills TTS mid-sentence.
**PTT button** on GPIO17 as alternative to wake word.
**Vision mode** -- say *"what do you see"* to trigger camera Q&A:
`rpicam-still` → base64 → Ollama vision prompt → spoken response.

---

## Serial Protocol

**Pi4 → Teensy:**
```
EMOTION:NEUTRAL / HAPPY / CURIOUS / ANGRY / SLEEPY / SURPRISED / SAD / CONFUSED
EYES:SLEEP    -- enter sleep display (space scene + snore mouth)
EYES:WAKE     -- restore current eye + neutral mouth
EYE:n         -- switch default eye index (0-8)
MOUTH:n       -- set mouth expression directly (0-8)
```

**Teensy → Pi4:**
```
FACE:1        -- face detected (30s cooldown between sends)
FACE:0        -- face lost
```

---

## Web Config Panel

Flask UI at `http://192.168.1.200:5000`:

- System status (CPU temp, uptime, assistant service state)
- Eye switcher (all 9 styles, live preview on hardware)
- Emotion tester (fires both EMOTION:x and MOUTH:x simultaneously)
- Mouth matrix expression tester (independent from emotion system)
- ElevenLabs voice browser (audition and swap voices live)
- Live assistant log tail
- Chat interface (text input to LLM with optional spoken response)
- Config editor (model names, thresholds, voice ID)
- Service restart button

---

## Building Firmware

Requires [PlatformIO](https://platformio.org/) and
[Teensyduino](https://www.pjrc.com/teensy/td_download.html).
```powershell
# Build and upload
pio run -t upload
# Then press PROG button on Teensy to complete flash
```

**Eye generation** (after editing `resources/eyes/240x240/<eye>/config.eye`):
```powershell
python resources\eyes\240x240\genall.py src\eyes\240x240 resources\eyes\240x240
```

After running `genall.py`, re-apply pupil reduction to nordicBlue, hazel,
bigBlue (genall.py resets values from config.eye):
```powershell
(Get-Content src\eyes\240x240\nordicBlue.h -Raw) `
  -replace '{ 0, 0, 0\.25, 0\.55 }','{ 0, 0, 0.21, 0.47 }' `
  | Set-Content src\eyes\240x240\nordicBlue.h
```

**Rebuild Ollama models** (on GandalfAI after editing `/ollama/`):
```powershell
ollama create jarvis -f "C:\Users\gandalf\jarvis_modelfile.txt"
ollama create jarvis-kids -f "C:\Users\gandalf\jarvis-kids_modelfile.txt"
```

---

## Pi4 Infrastructure Notes

The Pi4 runs overlayfs -- all writes go to RAM and are wiped on reboot.
Every file change must be persisted explicitly:
```bash
sudo mount -o remount,rw /media/root-ro
cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py
```

| Service | Details |
|---|---|
| `assistant.service` | Main voice pipeline, auto-starts on boot |
| `iris-web.service` | Flask web UI on port 5000, auto-starts on boot |
| Ollama | Port 11434 on GandalfAI (192.168.1.3) |
| Wyoming Whisper | Port 10300 on GandalfAI |
| OpenWakeWord | Port 10400 on GandalfAI |

---

## Changelog

### 2026-03-26
- MAX7219 32x8 mouth matrix installed and calibrated (Teensy bit-bang pins 5/6/7)
- 9 mouth expression bitmaps -- chain order and row orientation resolved
- Snore animation designed for sleep mode (12s breathe cycle, minimum intensity)
- Web UI mouth tester panel added
- Web UI emotion buttons fire EMOTION:x and MOUTH:x simultaneously
- Eyelid droop fix -- nordicBlue upper.png replaced with doe geometry
- Session protection system established: Chat=planning, Code=implementation

### 2026-03-25
- 9-eye system -- bigBlue (index 8) added
- All eyes unblocked for web UI direct selection
- Pupil size reduced -15% (nordicBlue, hazel, bigBlue)
- ElevenLabs voice updated to custom "Snarky James Bond" (90eMKEeSf5nhJZMJeeVZ)
- Web config panel live at http://192.168.1.200:5000

### 2026-03-24
- CONFUSED emotion added end-to-end (hypnoRed eyes, magenta LED, modelfile)
- EYE:n serial command for runtime eye switching
- 8-eye system compiled in

### 2026-03-22
- ElevenLabs Starter tier, PAM8403 amp, LED breathing tuned
- Date/time injection into every Ollama call
- EYES:SLEEP / EYES:WAKE voice commands and Teensy firmware
- fillBlack async fix in GC9A01A_Display.h

### 2026-03-21
- Physical base redesigned, pan servo deployed
- Flask web config panel initially deployed

### 2026-03-07
- Wake-on-LAN integration for GandalfAI (MAC: A4:BB:6D:CA:83:20)
- WM8960 ALSA card fix (card index 1, not 0)
- LLM response length capped (num_predict 120, 3 sentence instruction)

---

## Credits

Eye engine based on
[chrismiller/TeensyEyes](https://github.com/chrismiller/TeensyEyes), itself
inspired by [Adafruit Uncanny Eyes](https://github.com/adafruit/Uncanny_Eyes).
GC9A01A driver via [mjs513/GC9A01A_t3n](https://github.com/mjs513/GC9A01A_t3n).

Built by [@Maestro8484](https://github.com/Maestro8484) --
YouTube: [@schm3116](https://youtube.com/@schm3116)
