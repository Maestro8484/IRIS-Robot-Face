# S42 Log Audit + Interrupt Fix — Findings

**Date:** 2026-04-26  
**Log coverage:** journald only holds today's boot (Pi4 rebooted today). Two interactions captured.

---

## CONFIRMED: Formal AI response on "Go to sleep"

```
[STT]  'Go to sleep'
[LLM]  Streaming... (model=iris, num_predict=350)
[LLM]  'Okay! As a large language model, I don't need to sleep, but I understand
        you're playfully suggesting I power down. Consider me "offline" for now.
        Goodnight! I'll be here when you need me again. ✨'
```

**Root cause — two compounding failures:**

1. `"go to sleep"` is NOT in `EYES_SLEEP_TRIGGERS` (that set only has eye-specific phrases like "close your eyes", "turn off your eyes"). No sleep command handler exists. The phrase falls through to the LLM.

2. gemma3's safety alignment fires on "go to sleep" → produces the boilerplate "as a large language model" disclaimer, overriding the persona. The modelfile has "You never step outside this character" but gemma3 treats this as a consciousness/capability question and breaks character anyway.

**Fix plan:** Two-part.
- Part A: Add `SLEEP_TRIGGERS` set to config + handler in assistant.py. Intercepts "go to sleep", "goodnight", "sleep", etc. BEFORE the LLM path. Calls `_do_sleep()` and synthesizes a short in-character response.
- Part B: Strengthen modelfile with an explicit prohibition on "as a large language model" style responses + in-character sleep handling guidance.

---

## CONFIRMED: Response length tier not calibrated for sleep/goodbye phrases

```
"Go to sleep"          → tier=MEDIUM (num_predict=350)  ← wrong; will be fixed by Part A above
"I'll see you next time" → tier=MEDIUM (num_predict=350) ← plausible but SHORT is better
```

`classify_response_length()` in `services/llm.py` has no entries for goodnight/goodbye/sleep phrases in `_SHORT_PATTERNS`. "go to sleep" — 3 words, no `?`, not in SHORT → defaults to MEDIUM.

**Fix:** Add sleep/goodbye phrases to `_SHORT_PATTERNS`. This is a backstop — the handler fix (Part A) prevents them reaching the classifier at all.

---

## CONFIRMED: Interrupt mechanism exists but threshold is unreachable at high volume

```
[INT]  Bleed baseline RMS=4647   eff_threshold=18589    (4.0x bleed)
[INT]  Bleed baseline RMS=10674  eff_threshold=42695    (4.0x bleed)
```

The `_VOICE_MULTIPLIER = 4.0` was correct when IRIS's speaker bleed was 1200–4500 RMS. At current VOL_MAX (110/127), bleed reads 4647–10674. The resulting thresholds (18k–42k) exceed even a shouting voice.

The interrupt DID fire once today — that was likely the user speaking very loudly, not a "stop" phrase. The mechanism works, but normal-volume "stop" won't reach the threshold.

**Fix: STT-verified interrupt.** 
- Detect voice at `bleed_rms * 1.5` (lower trigger threshold — catches normal voice)
- Collect ~1.5s of audio
- Run STT (Whisper on GandalfAI, ~0.2–0.5s roundtrip) in background thread
- If transcript matches `STOP_PHRASES` → fire `_stop_playback`
- If not (noise, cough, bleed spike) → discard and keep monitoring

This is the correct fix because: (a) it works regardless of speaker volume, (b) it eliminates false positives from slams/coughs, (c) "stop" at normal voice reliably triggers.

---

## NOT CONFIRMED: Wakeword false fires

journald only holds today's boot. Today: 2 wakeword events, both scored 1.000 confidence. No false fires in available data. Cannot assess 30-day history — would need persistent log file to have retained it.

---

## Plan: Files to touch

| File | Change |
|---|---|
| `pi4/core/config.py` | Add `SLEEP_TRIGGERS` set |
| `pi4/assistant.py` | Add sleep command handler before LLM path |
| `pi4/services/llm.py` | Add goodbye/sleep phrases to `_SHORT_PATTERNS` |
| `pi4/hardware/audio_io.py` | STT-verified interrupt (replace RMS-only approach) |
| `ollama/iris_modelfile.txt` | Explicit anti-AI-disclaimer + sleep behavior guidance |

---

## "I'll see you next time" response quality issue (secondary)

```
[LLM]  'It was good chatting with you. Have a wonderful evening and I look forward
        to speaking with you again soon. Is there anything I can help you with before
        we finish up for now? Just let me know. Otherwise, goodbye!'
```

This is extremely un-IRIS — verbose, saccharine, ends with a question (which triggers the follow-up loop). IRIS's character would be something like "Later." or "See you." This is a model temperature/persona issue. The modelfile fix (Part B) should address it via strengthened brevity instructions for goodbye-type inputs. Not adding a hard-coded goodbye handler.
