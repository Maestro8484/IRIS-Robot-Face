# IRIS Web UI — Settings Guide

Settings are at `http://192.168.1.200:5000`. Changes save instantly to IRIS's memory,
but will be lost on reboot unless you hit **Persist to SD** (the button in the top bar).

---

## Audio tab

*Controls how IRIS listens after you say the wake word.*

### Adult

| Setting | What it does | Default | Range |
|---|---|---|---|
| Max record time | How long IRIS will wait for you to finish talking before giving up | 10s | 1–60s |
| Wait after silence | How long IRIS waits after you stop talking before sending your words off for processing. **This is the main responsiveness knob** — lower = faster response | 1.5s | 0.1–10s |
| Mic sensitivity | How quiet the room needs to be before IRIS considers you "done talking". Raise this if IRIS cuts you off too early in a noisy room | 300 | 50–5000 |

### Kids Mode

Same three settings but with more forgiving defaults — longer waits, lower mic gate — so kids have more time to think and speak.

| Setting | Default |
|---|---|
| Max record time | 14s |
| Wait after silence | 3.5s |
| Mic sensitivity | 150 |

---

## Wake Word tab

*Controls how IRIS detects "hey IRIS" (or whatever wake word is active).*

| Setting | What it does | Default | Range |
|---|---|---|---|
| Detection confidence | How sure IRIS needs to be before it wakes up. Higher = less likely to wake up by accident, but may miss quieter wake words | 0.90 | 0.5–1.0 |
| Startup delay | A brief audio flush right after the wake word fires, so the wake word itself doesn't bleed into what you say next. Rarely needs changing | 0.15s | 0.05–1.0s |

Active wake word model is shown as a label (read-only).

---

## Voice tab

*Controls how IRIS speaks.*

### Chatterbox (Primary Voice)

Chatterbox runs on the GandalfAI PC and does high-quality voice cloning.

| Setting | What it does | Default |
|---|---|---|
| Chatterbox on/off | Turn Chatterbox on or off. If off, IRIS falls back to the simpler built-in Piper voice | On |
| Reference voice | The audio file Chatterbox uses to clone IRIS's voice. Swap this to change how IRIS sounds | iris_voice.wav |
| Expressiveness | How dramatically IRIS speaks. 0 = flat and robotic, 0.45 = natural dry wit (default), 1.0 = theatrical | 0.45 |

### Piper (Fallback Voice)

Used automatically if Chatterbox is offline. No settings to configure.

---

## Conversation tab

*Controls how IRIS handles back-and-forth conversation.*

### Follow-up & Context

| Setting | What it does | Default | Range |
|---|---|---|---|
| Follow-up window | After IRIS answers, how long it keeps listening for a follow-up question before going back to sleep | 2s | 1–60s |
| Kids follow-up window | Same, for kids mode | 15s | 1–120s |
| Max follow-up turns | How many back-and-forth exchanges before IRIS forgets the conversation and starts fresh | 3 | 1–20 |
| Memory timeout | If nobody talks to IRIS for this long, it forgets the conversation context | 5 min | 30s–1hr |

### Response Length

IRIS automatically picks how long to make its answer based on what you asked. These settings control the word budget for each type of answer.

| Setting | When IRIS uses it | Default |
|---|---|---|
| Short | Simple yes/no, greetings, quick facts | 120 tokens (~2–3 sentences) |
| Medium | Explanations, how-to questions | 350 tokens (~4–6 sentences) |
| Long | Stories, detailed lists, step-by-step guides | 700 tokens (~8–12 sentences) |
| Max | "Tell me everything about...", essays | 1200 tokens (~15+ sentences) |
| Voice cutoff | Maximum characters spoken aloud. Text beyond this is cut off before it reaches the voice engine | 900 chars (~5–8 sentences) |

> Tip: if IRIS answers feel too long or too short, adjust these — no restart needed.

---

## Eyes tab

Live controls — nothing persists to config. Buttons send commands to the display hardware immediately.

- **Eye Style** — switch between eye looks (Nordic Blue, Flame, Hazel, etc.)
- **Emotion Test** — trigger a named emotion (changes both eyes and mouth expression)
- **TFT Mouth** — set the mouth expression directly

---

## Sleep tab

*Controls IRIS's sleep/wake behavior and display brightness at night.*

### Sleep / Wake buttons

Manually put IRIS to sleep or wake it up. Sleep activates the starfield eye animation and dims the display. IRIS also sleeps/wakes automatically on a cron schedule (9 PM / 7:30 AM).

### Mouth Display Brightness

The mouth display has separate brightness levels for when IRIS is awake vs asleep.

| Setting | What it does | Default | Range |
|---|---|---|---|
| Awake brightness | How bright the mouth display is during the day | 8 | 0–15 |
| Sleep brightness | How bright the mouth display is at night (should be very dim) | 1 | 0–15 |

"Save & Apply Now" changes the brightness immediately without a restart.

### Sleep LED Glow (indigo pulse)

The three LEDs on IRIS pulse slowly while sleeping. Requires assistant restart to take effect.

| Setting | Default |
|---|---|
| Peak brightness | 26 (very dim — intentional) |
| Floor brightness | 3 |
| Pulse speed | 8s per cycle |

---

## Lights tab

*Controls the LED glow color and pulse while IRIS is awake. Requires assistant restart.*

### Normal (cyan pulse)

| Setting | Default |
|---|---|
| Peak brightness | 65 |
| Floor brightness | 3 |
| Pulse speed | 5s per cycle |

### Kids Mode (yellow pulse)

| Setting | Default |
|---|---|
| Peak brightness | 62 |
| Pulse speed | 4s per cycle |

---

## Gandalf AI tab

*Controls which AI brain IRIS uses for answering questions.*

| Setting | What it does | Default |
|---|---|---|
| Adult model | The AI model used for adult conversations | iris |
| Kids model | The AI model used when kids mode is active | iris-kids |

VRAM viewer shows what's currently loaded on GandalfAI's GPU (read-only).

---

## System tab

### Volume

| Setting | What it does | Default | Range |
|---|---|---|---|
| Volume slider | IRIS's speaker volume right now. Takes effect immediately | 121 | 0–127 |
| Volume ceiling | The maximum volume voice commands ("turn it up") can reach | 127 | 60–127 |

### SD Persistence

Changes you make in the web UI are saved to IRIS's RAM instantly — they survive a service restart but **are lost on full reboot** unless you persist them. The colored bar at the top of every page shows current status:

- **Green** — saved to SD card, safe on reboot
- **Amber** — saved in RAM only, will be lost on reboot
- **Click "Persist to SD"** to lock in your changes permanently

---

## Pipeline timing — how a response happens

```
You say wake word
  → brief flush (OWW_DRAIN_SECS, ~0.15s)
  → IRIS records you speaking
  → you stop talking
  → IRIS waits (SILENCE_SECS, default 1.5s) ← biggest tunable delay
  → audio sent to Whisper for transcription
  → text sent to AI for response
  → response spoken aloud via Chatterbox
```

The **Bench tab** shows real timings for each stage of this pipeline.
The biggest gain available: reduce **Audio → Wait after silence** from 1.5s to 0.7–0.8s.
