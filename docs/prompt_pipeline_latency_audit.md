# IRIS Pipeline Latency Audit — Canned Claude Code Prompt
# Optimized for token efficiency. Paste as session opener.

---

TASK: Audit and optimize IRIS STT→LLM→TTS pipeline latency. Investigate causes, propose and apply targeted fixes.

REPO: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face
PI4: 192.168.1.200 (pi/ohs)
GANDALFAI: 192.168.1.3 (gandalf/5309)

---

## DISCOVERY (run all in parallel, read minimum)

**Step 1 — Git + baseline:**
```
git log --oneline -3 && git status
```

**Step 2 — Read these files (offset/limit — do NOT read full files):**
- `HANDOFF_CURRENT.md` lines 1–55 (deploy baseline + next-work)
- `pi4/core/config.py` lines 37–100 (SAMPLE_RATE, SILENCE_SECS, OWW_DRAIN_SECS, WOL_BOOT_TIMEOUT, NUM_PREDICT)
- `pi4/assistant.py` lines 44–100 (wake quip cache + _pre_synthesize_quips)
- `pi4/assistant.py` lines 580–640 (sleep-path gate + wakeword main loop entry)
- `pi4/assistant.py` lines 600–620 (beep/quip placement vs ensure_gandalf_up)

**Step 3 — Live log timing (SSH Pi4):**
```bash
journalctl -u assistant --since "2 hours ago" --no-pager -n 400 2>/dev/null \
  | grep -E "(BENCH.*stage=|dur_|wake_to|record_dur|stt_ms|llm_first|tts_ms|play_start|WOL|QUIP|SLEEP)" \
  | tail -80
```

**Step 4 — Config overrides live on Pi4:**
```bash
cat /home/pi/iris_config.json | python3 -c "
import sys,json; d=json.load(sys.stdin)
keys=['SILENCE_SECS','OWW_DRAIN_SECS','OWW_THRESHOLD','WOL_BOOT_TIMEOUT','FOLLOWUP_TIMEOUT','RECORD_SECONDS','NUM_PREDICT']
[print(f'{k}: {v}') for k,v in d.items() if k in keys]
" 2>/dev/null || echo "no overrides in iris_config.json"
```

**Step 5 — Recent bench records:**
```bash
cat /home/pi/iris_bench.jsonl 2>/dev/null | tail -10 || echo "no bench data"
```

---

## KNOWN BOTTLENECKS (historical — verify each still applies)

| # | Bottleneck | Location | Typical cost | Fix/status |
|---|-----------|----------|-------------|------------|
| B1 | `ensure_gandalf_up()` before RPQR quip | `assistant.py:593` | 0–120s | **BUG: quip is pre-cached PCM, needs no Gandalf** |
| B2 | `ensure_gandalf_up()` before wakeword beep | `assistant.py:604` | 0–120s | Beep has no audio feedback until Gandalf confirms up |
| B3 | `SILENCE_SECS = 1.5s` | `config.py:42` | +1.5s per turn | Could tighten to 1.0s (risk: cuts speech early) |
| B4 | `WOL_BOOT_TIMEOUT = 120s` | `config.py:175` | Up to 120s | Necessary but could reduce to 90s |
| B5 | Whisper STT remote call | `services/stt.py` | 1–3s | Pi4-side: nothing to optimize |
| B6 | Kokoro TTS remote call | `services/tts.py` | 1–3s | Pi4-side: nothing to optimize |
| B7 | LLM cold-start (no warmup) | `assistant.py:521` | 10–12s | Warmup at startup (S106). Check if skipped. |
| B8 | `NUM_PREDICT=300` default | `config.py:91` | varies | Tiered (S106): SHORT=120, MEDIUM=350, LONG=700 |
| B9 | `OWW_DRAIN_SECS = 0.15s` | `config.py:180` | 0.15s | Fine — already low |
| B10 | `RECORD_SECONDS = 10s` max | `config.py:41` | worst-case 10s | Fine — silence detection cuts it short |

---

## RPQR TRIGGER STATUS (Rapid Pre-canned Quick Responses)

Implemented (pre-cached at startup via `_pre_synthesize_quips`):
- [x] Time-of-day wake quips (5 time bands, 2 lines each, `_WAKE_QUIPS`)
- [x] Once-per-hour quip (after 1h inactivity + >2 interactions)

NOT implemented (from original RPQR design session):
- [ ] Double-tap — wakeword within 30s of previous wakeword: "Still here. Haven't moved."
- [ ] Post-speech — wakeword < 5s after IRIS finished speaking: "I literally just answered that."
- [ ] Top-of-hour — wakeword within ±2 min of XX:00: "[H] o'clock. That's the whole thought."
- [ ] First-of-day — first wakeword before 09:00: "Morning." / after 09:00: "Finally."
- [ ] Late-night specific — 00:00–05:00 with actual time: "It's [TIME]. Go to sleep."

All new RPQR triggers should: fire BEFORE `ensure_gandalf_up()`, play pre-cached PCM, then continue loop (no STT/LLM).

---

## FIX TEMPLATE (apply only after proposing to user)

### Fix 1 — RPQR sleep path (critical, ~5 lines changed)
File: `pi4/assistant.py` lines 589–598

REMOVE `ensure_gandalf_up()` from sleep-wakeword branch entirely.
Sleep quip path never needs Gandalf — quip is pre-cached PCM, then re-sleeps.

```python
# BEFORE (lines 589–598):
if os.path.exists('/tmp/iris_sleep_mode'):
    print('[SLEEP] Wakeword during sleep -- waking IRIS', flush=True)
    _do_wake(teensy, leds)
    if not ensure_gandalf_up(leds, pa):
        leds.show_error(); time.sleep(2); show_idle_for_mode(leds); continue
    _play_wake_quip(time.localtime().tm_hour, pa, teensy, leds)
    if in_sleep_window():
        _do_sleep(teensy, leds)
    show_idle_for_mode(leds); continue

# AFTER:
if os.path.exists('/tmp/iris_sleep_mode'):
    _do_wake(teensy, leds)
    _play_wake_quip(time.localtime().tm_hour, pa, teensy, leds)
    if in_sleep_window():
        _do_sleep(teensy, leds)
    show_idle_for_mode(leds); continue
```

### Fix 2 — Immediate beep before Gandalf check (minor UX improvement)
File: `pi4/assistant.py` lines 600–617

Move `play_beep(pa)` call to BEFORE `ensure_gandalf_up()` so user gets instant audio ACK.
The quip (once-per-hour path) also moves before the Gandalf gate.
After the beep/quip, Gandalf check proceeds normally.

### Fix 3 — Add double-tap RPQR trigger (new feature)
Needs: `_t_last_wake = 0.0` module-level tracker
Check: if `time.time() - _t_last_wake < 30` → play "Still here." → continue
Update `_t_last_wake` at every wakeword detection

### Fix 4 — Add post-speech RPQR trigger (new feature)  
Needs: `_t_last_spoke = 0.0` module-level tracker, update after every `play_pcm_speaking`
Check: if `time.time() - _t_last_spoke < 5` → play "I literally just answered that." → continue

### Fix 5 — Add top-of-hour RPQR trigger (new feature, requires pre-caching)
Pre-cache 12 variants: "One o'clock. That's the whole thought." through "Twelve o'clock..."
Check: if `abs(time.localtime().tm_min - 0) <= 2` and not fired in last 10 min → play
Needs: `_t_last_top_of_hour = 0.0` tracker

### Fix 6 — Add first-of-day RPQR trigger (new feature)
Needs: `_first_interaction_date = None` tracker
Check: if date != today → fire "Morning." (< 09:00) or "Finally." (>= 09:00), then set date

### Fix 7 — Tighten SILENCE_SECS (config-only, -0.5s/turn)
Change in iris_config.json: `"SILENCE_SECS": 1.0` (from 1.5)
Risk: may cut off slower speakers. Monitor for 1 session, revert if problems.

---

## DEPLOY SEQUENCE (after fixes applied)

```bash
# Pi4 deploy
scp pi4/assistant.py pi@192.168.1.200:/home/pi/assistant.py
ssh pi@192.168.1.200 "sudo cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py && md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py"
ssh pi@192.168.1.200 "sudo systemctl restart assistant"
# Verify
ssh pi@192.168.1.200 "journalctl -u assistant -n 30 --no-pager"
```

---

## QUICK BENCH CHECK (run after any live change)
```bash
# Trigger 3 interactions, then:
ssh pi@192.168.1.200 "journalctl -u assistant --since '5 minutes ago' --no-pager \
  | grep -E 'BENCH.*stage=(stt_done|tts|play_start)' | tail -20"
```

---

## SESSION CLOSE CHECKLIST
- [ ] assistant.py DEPLOYED to /home/pi/ AND /media/root-ro/home/pi/
- [ ] md5 RAM=SD verified
- [ ] service restarted + journal checked
- [ ] SILENCE_SECS change noted in CHANGELOG
- [ ] SNAPSHOT_LATEST.md updated with new RPQR trigger list
