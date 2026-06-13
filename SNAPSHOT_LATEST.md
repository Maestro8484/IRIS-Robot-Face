# IRIS Snapshot

> **WARNING: DO NOT USE PROJECT-ATTACHED .md FILES.**
> Read live repo via filesystem MCP only. Claude.ai project knowledge base attachments are stale (last updated S49, May 2026 -- 48 sessions behind as of S97). Any session that reads them instead of this file gets wrong hardware state, wrong serial numbers, wrong firmware version, and wrong deploy status.

**Session:** S130 | **Date:** 2026-06-12 | **Branch:** `main` | **Last commit:** S130

> Architecture, pins, constants, deploy commands: see `IRIS_ARCH.md`.

---

## WHAT'S NEXT (Priority Queue)

1. **T40 mechanical damper** — servo tracking confirmed working, user tuning physically. No firmware change needed.
2. **Pure Pi4-local STT commands** — deferred from S110. Evaluate simple wakeword-only commands ("hey jarvis… go to sleep") handled by Pi4 Whisper without LLM, for cases where GandalfAI is asleep. Design session needed.
3. **Wake-from-sleep fall-through** — still deferred. Current: wakeword during sleep → quip → re-sleep. Evaluate whether it should fall through to active listening after the quip.

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. assistant.service active. ttyIRIS_EYES → ttyACM0 (serial 13625440, T41). udev corrected + SD persisted S97. |
| GandalfAI 192.168.1.3 | **OPERATIONAL.** iris/iris-kids on **mistral-small3.2:24b** (S119, was qwen3.5:27b). Ollama **0.30.7**. arch=`mistral3`, 24.0B, caps include `vision` (Pixtral baked in, no mmproj). 15GB Q4, **100% GPU** confirmed (no CPU offload). **num_ctx 6144 unified (S119b)** so text+vision share one context — no reload. Text ~42 tok/s; vision cold-after-text **2.4s** (load 0.28s), warm 1.6s/0.3s first-token (vs 29s on qwen3.5). PT-001 15/20, persona-locked, no token bleed. Env (Machine scope): FLASH_ATTENTION=1, NUM_PARALLEL=1, KV_CACHE=q8_0. Kokoro TTS 8004 OK. **Clone `C:\IRIS\IRIS-Robot-Face` reset to S123/9a7f879 (S124, was S115/1a6950b + dirty modelfile edits).** **Watchtower scoped (S124):** `--label-enable` active; kokoro-tts, wyoming-whisper, wyoming-piper protected from auto-update; open-webui + watchtower labeled for auto-update. **Reboot hardened S127:** IRIS_DockerAutoStart schtask (AtLogon/gandalf/Highest) auto-starts both compose stacks. Docker Desktop auto-starts via HKCU Run. No manual action needed on reboot. |
| Teensy 4.1 (eyes+mouth) | **FLASHED S101.** [VER] confirmed `firmware=S101 built=Jun 7 2026`. Bridge live, no DROPs. Mouth update rate 2Hz during TTS (eye jitter fix). **Sleep mouth fixed S128:** sleep backlight now `MOUTH_INTENSITY:5` (BL_MAP[5]≈6%, starfield visible) — live config was overriding to 1 (≈0.8%, appeared blank). **Awake/idle mouth fixed S130:** resting `MOUTH_INTENSITY_IDLE` 3→8 (BL_MAP[8]≈16%, daytime-visible — was ≈2.7% near-black; idle breathe/blink/twitch now read), Pi4 now reads mouth intensities live from iris_config.json (WebUI changes stick), WebUI gained an Idle slider. **FLASHED S130 + VERIFIED:** `[VER] IRIS-EYES firmware=S130 built=Jun 12 2026` confirmed live (21:10 boot, bridge connected, Ready). RD-030 #2 emotion-tinted idle resting face + #3 face-acquire greet now on the running firmware. **⚠️ Face-tracking not sustained (RD-033):** sensor detects + eyes acquire a face but tracking drops after ~0.5 s (operator-confirmed; recurs after code changes). Detection is fine — this is a sustainment/EyeController-class bug; S130 `mouthGreet()` in the `FACE:1` path is a prime suspect. See Active Issues / ROADMAP RD-033. |
| Teensy 4.0 (servo+gesture) | **FLASHED S97** (FACE_RETURN_MS 30000ms). Tracking confirmed working. Mechanical damper tuning ongoing. |
| TTS | Kokoro primary (Docker 8004), Piper fallback (Wyoming 10200). **Streaming dispatch live (S116):** main LLM replies synthesized per sentence and played overlapped. **Hardened S122:** STOP now halts producer dispatch within ~1 sentence (shared interrupt event); TTS_MAX_CHARS enforced cumulatively across the utterance. **Unified S126:** follow-up turns use the same streaming pipeline via shared `_speak_llm_turn()` — first audio ~1.0–1.3 s after follow-up llm_start (was blocked for full generation + synthesis); follow-up turns now bench-logged (route=FOLLOWUP). **Tail-clip fixed S129:** `play_pcm_stream()` writes a ~200 ms silence tail before `stream.stop_stream()` (blocking-mode ALSA was dropping the last unplayed period → clipped final syllable since S116). Skipped when interrupted so STOP still cuts instantly. |

---

## Active Issues

- **⚠️ TOP PRIORITY (S130, RD-031): log spam / unbounded disk writes — prior space runout crippled the Pi4 (~late May 2026).** Live audit: `[SR] frame` debug print = 52% of recent `assistant` journal lines, `[EYES]` serial echo = 60% (~90% routine serial traffic, continuous all night); journald has no `SystemMaxUse`/`RuntimeMaxUse` cap; `/home/pi/logs` daily exports = 48 MB unbounded (no retention); `/home/pi/.cache/pip` ≈ 150 MB stale. Fix: gate firmware `[SR]` print + bridge serial logging, cap journald (system-path → SD-persist!), add log-export retention, prune pip cache. Full plan + **OPUS** recommendation: `docs/handoff_RD031_logspam.md` / ROADMAP RD-031. **RD-032 collector DEPLOYED S130** — `/home/pi/res_trend.sh` + cron (both md5 RAM=SD) logs one capped CSV line/min to `/home/pi/logs/res_trend.csv` (self-trim ~3 days); gives the RD-031 session real 24–48 h trend data. WebUI `/api/sysstat` panel still open.
- **MEDIUM (S130, RD-033): Person Sensor face-tracking not sustained — acquires then drops after ~0.5 s.** Operator-confirmed (authoritative): the sensor detects and the eyes lock onto a face, but tracking redirects after ~0.5 s; this recurs after code changes (regression-prone path). NOT a detection failure (earlier `No Person Sensor found` flash-boot logs + the inconclusive clean-reboot probe-line gap were misreads — `FACE:` log counts are unreliable here: 30 s rate-limit, no Pi4 consumer). Candidate mechanisms: `EyeController.h setTargetPosition` seeding (prior fix ed8fa41, **protected file**), gaze-timeout/`FACE_LOST_TIMEOUT_MS` autoMove re-engage, and the **S130 `mouthGreet()` blocking SWSPI redraw added into the `FACE:1` path** (RD-030 #3 — prime suspect to check first). Full plan: ROADMAP RD-033 / `docs/handoff_RD031_logspam.md` §8. Diagnose via serial debug + observed eye behavior, not log counts.

- **LOW: Wake-from-sleep fall-through** — wakeword during sleep: IRIS wakes, plays quip, re-enters sleep (S104). Evaluate whether it should fall through to active listening instead of re-sleeping.
- **LOW: Ollama version pin** — Currently 0.30.7 (runs mistral-small3.2:24b fine). Firewall outbound block on ollama app.exe in place; user unchecked auto-update in Ollama UI (S110). The qwen3.5 pin rationale is moot post-S119, but keep the firewall/pin to avoid surprise upgrades.
- **RESOLVED (S128): evening sleep mode now fully sleeps the displays.** Mouth was blank because live `iris_config.json` forced `MOUTH_INTENSITY_SLEEP=1` (≈0.8% backlight, starfield invisible) → raised to 5. Eyes could stay awake on state desync because voice `EYES_SLEEP`/`EYES_WAKE` were guarded by the in-memory `state.eyes_sleeping` → now route unconditionally through `_do_sleep()`/`_do_wake()`, plus a startup reconcile re-asserts sleep when booting/restarting inside the sleep window. DEPLOYED + VERIFIED (full 21:00 path exercises tonight).
- **RESOLVED (S119b): iris/iris-kids modelfile `num_ctx` raised 4096 → 6144.** Text+vision now share one context — Ollama no longer reloads on text↔vision switches (vision cold-after-text 12.4s → 2.4s) and generation has real headroom vs the ~3700-tok system prompt. VRAM verified safe: `ollama ps` = 15GB at 6144, +Kokoro 2GB = 17/24 GB, 100% GPU. The old sysmap `num_ctx ≤ 4096` limit was gemma3/qwen-era (obsolete) and is updated.

---

## udev Serial Numbers — Confirmed S97

| Symlink | Serial | Device |
|---|---|---|
| `/dev/ttyIRIS_EYES` | `13625440` | Teensy 4.1 (eyes + TFT mouth) |
| `/dev/ttyIRIS_SERVO` | `12763490` | Teensy 4.0 (servo + gesture) |

S94b had these swapped. Corrected S97 by connecting T41 alone and observing which serial appeared. IRIS_ARCH.md, pi4/scripts/99-iris-teensy.rules, and live Pi4 udev rules all updated.

---

## Do Not Touch

- `iris_config.json` — gesture map + emotion map live config
- `alsa-init.sh`
- `src/TeensyEyes.ino`
- `src/eyes/EyeController.h`

---

## Last Session Changes (S130 — 2026-06-12)

- **Awake/idle mouth too dark + brightness control had no lasting effect — DEPLOYED + VERIFIED (Pi4). No firmware change.** Root cause was threefold: (1) `MOUTH_INTENSITY_IDLE=3` (BL_MAP[3]≈2.7%, near-black) is the resting level sent after every interaction and after POST/boot — the mouth sits near-black most of the time and the firmware idle animations modulate around it (invisible); (2) `assistant.py` froze `MOUTH_INTENSITY_*` as startup constants (`from core.config import *`) so WebUI "Apply Now" only did a one-shot push that the next turn reverted; (3) WebUI exposed only AWAKE+SLEEP, not the dominant IDLE level.
- **Fixes:** `core/config.py` `MOUTH_INTENSITY_IDLE` 3→**8** (≈16%); `assistant.py` new `_mouth_intensity(kind)` helper reads the three intensities live from `iris_config.json` (default fallback, 0–15 clamp), wired into all 5 send sites — WebUI changes now persist across turns without a restart; `iris_post.py` post-boot idle 3→8; `iris_web.html` added an **Idle intensity** slider (+hint corrected to ILI9341 PWM); `iris_web.js` `saveMouthIntensity()` persists IDLE and pushes it live when awake.
- **Deployed (md5 RAM=SD, all 5):** core/config.py=`272a33f973a3644fc730b3e5ff08819b`, assistant.py=`f2909a7e0503e15752edb99ba6619460`, iris_post.py=`c4c4d813af1817144cf34bc4ab031890`, iris_web.html=`968f7045261309fb8d50eaca12473677`, iris_web.js=`370ac02a712d9148ac7268bf676bb448`. POST after restart **AUTHORIZED** (MOUTH:0-8, EYES:SLEEP/WAKE, MOUTH_INTENSITY ramp all PASS); post-boot resting intensity now `MOUTH_INTENSITY:8`. Live `iris_config.json` (protected) untouched: AWAKE=10, SLEEP=3, no IDLE key → config default 8 governs.
- **Pending human check:** in daylight, the mouth between interactions is clearly lit (~16%) with visible breathe/blink/twitch idle animation; the new WebUI Idle slider changes resting brightness immediately and persists across the next conversation.
- **Anthropomorphic mouth (RD-030):** #2 emotion-tinted idle resting face + #3 "noticed you" face-acquire greet **FLASHED S130 (firmware live, [VER] verified)** — visual confirmation still pending (IRIS auto-slept at 21:00; observe tomorrow awake). **#3 greet blocked until the Person Sensor re-detects** (see Active Issues). #2 tint does NOT need the sensor (needs an emotional turn + ~2 min idle during awake hours). #1 amplitude-reactive lip-sync deferred to its own session (Pi4+firmware, hot loop). See CHANGELOG S130 firmware addendum + ROADMAP RD-030.

## Last Session Changes (S129 — 2026-06-12)

- **TTS tail-clip fix — DEPLOYED (Pi4). No firmware change.** Spoken LLM replies were dropping the final syllable. Root cause: S116-streaming regression — `play_pcm_stream()` uses blocking `stream.write()` then called `stream.stop_stream()` right after the last write; in blocking mode `write()` returns when data is handed to ALSA (not played), so `stop_stream()` discarded the last unplayed period. Only the final blob was affected (inter-sentence writes are contiguous) → end-of-response clip. The callback-mode `play_pcm()` (single-blob path) never clipped because PortAudio drains before going inactive.
- **Fix:** `pi4/hardware/audio_io.py` `play_pcm_stream()` `finally` writes a ~200 ms stereo s16le silence tail (`b"\x00" * (rate*4//5)`) before `stop_stream()`, only when **not** interrupted (STOP still cuts instantly). Inaudible; no rate/pitch change.
- **Deployed (md5 RAM=SD=repo):** audio_io.py=`d5139a4c0942fe99fdf9a0dc59896b35` (CRLF; live byte-identical to repo). POST **20/23 PASS, 3 WARN, 0 FAIL → AUTHORIZED**, RAM vs SD md5 PASS.
- **Pending human check:** speak any reply — last word no longer clipped; "stop" mid-reply still cuts immediately.

## Last Session Changes (S128 — 2026-06-11)

- **Evening sleep-mode display fix + scheduled-sleep hardening — DEPLOYED + VERIFIED (Pi4). No firmware change.** Full diagnosis: `docs/sleep_mode_diagnosis_S128.md`.
- **Blank mouth (root cause):** live `iris_config.json` overrode `MOUTH_INTENSITY_SLEEP=1` → firmware `BL_MAP[1]=2/255≈0.8%`; the starfield was rendering but invisible. Raised to **5** (= the firmware's own `mouthSetSleepIntensity()` BL_MAP[5], matches repo `config.py` default).
- **Eyes stay awake (root cause):** `state.eyes_sleeping` is in-memory, defaults False, never seeded; voice `EYES_SLEEP`/`EYES_WAKE` were guarded by it so a desync (e.g. an assistant restart inside the sleep window) made "go to sleep" a silent no-op. Now both route through authoritative `_do_sleep()`/`_do_wake()` (unconditional/idempotent), and a **startup reconcile** re-asserts sleep when `in_sleep_window()` OR `/tmp/iris_sleep_mode`. Firmware needs no change — its render loop is gated on `eyesSleeping`, so it's self-consistent.
- **Goodnight chime:** `iris_sleep.py` called a non-existent `/usr/local/bin/piper` (errored nightly) → now plays a network-free `/home/pi/sounds/goodnight.wav`. **Clip rendered + deployed** via Kokoro (IRIS voice, md5 `6349193ebe4f99c42f01fd78e9364282`, RAM=SD); full `iris_sleep.py` run logged `[SLEEP] Goodnight chime played`.
- **Cron version-controlled:** added `pi4/scripts/iris_cron_reference.txt` (the `pi` user crontab sleep/wake/backup entries; confirmed SD-persisted).
- **Deployed (md5 RAM=SD):** assistant.py=`2092e0a8baa7e1bf0091c643436fdfec`, iris_sleep.py=`d697798794ca50f544321aa7288f7106`, iris_config.json=`bb5c803b0e7a8298e95869bfe27f71f0`. POST **20/23 PASS, 0 FAIL → AUTHORIZED**. Functional test: EYES:SLEEP → `MOUTH_INTENSITY: 5` + `starfield starting`; EYES:WAKE → restored.
- **Pending human check:** confirm tonight's automatic 21:00 sleep — mouth shows visible starfield, eyes show starfield; wake-word after that wakes then re-sleeps.

## Last Session Changes (S126 — 2026-06-11)

- **Follow-up loop unified onto the S116 streaming pipeline — DEPLOYED + VERIFIED (harness-level).** New shared `_speak_llm_turn()` in `pi4/assistant.py` drives BOTH the main turn and follow-up LLM turns: `stream_ollama` → per-sentence `synthesize` (Kokoro→Piper) → overlapped `play_pcm_stream`, emotion-on-first-chunk, STOP per chunk + post-synthesize, cumulative TTS_MAX_CHARS, producer-owned `_stop_playback`, history trim at 20, `t_last_spoke`. Follow-up answers now start speaking on the first sentence (~1.0–1.3 s after llm_start; previously blocked for full generation + full synthesis). Follow-up time/volume fast-paths and hallucination/dismissal/STOP gates unchanged.
- **Follow-up turns now bench-logged:** journal `[BENCH]` stages `fu_`-prefixed (keeps `/api/bench` journal parser from overwriting main-turn stages within a wake cycle); `iris_bench.jsonl` gets a `route="FOLLOWUP"` record per turn with stt/llm/tts/play stages.
- **Blocking `ask_ollama()` retired** (no callers left — vision uses `ask_vision()`); dead imports removed; `services/llm.py` docstring + `IRIS_ARCH.md` source map updated.
- **Verified via live Pi4 harness on the deployed modules** (real stream_ollama + Kokoro + play_pcm_stream through the speaker): follow-up first audio 1250/1046 ms; STOP at t+3.0 s mid-MAX-story → dispatch halted at 3.21 s, stream abandoned; interrupt propagated player→producer→caller; JSONL FOLLOWUP records present. POST after restart: **20/23 PASS, 3 WARN, 0 FAIL → AUTHORIZED**, `[INFO] Ready.`
- **Deployed (md5 RAM=SD):** assistant.py=`f48e258fdf86f3ef4c7bf4ceb5ca0bf0`, services/llm.py=`bc0e4bae31e616227840581a98adb7d4`.
- **Pending human check:** real spoken follow-up through the mic + spoken "stop" mid-follow-up.
- **Side-finding (pre-existing):** interrupt-listener STT substring-matches STOP_PHRASES — IRIS saying "…stops…" can self-interrupt when speaker bleed exceeds the detect threshold; bleed peaked 25733 > LOUD_STOP_THRESHOLD=25000 in harness conditions. See HANDOFF Proactive Flags.

## Previous Session Changes (S123 — 2026-06-11)

- **Gesture MUTE fixed — DEPLOYED + VERIFIED.** `set_volume()` clamped to VOL_MIN=60 so MUTE landed at ~47% and the `get_volume()==0` unmute branch was unreachable. Now: `set_volume(level, allow_zero=True)` bypasses the floor for MUTE only; bridge tracks `_muted` state explicitly and second CW restores `_mute_restore`. Live check on real ALSA: 123 → `Playback 0 [0%]` → restored 123.
- **RIGHT gesture wired — DEPLOYED + VERIFIED.** Firmware emits `RIGHT` (right swipe) but no map had the key → SKIP. `"RIGHT": "STOP"` added to both default maps (bridge + iris_web); bridge `_load_gesture_map()` now merges stored config over defaults so RIGHT works with the existing stored GESTURE_MAP (iris_config.json untouched). Web Gestures tab has a RIGHT row; `/api/gesture_config` returns RIGHT:STOP. Physical-swipe log check pending human.
- **Router word-boundary polish — DEPLOYED + VERIFIED.** `_layer0_reflex` prefix matches now require exact-or-phrase+space ("stopwatch please"→LLM, "cancelled order"→LLM; "stop"/"cancel"/"stop talking now" still REFLEX/STOP — confirmed in live iris_intent.log).
- **Cleanups:** assistant.py RMS gate uses `SILENCE_RMS` (was hardcoded 300); `handle_volume_command` calls `get_volume()` lazily (saves 2 subprocesses on non-matches); `play_pcm_speaking` docstring 120ms→0.50s; dead `GESTURE_SENSOR_REQUIRED` deleted from core/config.py (+ IRIS_ARCH/IRIS_CONFIG_MAP updated, 2 stale tests replaced). **RD-003 closed** (`/home/pi/iris_sleep.log` does not exist; removed from ROADMAP).
- **Deployed (md5 repo=RAM=SD, all 8):** assistant.py=`db96f785b796b9a61bed0b591f6fe5d8`, hardware/audio_io.py=`035d43b6d7e623f959354a9938110c5a`, hardware/base_mount_bridge.py=`9ba56cbb0862c11d2b28823700c4d2ad`, core/intent_router.py=`692c8e17b5340c0336bb1ade476ef1e0`, core/config.py=`d9ebc9c5751a2db89af9424b1af7c83f`, iris_web.py=`1fe3acc39ce4f54bc16c0e5621dd51d4`, iris_web.js=`5ffc825a52a53816a79d832cc37fd56e`, iris_web.html=`5925e0afd477917f37a62becba4efd18`.
- **POST after restart: 20/23 PASS, 3 WARN, 0 FAIL → AUTHORIZED**, `[BASE] Teensy 4.0 connected`, `[INFO] Ready.` iris-web restarted and serving the new UI.

## Previous Session Changes (S122 — 2026-06-11)

- **Streaming playback pipeline hardening — DEPLOYED + VERIFIED** (Session 2 of S121 review handoffs). Three fixes:
  - **STOP race fixed.** `play_pcm_stream()` no longer clears `_stop_playback` (entry or exit); it accepts a shared `interrupted` Event. The producer in `assistant.py` owns the flag lifecycle (clear at turn start + turn end) and checks `_stop_playback OR _player_interrupted` per LLM chunk and again after each `synthesize()`. Live harness: STOP at t=2.0s mid-synthesis → dispatch halted in 0.21s, LLM stream abandoned at 2/10 sentences. Also fixes latent inverse bug (stale STOP from idle aborting the next turn's first chunk).
  - **TTS_MAX_CHARS now enforced on the streaming path.** Cumulative dispatched-char counter; at ≥1500 chars dispatch stops and the LLM stream stops being consumed. Live harness: num_predict=2000 story → halted at 1567 chars/15 sentences. `config.py` comment names both enforcement points.
  - **TeensyBridge reader can no longer die silently.** Reader snapshots `_ser` under the lock, except handler uses the snapshot, broad `except Exception` → log + retry. Live harness reproduced the previously-fatal error class (`'NoneType' object cannot be interpreted as an integer`) → reader logged, reconnected, sends resumed.
- **Deployed files (md5 RAM=SD verified):** `assistant.py`=`e55bbda4a02f971ce6f31398dee01ab9` (now LF on Pi), `hardware/audio_io.py`=`09e6468d7dbce097408001d03890eec8`, `hardware/teensy_bridge.py`=`f662309a45b8aa065dad1f0a40c27f85`, `core/config.py`=`b5d8d57b9e66185d90a56d7b40f606ed`.
- **POST after restart: 19/23 PASS, 4 WARN, 0 FAIL → AUTHORIZED**, `[INFO] Ready.` (WARN delta vs S120 is the no-[VER]-on-restart artifact.)
- **Pending human check:** voice-spoken "stop" through the mic during a LONG reply (interrupt-listener STT path) + immediate next-wakeword acceptance.

## Last Session Changes (S120 — 2026-06-09)

- **Stale-reference sweep, Batch 3 (Pi4 code) — DEPLOYED + VERIFIED.** Removed dead `think:False` from the 4 remaining Pi4 Ollama callers (Mistral has no thinking mode) and refreshed their stale qwen3.5 comments:
  - **`pi4/assistant.py`** — `ask_ollama` (chat) + startup warmup. md5 RAM=SD=`2350a4108468a1f687f0eb40b094b0d7`.
  - **`pi4/services/vision.py`** — `ask_vision`; num_ctx 6144 KEPT (image tokens, matches modelfile). md5=`31cb7a089060ce3102c86281ac2936c6`.
  - **`pi4/iris_web.py`** — `api_vision`; removed wrong "qwen3.5 thinking model" rationale, num_ctx 6144 KEPT. md5=`077002b46dbc8691cb5b75b5e44b680b`.
  - **`pi4/iris_post.py`** — `l3_llm` POST smoke. md5=`18748f348149590879f8a43b83f83f11`.
- **WebUI:** `pi4/iris_web.html` confirmed 0 gemma/qwen hits (only generic "Vision Model" + config-key labels). No change.
- **Verified live:** `py_compile` clean; assistant + iris-web restarted; POST **20/23 PASS, 0 FAIL → AUTHORIZED**; L3 LLM smoke PASS; `[LLM] Model warmed.`; LLM chat smoke `[EMOTION:NEUTRAL]` + no `[INST]/</s>/User:` bleed; `/api/vision` returned a clean frame description (no HTTP 400, num_ctx intact, no bleed).
- **Flagged (non-behavioral drift):** repo `assistant.py` is CRLF vs live LF; repo `iris_post.py` is Unicode (`→ × ──`)+1 extra comment line vs live ASCII-normalized. Code logic byte-identical; only think:False changed. vision.py/iris_web.py byte-match repo. Future repo↔Pi4 normalization sweep recommended — see HANDOFF Proactive Flags.
- (Batches 1+2 — docs/JSON + tools stale-ref sweep — committed REPO-ONLY earlier this session; see CHANGELOG S120.)

## Last Session Changes (S119 — 2026-06-09)

- **LLM migrated qwen3.5:27b → mistral-small3.2:24b** (iris + iris-kids). Both rebuilt on GandalfAI. arch=`mistral3`, dense, Pixtral vision baked in. DEPLOYED+VERIFIED.
- **`ollama/iris_modelfile.txt`** — FROM mistral-small3.2:24b. PARAMETER block replaced: num_gpu 99, num_ctx 4096, temperature 0.75, top_p 0.9, repeat_penalty 1.1, stop `[INST]`/`[/INST]`/`</s>`/`User:`. SYSTEM + all few-shot/calibration/VISION blocks preserved verbatim. The `User:` stop was added (beyond brief spec) to kill few-shot turn-bleed Mistral exhibits without Qwen's `<|im_end|>` boundary. DEPLOYED.
- **`ollama/iris-kids_modelfile.txt`** — same FROM + PARAMETER block + stop set. Kids persona preserved. DEPLOYED.
- **`pi4/services/llm.py`** — removed `"think": False` from `stream_ollama()` payload (Mistral has no thinking mode; was dead weight from S114 qwen3.5). md5 RAM=SD=`911261166ce7aeed07a8e3ef1a2d044e`. DEPLOYED+VERIFIED. assistant.service restarted, POST L1 iris+iris-kids PASS, live path emits correct emotion tags with zero `[INST]/</s>/User:` bleed.
- **Gates:** PT-001 15/20 (persona-locked, no RLHF tells; cleaner than gemma3; `goodnight→NEUTRAL` and `motor/servo` now pass; remaining misses are borderline/fixture-debatable). Latency: text 35.8 tok/s, vision 100% GPU, warm 1.4s, cold 12s (vs 29s qwen3.5).
- **Housekeeping:** stray root files (`$null`, `Update-IRISProjectFiles.*`) swept to `_housekeeping/S119_root_sweep/` with MANIFEST; `LICENSE` restored (was an unstaged deletion).
- **S119b:** num_ctx unified 4096→6144 on both modelfiles + GandalfAI rebuild (vision cold-after-text 12.4s→2.4s, no reload; VRAM 15GB at 6144, 100% GPU). No Pi4 change needed (vision.py already sent 6144; text callers inherit the new default).
- **NOT done (follow-up):** `think:False` still present in 4 other Pi4 callers (assistant.py, vision.py, iris_web.py, iris_post.py) — harmless dead weight on Mistral, sweep next session. Live voice (wakeword→TTS) and camera-vision human checks pending. Repo-wide stale-reference sweep (old model names in docs/WebUI) recommended as its own session — see HANDOFF.

## Last Session Changes (S118 — 2026-06-09)

- **Vision 400 fixed.** Web UI "describe what you see" returned `400 Bad Request` from `/api/generate`. Root cause: a real camera frame = ~4570 vision tokens > the model's default 4096 `num_ctx` (`"exceeds the available context size"`). NOT a vision-support issue — iris has the `vision` capability. Broke both web UI and voice paths since the S113/S114 qwen2.5vl→qwen3.5 swap.
- **`pi4/services/vision.py`** — `ask_vision()` adds `"options": {"num_ctx": 6144}`. md5=`1e5500958db39e888db4bb4294150b9d` RAM=SD. DEPLOYED.
- **`pi4/iris_web.py`** — `api_vision()` adds `"think": False` (was missing → empty reply on thinking model) + `"options": {"num_ctx": cfg.get("VISION_NUM_CTX", 6144)}`. md5=`9f7af3a6d023edd794cb067abdff3871` RAM=SD. DEPLOYED.
- **VERIFIED:** `POST /api/vision` → HTTP 200 in ~29 s with a correct scene description. (~29 s is inflated by an Ollama model reload — vision's 6144 ctx differs from the 4096 text default; see Proactive Flags.)

## Previous Session Changes (S117 — 2026-06-09)

- **`pi4/core/config.py`** — Response-length tiers retuned for a voice robot (were narrator-length). `num_predict` SHORT 120→40 (~9s), MEDIUM 350→90 (~21s), LONG 700→180 (~41s), MAX 1200→400 (~92s≈1.5min), default 300→100. `TTS_MAX_CHARS` 2500→1500 (~100s hard backstop, all tiers). Basis: measured ~0.23s speech/token (S116). Inline rationale+rollback in file. md5=`5391ed8c079dee4527c72ec8e148237f` RAM=SD. DEPLOYED+VERIFIED.
- **`pi4/services/llm.py`** — `_MAX_PATTERNS` now triggers MAX (story tier) ONLY on explicit "tell me a story"/essay/long-form requests; removed the `word_count>15` LONG→MAX promotion so wordy "explain…" stays LONG. md5=`b94427979460d21805765f817b8cf522` RAM=SD. DEPLOYED+VERIFIED (live: story→400, explain→180, history→180, essay→400, hello→40).

## Previous Session Changes (S116 — 2026-06-09)

- **`pi4/hardware/audio_io.py`** — New `play_pcm_stream()`: gapless back-to-back playback of a queue of per-sentence PCM blobs with one EYES:SPEAKING/mouth-anim/interrupt-listener spanning the whole utterance. `play_pcm`/`play_pcm_speaking` untouched. md5=`ada50cfc3ab6b8ae52efdc7c7f9aab9c` RAM=SD. DEPLOYED.
- **`pi4/assistant.py`** — Main LLM block rewired: `stream_ollama()` → per-sentence `synthesize()` → background `play_pcm_stream` player. First audio now starts on the first sentence (was: full response synthesized in one blocking call). STOP checked per sentence dispatch. Emotion-on-first-chunk, Piper fallback, length classifier, follow-up loop all preserved. md5=`fe79c67bd5dfea50f5559e0304d37c35` RAM=SD. DEPLOYED.
- **Latency (LLM-start→first-audio, n=10 long prompts):** NEW p50=2086ms / p90=4257ms vs OLD (blocking) p50≈23.3s on these long replies. Resolves S98 streaming flag. Behavioral hardware checks (speaker/emotion-face/spoken-STOP/Piper) need a human — handed off.

## Previous Session Changes (S115 — 2026-06-09)

- **`pi4/core/intent_router.py`** — `_TIME_RE` pattern: added `what time is it` explicit literal + `time please` variant. "what time is it" now routes to UTILITY (was falling through to LLM at ~1434ms). md5=ea9e0d82425f76d98053c2b71221ef99 RAM=SD. DEPLOYED+VERIFIED.
- **`ollama/iris_modelfile.txt`** — Adversarial few-shot "You're dumb." example: `[EMOTION:ANGRY]` → `[EMOTION:AMUSED]`. Old ANGRY example was overriding S112 EMOTION CALIBRATION block. iris rebuilt on GandalfAI. DEPLOYED+VERIFIED.
- **VAD** — `SILENCE_SECS=1.2` confirmed in iris_config.json. No change needed.

## Previous Session Changes (S114 — 2026-06-09)

- **GandalfAI Ollama** — Already at 0.30.7 (no upgrade needed). GPU dispatch confirmed for qwen3.5:27b: 35.2 tok/s VERIFIED.
- **`ollama/iris_modelfile.txt`** — Removed `PARAMETER think false` (unsupported in Ollama 0.30.7; causes `ollama create` error). `"think": false` moved to API call level. iris rebuilt on GandalfAI. DEPLOYED+VERIFIED.
- **`ollama/iris-kids_modelfile.txt`** — Same removal. iris-kids rebuilt. DEPLOYED+VERIFIED.
- **`pi4/assistant.py`** — `"think": False` added to `ask_ollama()` and warmup call. DEPLOYED+VERIFIED. md5=1c42e3dd707281eaacc2cb2380394743 RAM=SD.
- **`pi4/services/llm.py`** — `"think": False` added to `stream_ollama()` payload. DEPLOYED+VERIFIED. md5=e93c69c2430415826baeaf05e247c853 RAM=SD.
- **`pi4/core/config.py`** — `VISION_MODEL` changed from `"qwen2.5vl:32b-q4_K_M"` → `"iris"` (qwen3.5:27b handles vision natively). DEPLOYED+VERIFIED. md5=f7a143d855a06c9b3fb8292e58ef363c RAM=SD.
- **`pi4/iris_post.py`** — `"think": False` added to l3_llm POST test. DEPLOYED+VERIFIED. md5=2bf0723a7f06d8f72896f3178af0e8ec RAM=SD.
- **`pi4/services/vision.py`** — `"think": False` added to ask_vision() /api/generate call. DEPLOYED+VERIFIED. md5=a60ffceaa8364678d2dffd04cbb951fc RAM=SD.
- **`tools/workbench/workbench.js`** — `"think": false` added to both /api/generate calls in harness + latency tester. REPO-ONLY.
- **Pi4 POST** — 20/23 PASS, WARN: 3, FAIL: 0 (was 19/23, FAIL: 1 on LLM smoke). All FAIL resolved.
- **pt001 persona harness** — 16/20 PASS (80%). Target ≥13/20 MET.

## Previous Session Changes (S112 — 2026-06-09)

- **`ollama/iris_modelfile.txt`** — `FROM qwen2.5vl:32b-q4_K_M` (was qwen2.5:32b). AMUSED calibration block added. DEPLOYED+VERIFIED. Smoke test: "You're dumb." → `[EMOTION:AMUSED]`. Both models rebuilt on GandalfAI. `ollama list` 21GB fresh timestamps.
- **`ollama/iris-kids_modelfile.txt`** — `FROM qwen2.5vl:32b-q4_K_M` (was qwen2.5:32b). No other changes. DEPLOYED+VERIFIED. Smoke test: "tell me a joke" → `[EMOTION:HAPPY]` + kid-appropriate response.
- **`IRIS_ARCH.md`** — VRAM baseline updated (VL base ~21GB, ~23GB total). Vision live note added S112.
- **`HANDOFF_CURRENT.md`** — GandalfAI status updated. S111 Chat flags marked RESOLVED.

## Previous Session Changes (S110 — 2026-06-09)

- **`pi4/assistant.py`** — RPQR + pipeline latency overhaul. DEPLOYED+VERIFIED. md5=`fa5bf5b065951bdbf34ab27b3af0ea4e` RAM=SD.
  - **RPQR sleep-path fix**: removed `ensure_gandalf_up()` from sleep-wakeword branch — pre-cached quip now plays instantly without Ollama check.
  - **Quip on every wakeword**: beep replaced by time-of-day quip on all activations. `_WAKE_QUIPS` expanded to 4–5 lines/band (26 total cached).
  - **New RPQR triggers** (all pre-cached PCM, fire before Gandalf gate): double-tap (<30s), post-speech (<5s after reply), top-of-hour (±2 min, 13 hour variants cached), first-of-day ("Morning."/"Finally.").
  - **`t_last_spoke` tracking**: set after LLM main response and follow-up responses to drive post-speech trigger.
  - **Removed** stale `_quip_state` dict (replaced by `_rpqr_state`).
- **`pi4/iris_config.json`** — `SILENCE_SECS=1.2` (was 1.5, -0.3s per interaction). DEPLOYED+VERIFIED. md5=`9dbd091fff10409f1e6d544d9e26b603` RAM=SD.
- **`docs/prompt_pipeline_latency_audit.md`** — NEW. Canned Claude Code prompt for pipeline latency troubleshooting: bottleneck table, fix templates, deploy sequence, bench check commands. REPO-ONLY.

## Previous Session Changes (S109 — 2026-06-08)

- **`pi4/core/config.py`** — `VISION_MODEL = "qwen2.5vl:32b-q4_K_M"` (was `"iris"` — text-only model broke vision). DEPLOYED+VERIFIED. md5 RAM=SD=`2978ca89d5d9e6172a0153b1802f179c`.
- **GandalfAI Ollama** — Downgraded 0.30.6 → **0.24.0** (0.30.x CLIP loader requires `clip.vision.n_wa_pattern` key missing from qwen2.5vl GGUF; 0.24.0 old engine does not check this). Installer via `$env:OLLAMA_VERSION="0.24.0"; irm https://ollama.com/install.ps1 | iex`.
- **GandalfAI Firewall** — Rule re-applied blocking `ollama app.exe` outbound (prevents auto-update from restoring a broken version).
- **Vision verified** — HTTP 200 from `/api/generate` with qwen2.5vl:32b-q4_K_M on Ollama 0.24.0. Pi4 assistant POST L1 PASS.

## Previous Session Changes (S108 — 2026-06-08)

- **`pi4/core/config.py`** — `TTS_MAX_CHARS=2500` (was 900). DEPLOYED+VERIFIED. md5 RAM=SD=`9d75f68d02d2a6f1cb2754d7df342b05`.
- **`pi4/services/llm.py`** — `clean_llm_reply()`: added opener/trailer/separator/list-artifact cleanup patterns. DEPLOYED+VERIFIED. md5 RAM=SD=`01b72e4c981c545bfe0cac016f8936a5`.
- **`pi4/services/vision.py`** — `ask_vision()`: HTTP 400 now returns "vision not available" message instead of raising. DEPLOYED+VERIFIED. md5 RAM=SD=`60a66d3a94310f90757d46ca1cbe5dc7`.

## Previous Session Changes (S107 — 2026-06-08)

- **`pi4/core/config.py`** — `LED_SLEEP_PEAK=8` (was 26), `LED_SLEEP_FLOOR=1` (was 3), `LED_SLEEP_BRIGHT=0xE3` (was 0xFF; 3/31 global brightness). Added `LED_SLEEP_BRIGHT` to `_OVERRIDABLE`/`_TYPE_COERCE`. DEPLOYED+VERIFIED. md5 RAM=SD=`f6f55fb58bc42532e673b334b8a04c05`.
- **`pi4/hardware/led.py`** — `show_sleep()` rewritten to read `iris_config.json` each animation cycle via `_load()`. WebUI peak/floor/period changes now take effect without service restart. DEPLOYED+VERIFIED. md5 RAM=SD=`b4a78a069bbd331ae4f73c829e86e256`.
- **`pi4/iris_web.html`** — Sleep LEDs card hint updated (no restart required, new defaults). DEPLOYED+VERIFIED. md5 RAM=SD=`b3ef97e941de491571f099df5557d140`.

## Previous Session Changes (S106 — 2026-06-07)

- **`tools/workbench/index.html`** — Latency Bench tab: added `lat-analysis-spinner`, `lat-analysis-panel`, and `lat-result-actions` action bar (Generate Handoff + Run AI Analysis). REPO-ONLY.
- **`tools/workbench/workbench.js`** — Added 5 new functions: `callAnthropicLatencyAnalysis`, `renderLatencyAnalysisPanel`, `saveLatencyBenchCases`, `runLatencyAnalysis`, `generateLatencyHandoff`. AI prompt asks for per-case tier, bottlenecks, prioritized optimizations, and new stress-test bench cases. REPO-ONLY.
- **`tools/workbench/workbench.css`** — Added `#lat-result-actions`, `#lat-analysis-spinner`, `.lat-opt-card` + header/meta/tradeoff classes. REPO-ONLY.
- **`.claude/launch.json`** — Added `autoPort: true` so preview server picks free port when 8080 is occupied. REPO-ONLY.

## Previous Session Changes (S105 — 2026-06-07)

- **`pi4/iris_web.py`** — `/api/bench` JSONL fallback added: if journalctl returns 0 cycles, reads `iris_bench.jsonl` and returns historical records to the frontend. Fixes empty Bench tab after reboots. DEPLOYED+VERIFIED. md5 RAM=SD=`856def24589ecae2e405f610db42958a`.
- **`pi4/assistant.py`** — `_bench_write()` now captures `emotion`, `tier`, `num_predict`, and `engine` in JSONL record. DEPLOYED+VERIFIED. md5 RAM=SD=`5db3b7f77ab3892ea8ec42967f168d80`.
- **`pi4/iris_bench.jsonl` (SD)** — Persisted 4 existing records to SD. Was 0 bytes since 2026-05-30.
- **`pi4/iris_bench_report.py`** — CLI comment wrong service name fixed (`iris-assistant.service` → `assistant`). REPO-ONLY.
- **`docs/bench_audit_S105.md`** — NEW. Full three-tier bench audit, gaps G1–G7, JSONL live state, architecture recommendations. REPO-ONLY.

## Previous Session Changes (S104 — 2026-06-07)

- **`pi4/assistant.py`** — Sleep-resume fix: added `if in_sleep_window(): _do_sleep(teensy, leds)` after `_play_wake_quip()` in the wakeword-during-sleep branch. DEPLOYED+VERIFIED. md5 RAM=SD=`0220719693fe3d6a6f52b0acfd46a4fa`.
- **`pi4/core/config.py`** — Mouth brightness fix: `MOUTH_INTENSITY_SLEEP = 1` → `5` (BL_MAP[1]=0.8% → BL_MAP[5]=6%). DEPLOYED+VERIFIED. md5 RAM=SD=`bfd247cc880cf2a7ad3fda790357a170`.

## Previous Session Changes (S103c — 2026-06-07)

- **`src/config.h`** — `FIRMWARE_VERSION` bumped `S100c` → `S101`. T41 reflashed. FLASHED+VERIFIED. `[VER] IRIS-EYES firmware=S101 built=Jun 7 2026` confirmed in journal.
- **S101 eye jitter fix** — mouth update rate 8Hz→2Hz during TTS now active on live hardware.

## Previous Session Changes (S103b — 2026-06-07)

- **`pi4/assistant.py`** — Wake quips system added: `_WAKE_QUIPS` (12 lines / 6 time windows), `_pre_synthesize_quips()` at startup, `_play_wake_quip()` at sleep-wake (always) and normal wakeword (rate-limited: >60min idle AND >2 wakewords since last quip). DEPLOYED+VERIFIED+PERSISTED. md5=`7aefc6a237e8ad131504586dcf8ff4a7`. All 11 unique quip lines confirmed cached in journal.

## Previous Session Changes (S103 — 2026-06-07)

- **`ollama/iris_modelfile.txt`** — FROM qwen2.5:32b (was gemma3:27b-it-qat), stop `<|im_end|>`. DEPLOYED+VERIFIED on GandalfAI.
- **`ollama/iris-kids_modelfile.txt`** — Same FROM + stop change. DEPLOYED+VERIFIED on GandalfAI.
- **GandalfAI Ollama** — Downgraded to 0.30.5. Windows Firewall rule blocks `ollama app.exe` outbound (no auto-update to 0.30.6).
- **Pi4 assistant.service** — Restarted. POST L1 Ollama models iris+iris-kids PASS.

## Previous Session Changes (S102 — 2026-06-06)

- **`ollama/iris_modelfile.txt`** — FROM gemma3:27b-it-qat (was qwen2.5vl:32b-q4_K_M), stop `<end_of_turn>`. DEPLOYED+VERIFIED on GandalfAI.
- **`ollama/iris-kids_modelfile.txt`** — Same FROM + stop change. DEPLOYED+VERIFIED on GandalfAI.
- **`pi4/services/tts.py`** — Removed `_PIPER_DIRECT_PHRASES` direct Piper routing. Kokoro-first for all text. DEPLOYED+PERSISTED. md5=`8130b382bc38699ed14cd907be641e6d`.
- **`pi4/iris_web.html`** — Vision card: "Pi Camera + Gemma" → "Pi Camera + Vision Model". DEPLOYED+PERSISTED. md5=`1fe42d456dbaec5cd3ea34b1372630fe`.
- **`iris_config.json` (live Pi4)** — Removed stale keys: EMOTION_MOUTH_MAP, EMOTION_EYE_MAP, GESTURE_PROXIMITY_THRESHOLD. md5=`19f0ed24d983d097a3c17b099b6399c3`.

**T41 status:** FLASHED S97. **T40 status:** FLASHED S97.
