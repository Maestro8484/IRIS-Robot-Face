# Task 2 — Config and Persistence Gap Audit

**Date:** 2026-05-16
**Reviewer:** Opus 4.7
**Scope:** Config key coverage, chown gaps, startup-only reads, stale keys, persistence pattern compliance

---

## 1. IRIS_CONFIG_MAP.md vs `_OVERRIDABLE` Cross-Reference

`_OVERRIDABLE` source: `pi4/core/config.py:170-184`.

| Key | In IRIS_CONFIG_MAP.md | In _OVERRIDABLE | Match |
|---|---|---|---|
| RECORD_SECONDS | Yes (Audio) | Yes | ✅ |
| SILENCE_SECS | Yes (Audio) | Yes | ✅ |
| SILENCE_RMS | Yes (Audio) | Yes | ✅ |
| KIDS_RECORD_SECONDS | Yes (Audio) | Yes | ✅ |
| KIDS_SILENCE_SECS | Yes (Audio) | Yes | ✅ |
| KIDS_SILENCE_RMS | Yes (Audio) | Yes | ✅ |
| OWW_THRESHOLD | Yes (Wake Word) | Yes | ✅ |
| OWW_DRAIN_SECS | Yes (Wake Word) | Yes | ✅ |
| WAKE_WORD | Yes (Wake Word, read-only note) | **No** | ❌ Doc says it's "stored in iris_config.json"; code does not override it |
| KOKORO_ENABLED | Yes (Voice) | Yes | ✅ |
| KOKORO_VOICE | Yes (Voice) | Yes | ✅ |
| CHATTERBOX_ENABLED | Yes (Voice, rollback) | Yes | ✅ |
| CHATTERBOX_VOICE | Yes (Voice, rollback) | Yes | ✅ |
| CHATTERBOX_EXAGGERATION | Yes (Voice, rollback) | Yes | ✅ |
| FOLLOWUP_TIMEOUT | Yes (Conversation) | Yes | ✅ |
| KIDS_FOLLOWUP_TIMEOUT | Yes (Conversation) | Yes | ✅ |
| FOLLOWUP_MAX_TURNS | Yes (Conversation) | Yes | ✅ |
| CONTEXT_TIMEOUT_SECS | Yes (Conversation) | Yes | ✅ |
| NUM_PREDICT_SHORT | Yes (Conversation) | Yes | ✅ |
| NUM_PREDICT_MEDIUM | Yes (Conversation) | Yes | ✅ |
| NUM_PREDICT_LONG | Yes (Conversation) | Yes | ✅ |
| NUM_PREDICT_MAX | Yes (Conversation) | Yes | ✅ |
| TTS_MAX_CHARS | Yes (Conversation) | Yes | ✅ |
| OLLAMA_MODEL_ADULT | Yes (Gandalf AI) | Yes | ✅ |
| OLLAMA_MODEL_KIDS | Yes (Gandalf AI) | Yes | ✅ |
| MOUTH_INTENSITY_AWAKE | Yes (Sleep) | Yes | ✅ |
| MOUTH_INTENSITY_SLEEP | Yes (Sleep) | Yes | ✅ |
| LED_SLEEP_PEAK | Yes (Sleep) | Yes | ✅ |
| LED_SLEEP_FLOOR | Yes (Sleep) | Yes | ✅ |
| LED_SLEEP_PERIOD | Yes (Sleep) | Yes | ✅ |
| LED_IDLE_PEAK | Yes (Lights) | Yes | ✅ |
| LED_IDLE_FLOOR | Yes (Lights) | Yes | ✅ |
| LED_IDLE_PERIOD | Yes (Lights) | Yes | ✅ |
| LED_KIDS_PEAK | Yes (Lights) | Yes | ✅ |
| LED_KIDS_PERIOD | Yes (Lights) | Yes | ✅ |
| SPEAKER_VOLUME | Yes (System) | Yes | ✅ |
| VOL_MAX | Yes (System) | Yes | ✅ |
| NUM_PREDICT (legacy) | Stale Keys section | Yes | ⚠ Listed stale but still overridable (intentional fallback) |

### Gap finding

- **File:** `pi4/core/config.py`
- **Lines:** 28, 170-184
- **Severity:** LOW
- **Issue:** `WAKE_WORD` is described in `IRIS_CONFIG_MAP.md` as "stored in iris_config.json and shown read-only on the Wake Word tab" but is NOT in `_OVERRIDABLE`. Setting `WAKE_WORD` in iris_config.json has no effect — the value falls through to the "ignored unknown keys" warning at line 234. The doc implies a JSON value exists and is respected; the code ignores any value provided.
- **Fix direction:** Either add `WAKE_WORD` to `_OVERRIDABLE` (string passthrough; no `_TYPE_COERCE` entry needed), or update IRIS_CONFIG_MAP.md to state that WAKE_WORD changes require a `core/config.py` edit and assistant restart.

---

## 2. iris_web.py Write Routes — chown Audit

Per IRIS_ARCH.md "Operational Notes" the `api_persist_config` ownership bug requires `chown pi:pi` after any sudo-cp to `iris_config.json`, otherwise the pipeline silently breaks on the next reboot (S22B post-mortem).

### Route: `/api/config` (POST) — `iris_web.py:80-82`

```python
if request.method == "POST":
    write_cfg(request.get_json(force=True)); return jsonify(ok=True)
```

`write_cfg` (lines 26-29) does direct `open(CONFIG_FILE, "w")` from the iris-web service. Per README service table, iris-web runs as user `pi`. No sudo — owner stays `pi:pi`.

- **Severity:** N/A — non-sudo write, owner preserved.

### Route: `/api/persist_config` (POST) — `iris_web.py:280-302`

```python
result = subprocess.run(
    ["sudo", "bash", "-c",
     f"mount -o remount,rw /media/root-ro && "
     f"cp {CONFIG_FILE} {SD_CONFIG} && "
     f"mount -o remount,ro /media/root-ro"],
    ...)
```

- **File:** `pi4/iris_web.py`
- **Lines:** 281-285
- **Severity:** HIGH
- **Issue:** `sudo cp /home/pi/iris_config.json /media/root-ro/home/pi/iris_config.json` runs as root. The resulting SD-layer copy is owned `root:root`. **There is no `chown pi:pi` after the cp.** IRIS_ARCH.md explicitly: "Any route doing `sudo cp` to `iris_config.json` must immediately follow with `sudo chown pi:pi /home/pi/iris_config.json`. Ownership corruption silently breaks the entire assistant pipeline on next deploy. Root cause of April 16-18 failure cascade (S22B post-mortem)."

  The live RAM-layer copy at `/home/pi/iris_config.json` is unchanged by this route (it's the source, not the target), so the *current* boot is not broken. But on next reboot the overlayfs RAM layer is cleared and the SD layer becomes live — at which point ownership is `root:root` and the documented failure mode triggers.

  The route additionally omits the `chmod 644` step from the canonical pattern (IRIS_ARCH.md "Pi4 Persistence"). The md5 verification step IS present via `_sd_synced()` (line 290).
- **Fix direction:** Extend the sudo bash command:
  ```
  mount -o remount,rw /media/root-ro && \
  cp {CONFIG_FILE} {SD_CONFIG} && \
  chown pi:pi {SD_CONFIG} && \
  chmod 644 {SD_CONFIG} && \
  sync && \
  mount -o remount,ro /media/root-ro
  ```

### Route: `/api/persist_config` (continued) — ALSA state — `iris_web.py:293-298`

```python
alsa_result = subprocess.run(
    ["sudo", "bash", "-c",
     f"mount -o remount,rw /media/root-ro && "
     f"cp {alsa_src} {alsa_dst} && "
     f"mount -o remount,ro /media/root-ro"],
    ...)
```

- **File:** `pi4/iris_web.py`
- **Lines:** 293-298
- **Severity:** LOW
- **Issue:** Same canonical-pattern deviation. ALSA state at `/var/lib/alsa/asound.state` is normally `root:root` by system convention — leaving the SD copy `root:root` is *correct* for ALSA. But `sync` is omitted before the read-only remount, and there is no md5 check on this copy. If the read-only remount lands before the kernel flushes the cp buffer, the SD copy may be incomplete.
- **Fix direction:** Add `sync` before the `mount -o remount,ro`. md5 verification optional but advisable.

### Route: `/api/sleep`, `/api/wake` — `iris_web.py:92-104`

Open/remove `/tmp/iris_sleep_mode` from iris-web running as `pi`. No sudo, no chown concerns.

### Route: `/api/volume` (POST) — `iris_web.py:273-280`

amixer + alsactl store + direct file write to `iris_config.json`. No sudo, no chown concerns for the iris_config.json write (already pi-owned).

### Summary table

| Route | sudo cp | chown present | Severity |
|---|---|---|---|
| /api/config POST | No | N/A | OK |
| /api/persist_config (iris_config.json) | **Yes** | **No** | **HIGH** |
| /api/persist_config (ALSA state) | Yes | No (intentional — root-owned by design) | LOW (missing sync) |
| /api/sleep, /api/wake | No | N/A | OK |
| /api/volume POST | No | N/A | OK |

---

## 3. Startup-Only Reads vs Documented Restart-Free Keys

`core/config.py` reads `iris_config.json` once at import time (lines 215-245) and assigns each override to a module-level global via `globals()[_k] = _coerced` (line 226). Whether a runtime config edit takes effect depends entirely on how the consumer reads the value:

- `from core.config import KEY` at module top: name bound to the value at consumer-import time; subsequent `globals()` mutation of `core.config.KEY` does NOT update the consumer's binding.
- `import core.config` followed by `core.config.KEY` at use-site: re-reads each time.
- Lazy `from core.config import KEY` inside a function body: re-reads on each function call.

The web UI promises "instant" or "no restart" behavior for several keys. Audit:

| Key | UI / Doc claim | Consumer pattern | Reality |
|---|---|---|---|
| `OWW_THRESHOLD` | "No restart" (CONFIG_MAP wyoming table) | Passed as CLI arg to wyoming-openwakeword subprocess (assistant.py:255-258) | **Subprocess-baked; requires assistant restart to relaunch wyoming** |
| `OWW_DRAIN_SECS` | "No restart" (CONFIG_MAP) | Read at use-site in assistant.py:318 via `from core.config import *` at line 25 | **Bound at startup** |
| `NUM_PREDICT_SHORT/MEDIUM/LONG/MAX` | "No restart" (Conversation tab) | Lazy `from core.config import NUM_PREDICT_SHORT as _S, ...` inside `classify_response_length` (llm.py:213-218) | **Re-read per call ✅** |
| `TTS_MAX_CHARS` | UI implies instant | Used as default arg `max_chars: int = TTS_MAX_CHARS` in `_truncate_for_tts` (tts.py:118) — defaults evaluated at function-def time | **Bound at startup** |
| `MOUTH_INTENSITY_AWAKE/SLEEP` | "Save & Apply Now changes brightness immediately without restart" (GUIDE-settings.md / Sleep tab) | Used in `_do_sleep` / `_do_wake` (assistant.py:224, 234) via top-level `from core.config import *` | **Bound at startup — UI claim is false** |
| `LED_IDLE_PEAK/FLOOR/PERIOD`, `LED_KIDS_PEAK/PERIOD` | "Requires assistant restart" (GUIDE-settings.md) | Lazy `from core.config import LED_IDLE_PEAK, ...` inside `show_idle().anim()` (led.py:58, 71) | **Re-read on each animation start — UI claim is *over-conservative*** |
| `LED_SLEEP_PEAK/FLOOR/PERIOD` | "Requires assistant restart" (GUIDE-settings.md) | Top-level `from core.config import LED_SLEEP_PEAK, ...` at led.py:14 | **Bound at startup — matches UI claim** |
| `SPEAKER_VOLUME` | "Takes effect immediately" (System tab) | Read once at boot (assistant.py:242) as `_startup_vol`. Web UI volume changes go direct via `amixer` (iris_web.py:273-278), bypassing config.py | **OK — immediate via amixer; config value is only the boot default** |
| `KOKORO_VOICE`, `KOKORO_ENABLED` | UI implies instant | `from core.config import KOKORO_BASE_URL, KOKORO_VOICE, KOKORO_ENABLED, ...` at tts.py:16-20 — bound at module load | **Bound at startup** |
| `VOL_MAX` | (System tab) | `from core.config import ..., VOL_MIN, VOL_MAX, VOL_STEP` at audio_io.py:21-25 — bound at startup | **Bound at startup** |
| `FOLLOWUP_TIMEOUT`, `KIDS_FOLLOWUP_TIMEOUT`, `FOLLOWUP_MAX_TURNS`, `CONTEXT_TIMEOUT_SECS` | UI implies instant | `from core.config import *` in assistant.py:25 — bound at startup | **Bound at startup** |
| `RECORD_SECONDS`, `SILENCE_SECS`, `SILENCE_RMS` (and KIDS_*) | UI implies instant | `from core.config import ... RECORD_SECONDS, SILENCE_SECS, ...` at audio_io.py:21-25 — bound at startup | **Bound at startup** |

### Gap findings

- **File:** `pi4/services/wakeword.py` + `pi4/assistant.py`
- **Lines:** wakeword.py:18, assistant.py:255-258
- **Severity:** MED
- **Issue:** `OWW_THRESHOLD` is baked into the wyoming-openwakeword subprocess command line at assistant boot. Changing the value via web UI does nothing until assistant restart (which relaunches wyoming). CONFIG_MAP table "Pi4 — wyoming-openwakeword" labels `OWW_THRESHOLD` as "Restart needed: No" — incorrect.
- **Fix direction:** Update CONFIG_MAP `Restart needed` cell to "Yes — wyoming restarts on assistant restart". (Note: `wakeword.py:76` references `OWW_THRESHOLD` only for the `[OWW]` log line; the actual threshold filter is inside the wyoming subprocess.)

---

- **File:** `pi4/services/tts.py`
- **Lines:** 16, 118
- **Severity:** LOW
- **Issue:** `TTS_MAX_CHARS` is bound as a default argument value at function-def time. Web UI edits to TTS_MAX_CHARS do not take effect until assistant restart.
- **Fix direction:** `def _truncate_for_tts(text: str, max_chars: int = None):` and inside the function `if max_chars is None: from core.config import TTS_MAX_CHARS; max_chars = TTS_MAX_CHARS`.

---

- **File:** `pi4/assistant.py`
- **Lines:** 224, 234
- **Severity:** MED
- **Issue:** `MOUTH_INTENSITY_AWAKE` and `MOUTH_INTENSITY_SLEEP` are used inside `_do_sleep` and `_do_wake` from the module-level `from core.config import *` binding (line 25). Web UI claim "Save & Apply Now changes immediately without restart" (GUIDE-settings.md Sleep tab) is false — values are bound at assistant startup.
- **Fix direction:** Lazy-read at use-site: `from core.config import MOUTH_INTENSITY_AWAKE` inside `_do_wake`, similarly for `_do_sleep`.

---

- **File:** `pi4/hardware/led.py`
- **Lines:** 13, 95-97
- **Severity:** LOW
- **Issue:** `LED_SLEEP_PEAK`, `LED_SLEEP_FLOOR`, `LED_SLEEP_PERIOD`, `LED_SLEEP_BRIGHT` imported at module top — bound at startup. Inconsistent with `LED_IDLE_*` and `LED_KIDS_*` which are lazy-imported inside the anim closures (lines 58, 71). Functionally matches GUIDE-settings.md ("Requires assistant restart"), but the inconsistency is a maintenance hazard: a future change to make sleep LED dynamic would need to know about this asymmetry.
- **Fix direction:** Move the LED_SLEEP_* import inside `show_sleep().anim()` for consistency.

---

## 4. Stale / Orphan Keys Audit

### MOUTH_INTENSITY

- **In config.py:** Not present. `MOUTH_INTENSITY_AWAKE` and `MOUTH_INTENSITY_SLEEP` exist (lines 132-133); the bare key does not.
- **In _OVERRIDABLE:** No.
- **In iris_web.py:** `MOUTH_INTENSITY:n` appears as a *Teensy serial command* (lines 99-103 — sent via UDP), not as a config key being read/written. No config reference.
- **In other pi4/* files:** None.
- **Status:** Safe to delete from any live `iris_config.json`. No code reads the bare key. CONFIG_MAP correctly flags it as "Dead key — not in _OVERRIDABLE".

### ELEVENLABS_ENABLED

- **In config.py:** No references.
- **In _OVERRIDABLE:** No.
- **In iris_web.py:** No references.
- **In any pi4/*:** None.
- **Status:** Safe to delete. If present in live iris_config.json, the load-time block logs it under "ignored unknown keys" (config.py:234-235). CONFIG_MAP correctly flags as removed S20.

### NUM_PREDICT (legacy)

- **In config.py:** Yes — line 76, default 300. Listed in `_OVERRIDABLE` (line 173). `_TYPE_COERCE` entry at line 152 (int, 10-2000).
- **In iris_web.py:** Read by `/api/config` GET via the `_OVERRIDABLE` enumeration (line 86); not specifically referenced by name elsewhere in iris_web.
- **In other pi4/*:** Used in `ask_ollama` (assistant.py:117) as a fallback when `num_predict=None` is passed. In practice, every caller of `ask_ollama` in the follow-up loop passes `num_predict=_followup_predict` (assistant.py:614) — the bare `NUM_PREDICT` default is only used if a caller omits the arg. Currently no such caller exists in the code.
- **In iris_config.json:** Per SNAPSHOT_LATEST.md S48 entry, this key was REMOVED from the live Pi4 iris_config.json in S48 ("`NUM_PREDICT: 200` key removed"). IRIS_ARCH.md "Key Constants" still documents `NUM_PREDICT = 150 # overridden to 120 by iris_config.json` — stale doc text (the override is gone post-S48).
- **Status:** Code-side it remains a live fallback (still has consumers, even if currently dead). Docs are stale.
- **Cross-reference Task 6.**

---

## 5. Overlayfs Persistence Pattern Compliance

Canonical pattern (IRIS_ARCH.md "Pi4 Overlayfs Deployment Principle"):

```bash
sudo mount -o remount,rw /media/root-ro
sudo cp /home/pi/<file> /media/root-ro/home/pi/<file>
sudo chown pi:pi /media/root-ro/home/pi/<file>
sudo chmod 644 /media/root-ro/home/pi/<file>
sync
sudo mount -o remount,ro /media/root-ro
md5sum /home/pi/<file> /media/root-ro/home/pi/<file>
```

The only route in iris_web.py that persists files is `/api/persist_config` (lines 280-302). It runs the operation as two separate sudo bash invocations: one for iris_config.json, one for ALSA state. Cross-reference each step against the canonical pattern:

### iris_config.json persistence (lines 281-285)

| Canonical step | Implementation | Match |
|---|---|---|
| `mount -o remount,rw /media/root-ro` | Present | ✅ |
| `cp src dst` | Present | ✅ |
| `chown pi:pi dst` | **Absent** | ❌ |
| `chmod 644 dst` | **Absent** | ❌ |
| `sync` | **Absent** | ❌ |
| `mount -o remount,ro /media/root-ro` | Present | ✅ |
| `md5sum` verification | Performed by `_sd_synced()` (called at line 290 after the bash run) | ✅ |

- **File:** `pi4/iris_web.py`
- **Lines:** 281-285
- **Severity:** HIGH (chown missing — already flagged in Section 2)
- **Issue:** Three deviations from canonical pattern: missing `chown pi:pi`, missing `chmod 644`, missing `sync`. The `chown` omission is the documented S22B failure mode. The `sync` omission can produce a write that the read-only remount races with — the SD copy may not be fully flushed when `_sd_synced()` runs md5 verification, producing a false "unsynced" status or, worse, a partial write persisted to SD.
- **Fix direction:** Extend the bash command to the full canonical sequence.

### ALSA state persistence (lines 293-298)

| Canonical step | Implementation | Match |
|---|---|---|
| `mount -o remount,rw` | Present | ✅ |
| `cp src dst` | Present | ✅ |
| `chown` | Absent | ⚠ Intentional (ALSA state is root-owned by system convention) |
| `chmod` | Absent | ⚠ Intentional |
| `sync` | **Absent** | ❌ |
| `mount -o remount,ro` | Present | ✅ |
| `md5sum` | **Absent** | ❌ |

- **File:** `pi4/iris_web.py`
- **Lines:** 293-298
- **Severity:** LOW
- **Issue:** chown / chmod omission is correct (ALSA state ownership/perms differ from user files). But `sync` is missing — same race risk as above. md5 verification is also missing for this file — `_sd_synced()` only checks iris_config.json (line 35), not ALSA state. The route returns `alsa_persisted=alsa_ok` based on the subprocess return code, not on actual SD-layer content match.
- **Fix direction:** Add `sync` before the read-only remount. Optionally extend `_sd_synced()` to also verify ALSA state, or perform a separate md5 check inline.

### Other write paths

No other iris_web.py routes touch the SD layer. `iris_sleep.py` and `iris_wake.py` write only to `/tmp/iris_sleep_mode` (a tmpfs file that does not need overlayfs persistence). `/api/volume` (line 278) calls `alsactl store` which writes the RAM-layer `/var/lib/alsa/asound.state` — that file requires the `/api/persist_config` route to be called separately to reach SD. This is documented behavior, not a defect.

---

## Summary

- **HIGH:** 1 (api_persist_config missing chown — documented failure mode, S22B repeat risk)
- **MED:** 3 (OWW_THRESHOLD subprocess-baked but doc says no-restart; MOUTH_INTENSITY_AWAKE/SLEEP bound at startup but UI promises instant; WAKE_WORD documented overridable but not in _OVERRIDABLE)
- **LOW:** 4 (TTS_MAX_CHARS default-arg binding; LED_SLEEP_* import inconsistency; ALSA persist missing sync; ALSA persist missing md5)

The configuration system is functionally correct on the happy path. The recurring pattern is **doc drift on dynamic-vs-static behavior**: several keys are described as taking effect immediately when they actually require an assistant restart. The S22B chown bug pattern is reproduced verbatim in the current iris_web.py persist route — this is the highest-priority finding in this task.

*End Task 2.*
