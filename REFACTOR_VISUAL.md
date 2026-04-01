# IRIS Refactor — Before & After Visual

---

## BEFORE  (single file, 1,492 lines)

```
pi4/
└── assistant.py  (1,492 lines — everything in one file)
    │
    ├── [CONSTANTS]        ~120 lines of inline literals + iris_config.json loader
    ├── [TEENSY]           TeensyBridge class — serial port, reader thread, reconnect
    ├── [LED]              APA102 class — SPI, all animations, emotion color map
    ├── [GPIO]             GPIO.setup / GPIO.input / GPIO.cleanup inline
    ├── [AUDIO I/O]        mic open, playback, beep, record_command
    │                      _stop_playback threading.Event (local)
    │                      kids_mode read from module global
    ├── [WYOMING]          wy_send / read_line duplicated inline in 3 places
    ├── [STT]              transcribe() inline
    ├── [TTS]              synthesize() + ElevenLabs + Piper inline
    ├── [LLM pure fns]     extract_emotion_from_reply / clean_llm_reply inline
    ├── [VISION]           capture_image / is_vision_trigger / ask_vision inline
    ├── [WAKEWORD]         wait_for_wakeword_or_button inline
    │
    ├── [GLOBALS]          7 scattered module-level variables (mutation via `global`)
    │   ├── conversation_history = []
    │   ├── _kids_mode = False          ← read by record_command via closure
    │   ├── _eyes_sleeping = False      ← mutated by 3 different code paths
    │   ├── _last_interaction = [0.0]   ← list-as-pointer hack for nested fn mutation
    │   ├── _person_context = {...}     ← mutated by background thread
    │   ├── _last_recognition_time = [0.0]
    │   └── SYSTEM_PROMPT = ""          ← defined, never used
    │
    ├── [ORCHESTRATION]    ask_ollama, WoL, CMD listener, local command handlers
    └── [MAIN LOOP]        main() — wake → record → STT → dispatch → TTS → follow-up
```

**Risk profile (before):**
- Any change to audio, LED, Teensy, or STT requires editing the same 1,492-line file
- `global` keyword in 3+ functions — any rename or add breaks silent state mutation
- `wy_send` / `read_line` duplicated → STT, TTS, wakeword could silently drift
- `kids_mode` read as a closure over a global — easy to break when moving code
- No isolation: a syntax error anywhere kills the entire program at import time

---

## AFTER  (modular, 695-line orchestrator)

```
pi4/
│
├── core/
│   └── config.py          ← ALL constants + iris_config.json loader
│       ├── Hardware pins, ports, baud rates
│       ├── Audio tuning (SAMPLE_RATE, CHUNK, silence thresholds)
│       ├── LLM / TTS endpoints and model names
│       ├── VALID_EMOTIONS, MOUTH_MAP, EMOTION_TAG_RE
│       └── iris_config.json runtime overrides (OWW_THRESHOLD, VOL_MAX, etc.)
│
├── hardware/
│   ├── teensy_bridge.py   ← TeensyBridge class
│   │   ├── send_emotion(emotion)
│   │   ├── send_command(cmd)
│   │   ├── close()
│   │   └── auto-reconnect reader thread on serial disconnect
│   │
│   ├── led.py             ← APA102 class (~220 lines)
│   │   ├── All animation methods (show_idle, show_wake, show_speaking, etc.)
│   │   ├── All animations run as daemon threads (non-blocking)
│   │   └── _EMOTION_LED dict: emotion → (r, g, b, period, flash)
│   │
│   ├── io.py              ← GPIO helpers (3 functions)
│   │   ├── setup_button()
│   │   ├── button_pressed() → bool
│   │   └── gpio_cleanup()          ← replaces bare GPIO.cleanup() in assistant.py
│   │
│   └── audio_io.py        ← all audio I/O
│       ├── _stop_playback = threading.Event()   ← importable by orchestrator
│       ├── play_pcm / play_pcm_speaking / play_beep / play_double_beep
│       ├── record_command(mic, ptt_mode, kids_mode)  ← kids_mode now EXPLICIT param
│       ├── handle_volume_command(text)
│       ├── get_volume / set_volume
│       └── STOP_PHRASES, FOLLOWUP_DISMISSALS   ← importable constants
│
├── services/
│   ├── wyoming.py         ← shared Wyoming protocol (ONE copy, used by 3 services)
│   │   ├── wy_send(sock, etype, data, payload)
│   │   └── read_line(sock, buf)
│   │
│   ├── stt.py             ← transcribe(audio_bytes) → str
│   ├── tts.py             ← synthesize(text) → pcm_bytes  (ElevenLabs + Piper)
│   ├── llm.py             ← extract_emotion_from_reply / clean_llm_reply  (pure fns)
│   ├── vision.py          ← capture_image / is_vision_trigger / ask_vision
│   └── wakeword.py        ← wait_for_wakeword_or_button(mic, oww_sock) → str
│
├── state/
│   └── state_manager.py   ← StateManager singleton
│       ├── conversation_history: list
│       ├── last_interaction: float
│       ├── kids_mode: bool
│       ├── eyes_sleeping: bool
│       ├── person_context: dict
│       ├── last_recognition_time: float
│       ├── clear_conversation()   ← atomic: clears history + person + recog timer
│       └── set_person(name, desc) ← thread-safe via lock
│
└── assistant.py           ← ORCHESTRATOR ONLY  (695 lines, down from 1,492)
    ├── Imports all of the above
    ├── ask_ollama()        ← still here (uses state); moves to services/llm next PR
    ├── Local handlers      ← weather, time, briefing, kids mode, volume
    ├── WoL + GandalfAI readiness
    ├── CMD UDP listener
    └── main()              ← wake → record → STT → dispatch → TTS → follow-up
```

---

## CLUSTER-BY-CLUSTER BENEFITS

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CLUSTER 1 — core/config.py                                             │
│  Before: ~120 literals scattered at top of assistant.py                 │
│  After:  single source of truth, loaded once, star-imported everywhere  │
├─────────────────────────────────────────────────────────────────────────┤
│  Benefit        │ iris_config.json overrides apply to ALL modules        │
│  Efficiency     │ tune a threshold in ONE place — no grep-and-replace    │
│  Risk reduction │ no constant defined in two files that can drift apart  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  CLUSTER 2 — hardware/teensy_bridge.py                                  │
│  Before: class + reconnect thread inline in assistant.py                │
│  After:  standalone module, default args from config                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Benefit        │ swap serial port or baud in config only                │
│  Efficiency     │ reconnect logic tested in isolation                    │
│  Risk reduction │ serial changes can't accidentally break audio/LED code │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  CLUSTER 3 — hardware/led.py                                            │
│  Before: APA102 class (~220 lines) embedded in assistant.py             │
│  After:  standalone, all animations daemon-threaded                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Benefit        │ add new LED animation without touching orchestrator    │
│  Efficiency     │ non-blocking calls — main loop never waits on LEDs    │
│  Risk reduction │ SPI/LED bug can't corrupt audio or serial state        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  CLUSTER 4 — hardware/io.py                                             │
│  Before: bare GPIO.setup / GPIO.input / GPIO.cleanup calls inline       │
│  After:  3 named functions; gpio_cleanup() replaces bare GPIO.cleanup() │
├─────────────────────────────────────────────────────────────────────────┤
│  Benefit        │ GPIO pin number lives only in config.py                │
│  Efficiency     │ trivial to mock button_pressed() in tests              │
│  Risk reduction │ cleanup can't be forgotten — it's a named contract    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  CLUSTER 5 — hardware/audio_io.py                                       │
│  Before: audio functions inline; kids_mode read from module global;     │
│          _stop_playback not importable externally                        │
│  After:  kids_mode is EXPLICIT parameter; _stop_playback importable     │
├─────────────────────────────────────────────────────────────────────────┤
│  Benefit        │ future web UI / watchdog can interrupt playback        │
│                 │ directly via _stop_playback.set()                     │
│  Efficiency     │ record_command is a pure function of its arguments     │
│  Risk reduction │ hidden global dependency eliminated — no silent bugs  │
│                 │ when kids_mode is set from a new code path             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  CLUSTER 6 — services/wyoming.py  (NEW — didn't exist before)           │
│  Before: wy_send / read_line copy-pasted inline in STT, TTS, wakeword   │
│  After:  single shared module imported by all three services             │
├─────────────────────────────────────────────────────────────────────────┤
│  Benefit        │ Wyoming protocol change fixed in ONE place             │
│  Efficiency     │ STT, TTS, wakeword guaranteed bit-identical framing    │
│  Risk reduction │ the most common source of silent protocol drift        │
│                 │ between services is completely eliminated              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  CLUSTER 7 — services/{stt, tts, llm, vision, wakeword}.py             │
│  Before: all logic inline in assistant.py                               │
│  After:  each service is a standalone importable module                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Benefit        │ swap STT engine: change one file, zero orchestrator   │
│                 │ impact; same for TTS, vision model, wake word engine  │
│  Efficiency     │ each module testable on a dev machine without Pi4 HW  │
│  Risk reduction │ a broken TTS import raises at startup, not mid-call   │
│                 │ llm.py pure functions have no side effects to debug   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  CLUSTER 8 — state/state_manager.py                                     │
│  Before: 7 module-level globals mutated via `global` keyword in 3+      │
│          functions; list-as-pointer hack for nested fn mutation          │
│  After:  StateManager singleton; plain attribute access; lock on         │
│          multi-field updates; `global` keyword gone from assistant.py   │
├─────────────────────────────────────────────────────────────────────────┤
│  Benefit        │ any module can import `state` — enables future web UI  │
│                 │ to read/write state without touching assistant.py      │
│  Efficiency     │ clear_conversation() is atomic — 3 fields in one call  │
│  Risk reduction │ no accidental global read before assignment;           │
│                 │ state is inspectable / serializable for debug logs     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## SIZE COMPARISON

```
                    BEFORE          AFTER
 assistant.py       1,492 lines     695 lines   (-53%)
 Total pi4/ code    1,492 lines     ~2,100 lines (+41% but modular)
 Files              1               18
 Module globals     7               0
 `global` keywords  4+              0
 Wyoming copies     3               1
 Testable units     0               8 (each service/hardware module)
```

---

## WHAT REMAINS (next PRs)

```
 [ ] Move ask_ollama() → services/llm.py     (unblocked by StateManager)
 [ ] ELEVENLABS_API_KEY → .env + systemd EnvironmentFile=
 [ ] speak_and_idle() helper                 (de-dup 7x TTS pattern in main())
 [ ] Merge refactor/modular-assistant → iris-ai-integration
```
