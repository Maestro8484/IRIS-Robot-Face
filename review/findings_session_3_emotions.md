# Task 3 — Emotion System Integrity Audit

**Date:** 2026-05-16
**Reviewer:** Opus 4.7
**Scope:** Emotion consistency across config.py, led.py, llm.py, src/main.cpp, IRIS_ARCH.md / README.md

---

## 1. Coverage Matrix

Sources read:
- `pi4/core/config.py` — `VALID_EMOTIONS` (line 142), `MOUTH_MAP` (lines 143-153)
- `pi4/hardware/led.py` — `_EMOTION_LED` dict (lines 132-141) and `show_emotion()` special cases (lines 144-160)
- `pi4/services/llm.py` — `extract_emotion_from_reply()` (lines 18-29) — uses `VALID_EMOTIONS`
- `src/main.cpp` — `EmotionID` enum (line 69), `emotionTable` (lines 71-81), `parseEmotion()` (lines 161-170), `applyEmotion()` (lines 173-195)
- `IRIS_ARCH.md` Serial Protocol (line 568); `README.md` Emotion System table (lines 121-130) and Mouth Display table (lines 89-100)

| Emotion | config VALID_EMOTIONS | config MOUTH_MAP | led.py | llm.py extract | main.cpp enum | main.cpp emotionTable | main.cpp parseEmotion | main.cpp applyEmotion | IRIS_ARCH.md | README.md |
|---|---|---|---|---|---|---|---|---|---|---|
| NEUTRAL | ✅ | ✅ (0) | ✅ (dict) | ✅ | ✅ (=0) | ✅ | ✅ (default return) | ✅ (else) | ✅ | ✅ |
| HAPPY | ✅ | ✅ (1) | ✅ (dict) | ✅ | ✅ (=1) | ✅ | ✅ | ✅ (else) | ✅ | ✅ |
| CURIOUS | ✅ | ✅ (2) | ✅ (dict) | ✅ | ✅ (=2) | ✅ | ✅ | ✅ (else) | ✅ | ✅ |
| ANGRY | ✅ | ✅ (3) | ✅ (dict) | ✅ | ✅ (=3) | ✅ | ✅ | ✅ (eye swap flame) | ✅ | ✅ |
| SLEEPY | ✅ | ✅ (4) | ✅ (dict) | ✅ | ✅ (=4) | ✅ | ✅ | ✅ (else) | ✅ | ✅ |
| SURPRISED | ✅ | ✅ (5) | ✅ (dict+flash) | ✅ | ✅ (=5) | ✅ | ✅ | ✅ (else) | ✅ | ✅ |
| SAD | ✅ | ✅ (6) | ✅ (dict) | ✅ | ✅ (=6) | ✅ | ✅ | ✅ (else) | ✅ | ✅ |
| CONFUSED | ✅ | ✅ (7) | ✅ (dict) | ✅ | ✅ (=7) | ✅ | ✅ | ✅ (eye swap hypnoRed) | ✅ | ✅ |
| AMUSED | ✅ | ✅ (2 — reuses CURIOUS) | ✅ (special case) | ✅ | ✅ (=8) | ✅ | ✅ | ✅ (else — no swap) | **❌ ABSENT** | **❌ ABSENT** |

---

## 2. Runtime Fallback Behavior at Each ABSENT Cell

Only one ABSENT pattern: **AMUSED** missing from `IRIS_ARCH.md` Serial Protocol line and `README.md` Emotion System table.

### IRIS_ARCH.md — Serial Protocol (line 568)
```
EMOTION:NEUTRAL/HAPPY/CURIOUS/ANGRY/SLEEPY/SURPRISED/SAD/CONFUSED
```
Doc string only; no runtime impact. Firmware at `src/main.cpp:168` parses `"AMUSED"` correctly.

### README.md — Emotion System table (lines 121-130)
8 rows; AMUSED row absent. Documentation only.

### Code-side fallback paths for *unknown* emotion strings

1. **`pi4/services/llm.py:22-29`** — unknown emotion coerced to `NEUTRAL`, tag stripped from reply.
2. **`pi4/core/config.py` MOUTH_MAP** — `MOUTH_MAP.get(emotion, 0)` at assistant.py:175 → unknown → `MOUTH:0` (flat line).
3. **`pi4/hardware/led.py:143-162`** — AMUSED special-case at line 143; otherwise `self._EMOTION_LED.get(emotion.upper(), self._EMOTION_LED["NEUTRAL"])` → unknown → NEUTRAL breathe.
4. **`src/main.cpp` parseEmotion:161-170** — strcmp walk; default return `NEUTRAL`.
5. **`src/main.cpp` applyEmotion:188-194 else branch** — clears any active eye swap, reverts to `userDefaultEye`.

**Summary:** All five code-side locations coerce unknown emotions to NEUTRAL. Defense-in-depth is uniform. The pre-S47 AMUSED defect (iris_issue_log.md "2026-05-03 | S47 | Cross-Stack / Emotion") demonstrated this exact chain — `[EMOTION:AMUSED]` was emitted by the LLM but stripped to NEUTRAL by `extract_emotion_from_reply` because AMUSED wasn't yet in `VALID_EMOTIONS`. No crash, just silent loss of functionality.

---

## 3. MOUTH_MAP vs README.md Index Cross-Reference

Source: `pi4/core/config.py:143-153` and `README.md` Mouth Display table (lines 89-100).

| Emotion | MOUTH_MAP index | README.md index | Match |
|---|---|---|---|
| NEUTRAL | 0 | 0 (Flat line) | ✅ |
| HAPPY | 1 | 1 (Wide smile) | ✅ |
| CURIOUS | 2 | 2 (Diagonal smirk) | ✅ |
| ANGRY | 3 | 3 (Frown) | ✅ |
| SLEEPY | 4 | 4 (Right droop) | ✅ |
| SURPRISED | 5 | 5 (Oval) | ✅ |
| SAD | 6 | 6 (Downturn) | ✅ |
| CONFUSED | 7 | 7 (Zigzag) | ✅ |
| AMUSED | 2 (reuses CURIOUS smirk) | — | ⚠ Not in README |
| SLEEP (non-emotion) | n/a | 8 (Off — SLEEP) | ⚠ README index 8 is a state, not an emotion. Sent via direct `MOUTH:8` in `_do_sleep` (assistant.py:222) — not via MOUTH_MAP. |

### Findings
1. AMUSED documented only in CHANGELOG S47 + ROADMAP RD-002. README emotion table at lines 121-130 still lists 8 emotions.
2. Mouth index 8 is a non-emotion sleep expression — correctly sent via direct command, not lookup. Not a gap.

---

## 4. led.py Coverage vs VALID_EMOTIONS

`VALID_EMOTIONS = {"NEUTRAL", "HAPPY", "CURIOUS", "ANGRY", "SLEEPY", "SURPRISED", "SAD", "CONFUSED", "AMUSED"}` — 9 emotions.

`_EMOTION_LED` dict keys (led.py:132-141): NEUTRAL, HAPPY, CURIOUS, ANGRY, SLEEPY, SURPRISED, SAD, CONFUSED — 8 emotions.

`show_emotion()`: line 143 special-case for AMUSED; line 162 dict lookup with NEUTRAL fallback for everything else.

| Emotion | _EMOTION_LED entry | Special branch | Covered? |
|---|---|---|---|
| NEUTRAL | ✅ | — | ✅ |
| HAPPY | ✅ | — | ✅ |
| CURIOUS | ✅ | — | ✅ |
| ANGRY | ✅ | — | ✅ |
| SLEEPY | ✅ | — | ✅ |
| SURPRISED | ✅ (flash=True) | — | ✅ |
| SAD | ✅ | — | ✅ |
| CONFUSED | ✅ | — | ✅ |
| AMUSED | — | ✅ (lines 143-160) | ✅ |

No emotion in VALID_EMOTIONS lacks an LED code path.

---

## 5. AMUSED Verification (All Five Locations)

Per task instruction — AMUSED is the most recent emotion (S47) and highest partial-implementation risk.

### config.py VALID_EMOTIONS
Line 142. ✅ Present.

### config.py MOUTH_MAP
Lines 143-153. ✅ Present, value 2 (smirk — reuses CURIOUS expression per RD-002 design).

### led.py show_emotion
Lines 143-160. ✅ Present. Sinusoidal breathe, amber [255,160,0] via `(v, v*160//255, 0)` scaling, floor=10, peak=80, period=1.5s, gamma=1.8, duration=3.0s. Matches RD-002 spec.

⚠ **Sub-finding:** Line 158-159 explicitly turns LED off (`self._write([(0, 0, 0)] * self.n)`) after the 3s window completes. Other `_EMOTION_LED` emotions breathe continuously until interrupted by the next `show_*` call. This produces a behavioral asymmetry — see Finding 3.2 below.

### llm.py extract_emotion_from_reply
Lines 18-29. ✅ Indirectly correct via VALID_EMOTIONS membership.

### main.cpp EmotionID enum
Line 69. ✅ Present at value 8. `EMOTION_COUNT = 9`.

### main.cpp emotionTable
Lines 71-81. ✅ Present. `{0.55f, false, 3000}` — medium pupil, no blink, 3s gaze. Matches RD-002 spec.

### main.cpp parseEmotion
Line 168. ✅ `if (strcmp(name, "AMUSED") == 0) return AMUSED;`

### main.cpp applyEmotion
Lines 188-194 (else branch). ✅ AMUSED falls through with no eye swap — uses `userDefaultEye`. Matches RD-002 spec ("Falls to default else branch — no eye swap, uses default eyes").

### iris_web.html
Out of scope for this audit (not on pre-flight read list). CHANGELOG S47 documents AMUSED button at index 2. Trust the doc — not verified here.

### iris-kids modelfile
Out of scope. HANDOFF_CURRENT S47 documents AMUSED added to valid emotion list. Trust the doc.

### Summary for AMUSED

| Location | Status |
|---|---|
| config.py VALID_EMOTIONS | ✅ |
| config.py MOUTH_MAP | ✅ |
| led.py show_emotion | ✅ |
| llm.py extract_emotion_from_reply | ✅ (via VALID_EMOTIONS) |
| main.cpp EmotionID | ✅ |
| main.cpp emotionTable | ✅ |
| main.cpp parseEmotion | ✅ |
| main.cpp applyEmotion | ✅ (correct else branch) |
| iris_web.html | (out of scope — trust S47 docs) |
| iris-kids modelfile | (out of scope — trust S47 docs) |
| **IRIS_ARCH.md emotion table** | **❌ Absent** |
| **README.md emotion table** | **❌ Absent** |

---

## Findings

### Finding 3.1 — AMUSED missing from IRIS_ARCH.md and README.md

- **Files:** `IRIS_ARCH.md` line 568; `README.md` lines 121-130
- **Severity:** LOW
- **Risk:** Code-side AMUSED is fully wired across all 5 implementation locations. Both top-level user docs still enumerate 8 emotions. New readers will miss AMUSED.
- **Fix direction:** Add AMUSED row to README.md emotion system table (nordicBlue eyes, pupil 0.55, amber breathe 1.5s, smirk mouth). Extend IRIS_ARCH.md serial protocol enumeration to include AMUSED. Per CHANGELOG S47 the lower-tier docs (HANDOFF, ROADMAP, CHANGELOG, SNAPSHOT, issue log) WERE updated — only the two highest-traffic top-level docs were missed.

### Finding 3.2 — AMUSED LED auto-off after 3s vs other emotions' continuous breathe

- **File:** `pi4/hardware/led.py`
- **Lines:** 158-159
- **Severity:** LOW
- **Risk:** AMUSED ends the animation by writing all-zero LEDs (LED off) after 3s. Other emotions in `_EMOTION_LED` breathe continuously until the next `show_emotion` or `show_idle_*` call. If the assistant transitions AMUSED → listening without an intermediate emit, the LED stays dark during listening. RD-002 spec does say "duration=3s" so this matches design, but the asymmetry with other emotions is a hazard.
- **Fix direction:** Either accept as design intent (document in README that AMUSED is time-bounded), or remove the duration cap and let AMUSED breathe continuously like other emotions.

### Finding 3.3 — Emotion fallback paths are uniform and correct

- **Severity:** none (informational)
- **Observation:** All five code-side layers independently coerce unknown emotions to NEUTRAL. The pre-S47 AMUSED defect was an *invisible* loss of functionality, not a stability issue. Defense-in-depth is functioning as designed.

### Finding 3.4 — main.cpp `applyEmotion` unbounded array index

- **File:** `src/main.cpp`
- **Lines:** 173-174
- **Severity:** LOW
- **Risk:** `emotionTable[id]` direct array access. `EMOTION_COUNT = 9` is the bound. All current callers pass `parseEmotion` output or named enum values — bounded. A future caller passing an out-of-range `EmotionID` (via casting or enum overflow) would read adjacent memory. Risk is hypothetical, not active.
- **Fix direction:** Add `if (id >= EMOTION_COUNT) id = NEUTRAL;` at the top of `applyEmotion`.

---

## Summary

- **LOW:** 3 active findings
- **None HIGH or MED.**

The emotion system is the most consistently implemented subsystem in IRIS. RD-002 (S47) executed cleanly across all 5 code-side locations. The only outstanding work is two doc updates. The 9 emotions × 5 implementation locations matrix has every code cell filled. Fallback coercion to NEUTRAL is uniform.

*End Task 3.*
