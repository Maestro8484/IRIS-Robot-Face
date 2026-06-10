# S121 Review Handoffs — Copy-Pastable Session Prompts

Source: S121 whole-project review (2026-06-10). Each block below is a complete opening
prompt for a NEW Claude Code session. Paste the fenced block verbatim. Run sessions in
the order listed — priority is resiliency first, token efficiency second.

Model guidance:
- **Sonnet 4.6** = routine edits, doc sweeps, config changes. Cheap, fast, sufficient.
- **Opus 4.8 / Fable (high effort)** = threading/concurrency, multi-file contracts, anything
  where a subtle mistake ships silently.

---

## SESSION 1 — Documentation Truth Sweep (REPO-ONLY)
**Model: Sonnet 4.6, default effort. No SSH needed. Est: short session.**
**Why first:** every future Claude session reads these docs; wrong docs poison every
session that follows and waste tokens re-deriving truth. The swapped serials in
sysmap.json can reproduce the S63 8-hour display outage if any agent trusts them.

```text
TASK: Repo-only documentation truth sweep from the S121 review. NO deploys, NO SSH, NO code changes.

READ FIRST (only these): CLAUDE.md, SNAPSHOT_LATEST.md (first 50 lines), docs/sysmap.json, IRIS_ARCH.md, docs/iris_issue_log.md (tail), ROADMAP.md, HANDOFF_CURRENT.md (Proactive Flags). Ground truth sources to consult while editing: pi4/core/config.py, src/config.h, src/main.cpp (eye index comments), servo_teensy40/teensy40_base_mount/paj7620.h, pi4/scripts/99-iris-teensy.rules, ollama/iris_modelfile.txt.

CHANGES:
1. docs/sysmap.json — fix SWAPPED Teensy serials in all 4 places (_meta.notes near the end, pi4.serial.usb_serial_number, pi4.teensy40_serial.usb_serial_number, pi4.udev_rules.entries). Truth per pi4/scripts/99-iris-teensy.rules and live Pi4 (verified S121): ttyIRIS_EYES = 13625440 (Teensy 4.1), ttyIRIS_SERVO = 12763490 (Teensy 4.0).
2. docs/sysmap.json config_keys — update stale defaults to current pi4/core/config.py: NUM_PREDICT_SHORT/MEDIUM/LONG/MAX = 40/90/180/400, TTS_MAX_CHARS 1500, LED_SLEEP_PEAK/FLOOR 8/1; add missing _OVERRIDABLE keys (LED_SLEEP_BRIGHT, LOUD_STOP_THRESHOLD, DEFAULT_EYE_IDX, MOUTH_INTENSITY_IDLE, OWW_POST_PLAY_DRAIN_SECS, SLEEP_ANIM_* set).
3. IRIS_ARCH.md — Key Constants block: same tier/LED values; GESTURE_SENSOR_REQUIRED is True; eye index 6 is strikingBlue not bigBlue (also fix pupil-table mention and repo-structure eye list; see src/config.h:56); GESTURE_MOUNT_DEGREES is 180 not 270 (paj7620.h:10); remove "num_predict 800" claim from the Ollama models section (not in modelfile); mark or trim the S23-era "System Status - Active Issues" table as historical.
4. README.md — eye table says 6=bigBlue; firmware is strikingBlue. Fix.
5. docs/iris_issue_log.md — close HW-004 (PAJ7620U2 replaced S82, gestures confirmed live S121).
6. ROADMAP.md — remove RD-003 (verified S121: /home/pi/iris_sleep.log does not exist on live Pi4; only logs/iris_sleep.log remains).
7. HANDOFF_CURRENT.md Proactive Flags — append: S98 VAD-tightening flag SUPERSEDED (SILENCE_SECS=1.2 deliberate per S110/S115); S120 CRLF drift flag also covers hardware/base_mount_bridge.py (CRLF-only, verified S121).

VERIFY: grep sysmap.json for 13625440 — appears only beside ttyIRIS_EYES/Teensy 4.1. Every constant edited matches its source file. git diff touches only the 6 docs listed.
COMMIT: "S121 H-docs: sysmap serial fix + stale-constants sweep + tracker closures (REPO-ONLY)". Update CHANGELOG.md in the same session. Do not push.
```

---

## SESSION 2 — Playback Pipeline Hardening (DEPLOY, Pi4)
**Model: Opus 4.8 or Fable, HIGH effort — this is threading/event-race work.**
**Why second:** three resiliency bugs in the speech path: STOP doesn't actually stop
the pipeline, the audio-length safety cap silently stopped applying when streaming
shipped (S116), and a rare serial race can permanently kill the eye display link
until service restart.

```text
TASK: Three-part hardening batch on the Pi4 streaming playback pipeline. Deploy + persist + verify each.

READ FIRST: CLAUDE.md, SNAPSHOT_LATEST.md (first 50), HANDOFF_CURRENT.md, then IN FULL: pi4/assistant.py (main streaming LLM block, ~lines 940-1085), pi4/hardware/audio_io.py (play_pcm_stream, _playback_interrupt_listener, play_pcm), pi4/hardware/teensy_bridge.py, pi4/services/tts.py (_truncate_for_tts), pi4/core/config.py (lines 91-120). Do not read iris_web.py, vision.py, or firmware.

BUG 1 — STOP race: play_pcm_stream() clears _stop_playback only on exit (audio_io.py ~line 434). The producer loop in assistant.py checks _stop_playback per sentence but is normally blocked inside synthesize() or the LLM stream during the brief window before the clear, so after a voice/gesture STOP the loop keeps streaming LLM tokens and calling Kokoro for the whole remaining reply. FIX: pass a shared interrupted Event into play_pcm_stream (or expose player state) and have the producer break on it per sentence AND per LLM chunk; move the _stop_playback.clear() responsibility to the producer at turn end. Preserve existing behavior for play_pcm_speaking callers.

BUG 2 — TTS_MAX_CHARS dead on streaming path: config.py documents a ~100s hard audio backstop, but per-sentence synthesis means _truncate_for_tts caps each sentence, never the utterance. FIX: cumulative dispatched-char counter in the streaming loop; once TTS_MAX_CHARS exceeded, stop dispatching and stop consuming the stream (log one [TTS] cap line). Update the config.py comment block to name the new enforcement point.

BUG 3 — TeensyBridge reader death: _reader() calls self._ser.readline() unlocked; a concurrent failed send sets self._ser=None; the resulting AttributeError is not caught (only SerialException/OSError) and the reader thread dies silently — no reconnect ever, all sends DROP until restart. FIX: snapshot ser = self._ser under the lock before readline and/or catch Exception in the loop (log once, sleep 5, continue).

VERIFY: py_compile all touched files. Deploy to Pi4 (/home/pi/...), restart assistant, POST must be AUTHORIZED. Live test 1: LONG-tier prompt ("explain how radios work"), say "stop" after first sentence — journal must show dispatch halt within ~1 sentence (no further [KOK] OK lines) and next wakeword accepted immediately. Live test 2: temporarily set NUM_PREDICT_MAX=2000 via web UI, "tell me a story", confirm audio ends near TTS_MAX_CHARS; revert the override. Persist every changed file to /media/root-ro with md5 RAM=SD per CLAUDE.md.

ROLLBACK: restore prior file versions from git and redeploy.
COMMIT: "S12x: streaming STOP race + cumulative TTS cap + TeensyBridge reader hardening (DEPLOYED+VERIFIED)". Update CHANGELOG.md and SNAPSHOT_LATEST.md.
```

---

## SESSION 3 — Gesture + Router Fixes (DEPLOY, Pi4)
**Model: Sonnet 4.6, default effort.**
**Why:** two user-facing gesture features are broken today (MUTE sets ~47% volume and
can never unmute; right-swipe does nothing), plus small router correctness polish.

```text
TASK: Fix gesture MUTE, wire the dead RIGHT gesture, and apply small router/cleanup fixes. Deploy + persist + verify.

READ FIRST: CLAUDE.md, SNAPSHOT_LATEST.md (first 50), then IN FULL: pi4/hardware/base_mount_bridge.py, pi4/hardware/audio_io.py (volume section only, ~lines 97-150), pi4/core/intent_router.py, pi4/iris_web.py (gesture_config route ~lines 649-678), pi4/iris_web.js + iris_web.html (Gestures tab only). Reference: servo_teensy40/teensy40_base_mount/paj7620.cpp line ~161 emits literal "RIGHT" — do NOT touch firmware.

FIX 1 — MUTE broken: set_volume() clamps to VOL_MIN=60, so base_mount_bridge MUTE's set_volume(0) lands at 60 (~47%) and the unmute branch (get_volume()==0) is unreachable. Live config maps CW→MUTE so this is user-facing. FIX: mute via direct amixer set to 0 (bypass clamp) or add an allow_zero path; track muted state explicitly so the second CW restores _mute_restore.

FIX 2 — RIGHT gesture dead: firmware emits "RIGHT"; neither default GESTURE_MAP (base_mount_bridge.py and iris_web.py copies) nor the web UI has a RIGHT key, so it dispatches SKIP. Docs say right-swipe = STOP. FIX: add "RIGHT": "STOP" to both default maps and expose RIGHT in the web Gestures tab. iris_config.json is PROTECTED — do not edit it; the user saves the mapping via web UI.

FIX 3 — Router polish: in intent_router.py _layer0_reflex, prefix matches use bare startswith — "stopwatch timer" triggers REFLEX STOP. Use (norm == p or norm.startswith(p + " ")) for _STOP_STARTS/_SLEEP_STARTS/_WAKE_STARTS (assistant.py's main-loop STOP gate already does this — mirror it). Also: assistant.py ~line 728 hardcodes RMS 300, use SILENCE_RMS; handle_volume_command calls get_volume() (2 subprocesses) before any pattern check — move it after the first match; delete dead GESTURE_SENSOR_REQUIRED from core/config.py (grep-verified unused); fix play_pcm_speaking docstring (says 120ms/frame, code is 0.50s).

VERIFY: py_compile clean; deploy, restart assistant + iris-web, POST AUTHORIZED. CW gesture mutes to silence and second CW restores (amixer sget Speaker shows 0 then prior). Right swipe logs [GESTURE] gesture=RIGHT action=STOP. "stopwatch please" routes to LLM in iris_intent.log; "stop" still REFLEX/STOP. Persist all to /media/root-ro, md5 RAM=SD.
COMMIT: "S12x: gesture MUTE/RIGHT fixes + router word-boundary polish (DEPLOYED+VERIFIED)". Update CHANGELOG.md and SNAPSHOT_LATEST.md.
```

---

## SESSION 4 — GandalfAI Hygiene (DEPLOY, GandalfAI — say DEPLOY explicitly)
**Model: Sonnet 4.6, default effort.**
**Why:** the clone is armed to repeat the S49 deploy failure, and watchtower can
silently break STT/TTS the same way Ollama auto-update broke vision twice (S102/S109).

```text
TASK: GandalfAI maintenance: reset the stale dirty clone and scope watchtower away from the IRIS pipeline containers. I authorize DEPLOY on GandalfAI. No model rebuilds.

READ FIRST: CLAUDE.md, SNAPSHOT_LATEST.md (first 50), IRIS_ARCH.md (GandalfAI sections + PowerShell ampersand rule). GandalfAI shell via ssh-gandalf is cmd.exe — no PowerShell cmdlets inline.

PART 1 — Clone reset: C:\IRIS\IRIS-Robot-Face is at S115 (1a6950b) with local uncommitted edits to both ollama modelfiles. S121 review verified those edits are functionally identical to canonical repo (trailing newline/CR only) and the LIVE iris/iris-kids models are already correct — so a hard reset is safe and NO ollama create is needed. Run: git fetch origin, git reset --hard origin/main (requires SuperMaster repo pushed to GitHub first — verify with the user that local main is pushed before resetting, otherwise the clone resets to an older origin). VERIFY: git status clean; git rev-parse HEAD matches origin/main; ollama show iris --modelfile still shows num_ctx 6144 and stop "User:" (models untouched).

PART 2 — Watchtower scoping: docker inspect watchtower shows Args [--interval 300 --cleanup] with no label filtering — it auto-updates ALL containers including kokoro-tts, wyoming-whisper, wyoming-piper every 5 min check. This is the same failure class as the S102/S109 Ollama auto-update breakages. FIX: read C:\IRIS\docker\docker-compose.gandalf.yml and docker-compose.yml via sftp; add --label-enable to watchtower command and add the enable label ONLY to containers the user wants auto-updated (open-webui, watchtower itself); recreate the gandalf stack (docker compose -f C:\IRIS\docker\docker-compose.gandalf.yml up -d). VERIFY: docker inspect watchtower shows label-enable; curl http://localhost:8004/health healthy; ports 10300/10200 respond; docker ps shows all five containers up.

ROLLBACK: git reflog on the clone for part 1; restore compose file backup (copy to C:\IRIS\backup\ before editing) for part 2.
Update CHANGELOG.md + SNAPSHOT_LATEST.md (GandalfAI row) + HANDOFF_CURRENT.md on SuperMaster repo and commit. Do not push unless I say so.
```

---

## SESSION 5 (optional, feature) — Streaming Follow-Up Turns
**Model: Opus 4.8 or Fable, high effort.**

```text
TASK: Unify the follow-up loop onto the S116 streaming pipeline so follow-up answers start speaking on the first sentence instead of blocking for full generation + full synthesis.

READ FIRST: CLAUDE.md, SNAPSHOT_LATEST.md (first 50), HANDOFF_CURRENT.md, then pi4/assistant.py IN FULL (main streaming block ~940-1085 AND follow-up loop ~1086-1140), pi4/services/llm.py (stream_ollama), pi4/hardware/audio_io.py (play_pcm_stream).

DESIGN: extract one shared helper (e.g. _speak_llm_turn(messages, model, num_predict, teensy, leds, pa, mic)) used by BOTH the main turn and follow-up turns: stream_ollama → per-sentence synthesize → play_pcm_stream, emotion-on-first-chunk, bench stage capture, history append, interrupt propagation. Follow-up keeps its time/volume fast-paths and hallucination/dismissal gates. ask_ollama() remains only for the vision path (or is retired if unused after this). Preserve ALL existing behavior: STOP per sentence, Piper fallback, _rpqr_state["t_last_spoke"], conversation history trim at 20.

VERIFY: py_compile; deploy + persist + md5; POST AUTHORIZED. Live: ask a question that ends in a question (triggers follow-up), answer with a LONG-tier follow-up ("explain why..."), confirm journal shows streaming dispatch and first audio within ~2-4s of llm_start, and the bench JSONL records the follow-up turn. Spoken "stop" mid-follow-up halts.
ROLLBACK: git revert + redeploy.
COMMIT: "S12x: follow-up loop unified onto streaming pipeline (DEPLOYED+VERIFIED)". CHANGELOG + SNAPSHOT.
```

---

## SESSION 6 (optional, feature) — GandalfAI Boot Self-Healing
**Model: Sonnet 4.6.**

```text
TASK: Make GandalfAI reboot non-fragile: docker stacks auto-start, and Pi4 logs a warning when Kokoro/Whisper are down while Ollama is up (silent Piper degradation today). I authorize DEPLOY on GandalfAI and Pi4.

READ FIRST: CLAUDE.md, IRIS_ARCH.md (GandalfAI sections, reboot survival checklist), pi4/iris_post.py (service checks), docs/sysmap.json gandalf block.

PART 1 (GandalfAI): create a Windows Scheduled Task (schtasks, run at logon/boot, highest privileges) that runs: docker compose -f C:\IRIS\docker\docker-compose.yml up -d && docker compose -f C:\IRIS\docker\docker-compose.gandalf.yml up -d. Note Docker Desktop must itself be set to auto-start — check and report its current setting, do not change it without telling the user.
PART 2 (Pi4): in iris_post.py the service layer already probes ports — confirm 8004/10300/10200 checks exist; if Kokoro is WARN-only, ensure the POST summary line makes "Kokoro down, Piper fallback active" explicit in journal. Small change only; no new daemon.

VERIFY: schtasks /query shows the task; run it manually once, docker ps shows all containers; Pi4 POST output names each GandalfAI service status. Persist Pi4 changes to /media/root-ro + md5. Update IRIS_ARCH.md reboot checklist (manual step removed) + CHANGELOG.
```

---

## DEFERRED (design sessions first — do not start cold)
- **P-3 VIGIL presence pre-warm:** VIGIL node posts presence → Pi4 fires WoL + Ollama warmup before the wakeword, hiding the 60-120s GandalfAI wake behind walk-up time. Opus 4.8, TWO sessions (VIGIL firmware event push; Pi4 listener + cooldown policy). Needs a design pass on debounce/power policy first.
- **P-4 conversation memory digest:** nightly cron summarizes conversations.jsonl into ~10 lines injected as a second system message — IRIS remembers yesterday. Opus 4.8, one design + one build session. Hard token cap on the digest is the critical constraint (system prompt is already ~3700 tokens of 6144).
- **F-12 web panel auth (user decision):** token header on mutating iris_web routes. Sonnet, small.
- **F-15 GandalfAI disk (user decision):** ~100GB of retired model weights (qwen2.5vl 21GB, qwen3.5 17GB, gemma3:12b 8.1GB, llama/deepseek/coder ~45GB). Keep gemma3:27b-it-qat (documented rollback). One ollama rm pass after user picks.
- **F-18 T40 8s boot delay:** delay(8000) diagnostics hold in production firmware — fold into the next planned T40 flash (RD-004 batch), not worth a standalone flash cycle.
