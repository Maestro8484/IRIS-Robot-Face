
## IRIS SYSTEM AUDIT — FULL HEALTH CHECK

### CONTEXT
Read SNAPSHOT_LATEST.md and CLAUDE.md before doing anything else.
Do not make any changes until the full audit is complete.
Report findings in the structured format below.

### STEP 1 — FILE STRUCTURE INTEGRITY
Verify the following exist and are non-empty:
- core/config.py, core/assistant.py, core/led_controller.py
- services/tts.py, services/stt.py, services/wakeword.py
- state/ (all state management files)
- hardware/ (all hardware interface files)
- iris_sleep.py, iris_wake.py
- SNAPSHOT_LATEST.md, CLAUDE.md

Flag any missing, empty, or zero-byte files.

### STEP 2 — CONFIG CONSISTENCY CHECK
Cross-check these sources for conflicts:
- core/config.py defaults
- iris_config.json overrides (Pi4: /home/pi/iris_config.json)
- Any hardcoded values in assistant.py that bypass config

Verify:
- ELEVENLABS_ENABLED matches current intent (False until 4/22)
- OLLAMA_HOST points to 192.168.1.3:11434
- STT_HOST points to 192.168.1.3:10300
- TTS_HOST points to 192.168.1.3:10200
- WAKEWORD_HOST points to localhost:10400
- num_predict: 120 in Ollama API call

### STEP 3 — EMOTION/MOUTH/LED ALIGNMENT
Verify in assistant.py:
- Every EMOTION:X dispatch also sends a MOUTH:n via MOUTH_MAP
- MOUTH_MAP covers all 9 emotions: NEUTRAL(0) HAPPY(1) CURIOUS(2)
  ANGRY(3) SLEEPY(4) SURPRISED(5) SAD(6) CONFUSED(7) SLEEP(8)
- LED colors match: NEUTRAL=cyan, HAPPY=yellow, CURIOUS=bright cyan,
  ANGRY=red, SLEEPY=purple, SURPRISED=white, SAD=blue, CONFUSED=magenta
- CONFUSED dispatches EMOTION:CONFUSED + MOUTH:7 (not missing/defaulting)

### STEP 4 — SERIAL COMMAND INTEGRITY (Pi4 -> Teensy)
Verify in hardware/ or assistant.py:
- Serial port path is correct and consistent (not hardcoded vs config mismatch)
- All serial commands use correct format: EMOTION:X, EYES:SLEEP, EYES:WAKE,
  EYE:n, MOUTH:n
- No duplicate serial writes on same event
- FACE:1 / FACE:0 inbound from Teensy is handled

### STEP 5 — SLEEP/WAKE PIPELINE
Check iris_sleep.py:
- Sends EYES:SLEEP before writing /tmp/iris_sleep_mode flag
- Sends MOUTH:8 (snore/sleep expression)
- Piper TTS "Goodnight" fires correctly
- sleep 20 delay present (startup timing fix)

Check iris_wake.py:
- Sends EYES:WAKE
- Sends MOUTH:0 (neutral)
- Removes /tmp/iris_sleep_mode flag
- Wakeword-during-sleep handler: WoL -> poll Ollama -> EYES:WAKE -> MOUTH:0
  -> Piper "Good morning" -> resume pipeline

### STEP 6 — VOICE PIPELINE END-TO-END
Verify the chain is intact in assistant.py / services/:
wakeword (OWW:10400) -> STT (Whisper:10300) -> strip [EMOTION:X] tag
-> Ollama (gemma3:27b @ 192.168.1.3:11434) -> parallel dispatch:
   [serial EMOTION+MOUTH] + [LED] + [TTS]
-> TTS: ElevenLabs (if enabled) else Piper:10200
-> play_pcm() with 3x gain -> wm8960 -> speakers

Flag any step that is not connected or has a silent failure path.

### STEP 7 — KIDS MODE
Verify:
- Voice toggle switches model to jarvis-kids
- Yellow LED activates on kids mode entry
- Extended thresholds active
- Context timeout still 300s

### STEP 8 — CONTEXT TIMEOUT + HISTORY MANAGEMENT
Verify:
- Context window resets after 300s idle
- History is cleared, not accumulated indefinitely
- No memory leak in conversation history list

### STEP 9 — NETWORK DEPENDENCY HEALTH
For each remote service, verify the connection code has:
- Timeout set (not indefinite hang)
- Fallback or graceful error on connection failure
- No hard crash if GandalfAI is asleep/unreachable

Services to check: Ollama, Whisper, Piper, ElevenLabs, WoL

### STEP 10 — OVERLAYFS / PERSISTENCE AUDIT (Pi4)
SSH to Pi4 (192.168.1.200, pi/ohs). Run:
  sudo overlayroot-chroot md5sum /home/pi/assistant.py
  cat /home/pi/iris_config.json
  systemctl status iris.service
  crontab -l

Verify:
- assistant.py md5 matches repo copy
- iris_config.json has expected overrides
- iris.service is enabled and active
- Cron entries for sleep (9PM) and wake (7:30AM) exist

### OUTPUT FORMAT
For each step, output one of:
  [OK]   — verified, no issues
  [WARN] — works but has a risk or inconsistency worth noting
  [FAIL] — broken, missing, or misaligned — describe exactly what and where
  [SKIP] — could not check (state reason)

After all steps, output:
  CRITICAL ISSUES (FAIL items only, numbered)
  WARNINGS (WARN items, numbered)
  RECOMMENDED NEXT ACTIONS (surgical, ordered by priority)

Do not fix anything during the audit. Do not make opportunistic changes.
Commit nothing. This is read-only diagnostic only.
  