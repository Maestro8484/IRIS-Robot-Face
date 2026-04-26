# Wakeword Baseline Handoff - S35

## Status

Production wakeword is restored to:

```text
hey_jarvis
```

The custom wakeword deployment attempt is paused and treated as experimental history.

---

## What Was Tried

Custom wakeword candidates:

- `hey_der_iris`
- `real_quick_iris`

Goal:

Replace `hey_jarvis` with IRIS-specific wake phrases.

Outcome:

Both failed practical real-world reliability expectations. The system was reverted to `hey_jarvis`.

---

## Current Decision

Do not deploy custom wakewords right now.

`hey_jarvis` remains the stable production baseline.

Custom wakeword tooling and docs are preserved because they may be useful later, but they are not active deployment instructions.

---

## Known Problems From Attempt

Possible causes of failure:

- Synthetic or TTS-generated positive samples did not match real household voices.
- The phrase `hey_der_iris` was awkward in real use and likely weaker phonetically.
- Testing multiple custom wakewords complicated diagnosis.
- Old wyoming-openwakeword process state may have kept `hey_jarvis` active during testing.
- Custom model format and deployment state became unclear across ONNX and TFLite attempts.

---

## Active Task If Continued

Audit current Pi4 wakeword state read-only.

Required checks:

```bash
ps aux | grep -i wyoming
ss -ltnp | grep 10400
cat /home/pi/iris_config.json
ls -lah /home/pi/wyoming-openwakeword/custom/
grep -n "WAKE_WORD\|custom-model-dir\|preload-model\|hey_jarvis\|hey_der_iris\|real_quick_iris" /home/pi/assistant.py
grep -n "WAKE_WORD\|hey_jarvis" /home/pi/core/config.py
```

No edits.
No restarts.
No deploy.
No GitHub push.

---

## Rollback Target

Stable target:

```text
WAKE_WORD = hey_jarvis
```

Expected behavior:

- Wakeword process uses stock OpenWakeWord `hey_jarvis`.
- Custom wakeword models are not required for production.
- IRIS wakes reliably using `hey_jarvis`.

---

## Future Custom Wakeword Strategy

If custom wakeword work resumes:

1. Use one custom wakeword only.
2. Prefer `hello_iris` or another clean phrase over `hey_der_iris`.
3. Collect real household voice samples.
4. Train against real negatives from the room.
5. Test offline first.
6. Deploy to Pi4 only after offline model validation.
7. Kill all old wyoming-openwakeword processes before testing.
8. Confirm port 10400 owner.
9. Confirm active process command line.
10. Confirm logs show the intended model loaded.
11. Run real-world wake testing.
12. Keep `hey_jarvis` rollback ready.

---

## Files Not To Touch Without Explicit Approval

- `iris_config.json`
- `assistant.py`
- `core/config.py`
- `services/wakeword.py`
- Pi4 live files
- GandalfAI live files
- Teensy firmware

---

## Commit Guidance

Recommended commit for documentation cleanup:

```text
S35: restore hey_jarvis wakeword baseline
```

Recommended later commit for preserving tooling:

```text
S36: preserve experimental wakeword training tooling
```
