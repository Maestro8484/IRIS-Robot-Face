# Task 4 — Intent Router Coverage and Edge Case Audit

**Date:** 2026-05-16
**Reviewer:** Opus 4.7
**Scope:** Pattern coverage vs intent-router.md spec, false positives, fail-open, state-dependent ambiguity, log format, RANDOM_NUMBER handler

---

## 1. Patterns per Layer + Spec Cross-Reference

### Layer 0: REFLEX (intent_router.py:71-86, 154-161)

**Patterns:**
- `_SLEEP_EXACT` (set, 13 phrases): "go to sleep", "go to sleep iris", "goodnight", "good night", "good night iris", "sleep now", "sleep mode", "time to sleep", "go to bed", "bedtime", "sleep iris", "iris sleep", "night night", "nighty night"
- `_SLEEP_STARTS` (tuple, 5 prefixes): "go to sleep", "goodnight", "good night", "sleep now", "bedtime"
- `_STOP_EXACT` (set, 12 phrases): "stop", "cancel", "quiet", "stop talking", "shut up", "be quiet", "stop it", "ok stop", "please stop", "jarvis stop", "pause", "pause it"
- `_STOP_STARTS` (tuple, 7 prefixes): "stop", "shut up", "stop talking", "cancel", "quiet", "be quiet", "pause"
- `_WAKE_EXACT` (set, 3 phrases): "wake up", "wake up iris", "iris wake up"
- `_WAKE_STARTS` (tuple, 1 prefix): "wake up"

**Match logic:** `norm in _SLEEP_EXACT or any(norm.startswith(p) for p in _SLEEP_STARTS)` etc.

**Spec examples (intent-router.md "Layer 0" table):**

| Spec phrase | Match in code? |
|---|---|
| "stop" | ✅ exact + starts |
| "stop talking" | ✅ exact + starts |
| "shut up" | ✅ exact + starts |
| "go to sleep" | ✅ exact + starts |
| "goodnight" | ✅ exact + starts |
| "sleep now" | ✅ exact + starts |
| "wake up" | ✅ exact + starts |
| "iris wake up" | ✅ exact only |
| "pause" | ✅ exact + starts |
| "cancel" | ✅ exact + starts |
| "enough" | **❌ Spec lists "enough" as REFLEX-STOP trigger; code routes "enough" to AMBIGUOUS-STOP via `_AMBIGUOUS_STOP_EXACT`** |

### Layer 1: COMMAND (intent_router.py:90-107, 163-188)

**Patterns (regexes via `re.compile`):**
- `_VOL_UP_RE`: `volume up|louder|turn it up|increase volume|turn up|raise volume|higher volume|more volume`
- `_VOL_DN_RE`: `volume down|quieter|turn it down|decrease volume|lower volume|turn down|reduce volume|less volume|softer|too loud`
- `_VOL_MAX_RE`: `all the way up|max volume|volume max|full volume|maximum volume|as loud`
- `_VOL_MIN_RE`: `all the way down|volume low|minimum volume|volume minimum|as quiet`
- `_VOL_QRY_RE`: `what'?s the volume|current volume|volume level|how loud|what volume`
- `_VOL_PCT_RE`: `(\d+)\s*(?:percent|%)`
- `_KIDS_ON_RE`: `kids mode on|enable kids mode|turn on kids mode|switch to kids mode|kids mode please|activate kids mode|children'?s mode on|kid mode on`
- `_KIDS_OFF_RE`: `kids mode off|disable kids mode|turn off kids mode|switch to adult mode|adult mode|deactivate kids mode|kid mode off|normal mode`
- `_EYES_OFF_TRIGGERS` (imported from config.py): 12-phrase set
- `_EYES_ON_TRIGGERS` (imported): 12-phrase set

**Spec examples (intent-router.md "Layer 1" table):**

| Spec phrase | Match in code? |
|---|---|
| "volume up" | ✅ `_VOL_UP_RE` |
| "louder" | ✅ `_VOL_UP_RE` |
| "turn it up" | ✅ `_VOL_UP_RE` |
| "volume down" | ✅ `_VOL_DN_RE` |
| "quieter" | ✅ `_VOL_DN_RE` |
| "turn it down" | ✅ `_VOL_DN_RE` |
| "kids mode on" | ✅ `_KIDS_ON_RE` |
| "enable kids mode" | ✅ `_KIDS_ON_RE` |
| "kids mode off" | ✅ `_KIDS_OFF_RE` |
| "adult mode" | ✅ `_KIDS_OFF_RE` |
| "restart" | **❌ Spec lists "restart / reboot" → COMMAND; no pattern in code** |
| "reboot" | **❌ Same** |
| "change your eyes" | **❌ Spec lists "change your eyes / switch eyes" → eye index command; no pattern in code** |
| "switch eyes" | **❌ Same** |

### Layer 2: UTILITY (intent_router.py:112-160, 190-215)

**Patterns:**
- `_TIME_RE`: `what time|what'?s the time|current time|tell me the time|time is it|what hour`
- `_DATE_RE`: `what day|what date|what'?s the date|today'?s date|what month|what year|day is it|date is it`
- `_RANDOM_RE`: `\b(pick|choose|give|tell|generate|select|get)\b.{0,30}\brandom\s+(number|integer|digit|num)\b | \brandom\s+(number|integer|digit)\b | \bpick\s+a\s+number\b | \bgive\s+me\s+a\s+number\b`
- `_RANDOM_RANGE_RE`: `\b(?:between|from)\s+([\d,]+)\s+(?:and|to)\s+([\d,]+)\b`
- `_MATH_PREFIXES`: `("what is ", "what's ", "calculate ", "compute ", "solve ", "evaluate ")` — line-start prefixes
- `_MATH_WORD_OPS`: replaces "multiplied by", "divided by", "times", "plus", "minus", "over" with arithmetic operators
- `_MATH_SAFE_RE`: `^[\d\s\+\-\*\/\(\)\.]+$`
- `_VISION_TRIGGERS` (imported from config.py): 22-phrase set

**Spec examples:**

| Spec phrase | Match in code? |
|---|---|
| "what is 27 times 43" | ✅ `_MATH_PREFIXES` + `_MATH_WORD_OPS` |
| "what time is it" | ✅ `_TIME_RE` |
| "what day is it" | ✅ `_DATE_RE` |
| "what's the date" | ✅ `_DATE_RE` |
| "set a timer for 10 minutes" | **❌ Spec lists timer handler; no `_TIMER_RE` in code** |
| "convert 3/8 inch to mm" | **❌ Spec lists unit converter; no pattern in code** |

### Layer 3: AMBIGUOUS (intent_router.py:88-89, 217-225)

**Patterns:**
- `_AMBIGUOUS_STOP_EXACT` (set, 5 phrases): "that's enough", "thats enough", "enough", "never mind", "nevermind"
- `_AMBIGUOUS_SLEEPY` (set, 5 phrases): "sleepy", "i'm sleepy", "im sleepy", "i'm tired", "im tired", "getting sleepy"

**State check:** `_AMBIGUOUS_SLEEPY` uses `time.localtime().tm_hour`. If hour ≥ 21 or < 8 → `IntentResult(ROUTE_AMBIGUOUS, "SLEEP", CONF_MEDIUM)`; else → `IntentResult(ROUTE_AMBIGUOUS, "LLM", CONF_MEDIUM)`.

**Spec examples:**

| Spec phrase | Match in code? |
|---|---|
| "that's enough" | ✅ `_AMBIGUOUS_STOP_EXACT` |
| "sleepy" | ✅ `_AMBIGUOUS_SLEEPY` |
| "turn it down" | **❌ Spec describes context-dependent VOLUME_DOWN vs clarification; code unconditionally routes to COMMAND.VOLUME_DOWN via `_VOL_DN_RE` at Layer 1** |
| "never mind" | ✅ `_AMBIGUOUS_STOP_EXACT` |

### Layer 4: LLM (intent_router.py:135)

Default fallback if no earlier layer matches. No patterns.

### Findings — Pattern coverage gaps

#### Finding 4.1 — Spec phrase "enough" routes to AMBIGUOUS, not REFLEX

- **File:** `pi4/core/intent_router.py`
- **Lines:** 47, 88
- **Severity:** LOW
- **Risk:** Spec (intent-router.md Layer 0 table) lists "enough" as a REFLEX-tier STOP phrase, meaning it should fire immediately. Code routes it to `_AMBIGUOUS_STOP_EXACT` (Layer 3), which has CONF_MEDIUM and is handled differently. Behaviorally: assistant.py:491-492 catches AMBIGUOUS/STOP and calls `_stop_playback.set()` + `emit_emotion(NEUTRAL)` — same effect as REFLEX/STOP. So functionally there is no user-visible difference; the spec/implementation mismatch is internal.
- **Fix direction:** Either update intent-router.md to reflect that "enough" is AMBIGUOUS, or move "enough" from `_AMBIGUOUS_STOP_EXACT` into `_STOP_EXACT`.

#### Finding 4.2 — Spec lists `restart`, `reboot` and `change/switch eyes` as COMMAND-tier; no implementation

- **File:** `pi4/core/intent_router.py`
- **Lines:** N/A — no pattern exists
- **Severity:** LOW
- **Risk:** intent-router.md Layer 1 table lists these as deterministic COMMAND handlers. Code has no matching regex. These phrases fall through to Layer 4 LLM. The LLM might respond conversationally about restarts rather than executing one. No restart endpoint is wired in either the router or `assistant.py` — only the web UI route `/api/restart` exists.
- **Fix direction:** If voice restart is intended, add `_RESTART_RE` to Layer 1 and call `subprocess.run(["sudo","systemctl","restart","assistant"])`. If not intended, remove from intent-router.md.

#### Finding 4.3 — Spec lists timer + unit converter as UTILITY; no implementation

- **File:** `pi4/core/intent_router.py`
- **Lines:** N/A
- **Severity:** LOW
- **Risk:** intent-router.md Layer 2 table includes "set a timer for 10 minutes" and "convert 3/8 inch to mm". No regex in code. These fall through to LLM, which will produce conversational responses ("Sure, I've set a timer..." with no actual timer). User believes the timer is running; it is not.
- **Fix direction:** Spec describes work not yet implemented. Either implement (add `_TIMER_RE`, threading.Timer; add unit converter), or update intent-router.md to mark as "deferred / not yet implemented".

#### Finding 4.4 — "turn it down" routes to COMMAND, spec says AMBIGUOUS

- **File:** `pi4/core/intent_router.py`
- **Lines:** 91
- **Severity:** LOW
- **Risk:** intent-router.md Layer 3 spec describes "turn it down" as state-dependent (if audio playing → VOLUME_DOWN, else → clarification). Code unconditionally matches `_VOL_DN_RE` and routes to Layer 1 COMMAND/VOLUME_DOWN. In practice "turn it down" without audio context still lowers the speaker volume — usually the correct behavior. Spec is over-engineered for the implementation, but the implementation choice is defensible.
- **Fix direction:** Update intent-router.md to reflect the simpler implementation, OR add the state-dependent disambiguation if `state.is_playing` is plumbed through.

---

## 2. False-Positive Analysis

For each pattern in intent_router.py, attempt to construct a plausible utterance that matches but should not.

### Layer 0 STOP false positives

| Pattern | False positive | Triggers | Should trigger |
|---|---|---|---|
| `_STOP_STARTS = ("stop", ...)` with `norm.startswith("stop")` | `"stop reminding me about that"` (legitimate LLM query about stopping behavior) | REFLEX/STOP | LLM |
| Same | `"stopwatch"` (single word about a clock) | **No** — falls through. Because the gate is `norm.startswith("stop")` not `norm == "stop"` or `norm.startswith("stop ")`. "stopwatch" starts with "stop" → **WOULD trigger REFLEX/STOP** ⚠ |
| Same | `"stop signs in California require ..."` | REFLEX/STOP | LLM |
| `_STOP_STARTS = ("cancel", ...)` | `"cancel culture is overblown"` | REFLEX/STOP | LLM |
| `_STOP_STARTS = ("quiet", ...)` | `"quiet please, my baby is sleeping"` | REFLEX/STOP | This is genuinely ambiguous; user might want STOP |
| `_STOP_STARTS = ("pause", ...)` | `"pause for thought is what philosophy teaches"` | REFLEX/STOP | LLM |

**Critical sub-finding:** The pre-router gate in assistant.py:355-361 uses `norm.startswith(phrase + " ")` (with trailing space) which avoids `stopwatch` collision — but the *router itself* uses `norm.startswith(phrase)` (no trailing space, line 156) which DOES trigger on "stopwatch". The pre-router gate intercepts most STOP phrases before they reach the router, but in any code path that bypasses the pre-router gate (e.g., follow-up loop calling router.classify directly — though current code doesn't do this), "stopwatch" would route to REFLEX/STOP incorrectly.

### Layer 0 SLEEP false positives

| Pattern | False positive | Triggers | Should trigger |
|---|---|---|---|
| `_SLEEP_STARTS = ("go to sleep", ...)` | `"go to sleep mode docs and read about hibernation"` | REFLEX/SLEEP | LLM |
| `_SLEEP_STARTS = ("goodnight", ...)` | `"goodnight moon is a children's book"` | REFLEX/SLEEP | LLM |
| `_SLEEP_STARTS = ("bedtime", ...)` | `"bedtime stories are usually 10 minutes long"` | REFLEX/SLEEP | LLM |

### Layer 1 VOLUME false positives

| Pattern | False positive | Triggers | Should trigger |
|---|---|---|---|
| `_VOL_UP_RE` "louder" | `"speak louder than words is the saying"` | COMMAND/VOLUME_UP | LLM |
| `_VOL_DN_RE` "too loud" | `"that protest was too loud for me to think"` | COMMAND/VOLUME_DOWN | LLM |
| `_VOL_DN_RE` "softer" | `"softer fabrics are easier on skin"` | COMMAND/VOLUME_DOWN | LLM |
| `_VOL_MAX_RE` "as loud" | `"shouting is as loud as a chainsaw"` | COMMAND/VOLUME_MAX | LLM |
| `_VOL_MIN_RE` "as quiet" | `"libraries should be as quiet as possible"` | COMMAND/VOLUME_MIN | LLM |
| `_VOL_UP_RE` "more volume" | `"the next album will have more volume than the last"` | COMMAND/VOLUME_UP | LLM |
| `_VOL_PCT_RE` `(\d+)\s*(?:percent|%)` + `"volume" in norm` | `"my volume control on the stereo is at 50 percent"` | COMMAND/VOLUME_PCT (pct=50) | LLM — user is describing, not commanding |

The volume false-positives are the highest-risk class. Many casual sentences contain "louder," "softer," "more volume," "too loud" in non-imperative form.

### Layer 1 KIDS_MODE false positives

| Pattern | False positive | Triggers |
|---|---|---|
| `_KIDS_ON_RE` "kids mode on" | `"i wish kids mode on netflix worked better"` | COMMAND/KIDS_ON ⚠ |
| `_KIDS_OFF_RE` "adult mode" | `"my doctor said i need adult mode swimming lessons"` | COMMAND/KIDS_OFF ⚠ |
| `_KIDS_OFF_RE` "normal mode" | `"normal mode driving requires a license"` | COMMAND/KIDS_OFF ⚠ |

### Layer 2 UTILITY false positives

| Pattern | False positive | Triggers |
|---|---|---|
| `_TIME_RE` "what hour" | `"what hour did the cretaceous extinction begin"` | UTILITY/TIME ⚠ |
| `_DATE_RE` "what year" | `"what year did world war two end"` | UTILITY/DATE — returns current year instead of 1945 ⚠⚠ HIGH-impact false positive |
| `_DATE_RE` "what month" | `"what month is wedding season"` | UTILITY/DATE ⚠ |
| `_TIME_RE` "current time" | `"current time travel theories suggest..."` | UTILITY/TIME ⚠ |
| `_RANDOM_RE` "give me a number" | `"give me a number for the IRS, my refund is late"` | UTILITY/RANDOM_NUMBER ⚠ |
| `_RANDOM_RE` "pick a number" | `"pick a number on the lottery wheel like the pros"` | UTILITY/RANDOM_NUMBER — might be intended; ambiguous |
| `_MATH_PREFIXES` "what is " | `"what is 27 united nations resolutions"` — eval fails harmlessly | Falls through (Math parse returns None on non-numeric) ✓ |

The "what year" false positive is the most damaging: a legitimate historical question about a year ("what year did Rome fall", "what year was JFK shot") returns the *current* year. The math parser at `_parse_math` has a safety check (`_MATH_SAFE_RE`) that prevents harmful eval, but the date path has no semantic guard — any "what year" prefix routes to DATE regardless of whether a specific year is named.

### Layer 3 AMBIGUOUS false positives

| Pattern | False positive | Triggers |
|---|---|---|
| `_AMBIGUOUS_SLEEPY` "sleepy" | `"sleepy songs help children fall asleep faster"` (single word match) | AMBIGUOUS — but only on exact match. Since the input must be exactly "sleepy", this requires user to say literally "sleepy" alone. Low risk. |
| `_AMBIGUOUS_STOP_EXACT` "enough" | `"enough already" → "enough already"` doesn't exact-match | No trigger. Low risk. |

### Patterns with no constructable false positive

- `_KIDS_ON_RE` "activate kids mode" — context-specific, no plausible false positive.
- `_KIDS_OFF_RE` "deactivate kids mode" — same.
- `_VOL_QRY_RE` "what's the volume" — context-specific question form.
- `_RANDOM_RANGE_RE` `between X and Y` — only triggered downstream of `_RANDOM_RE` match, so isolation is enforced.
- `_WAKE_EXACT` "wake up iris" — context-specific.

### Finding 4.5 — High-impact "what year" / "what month" false positive

- **File:** `pi4/core/intent_router.py`
- **Lines:** 113 (_DATE_RE)
- **Severity:** **MED**
- **Risk:** Any historical question starting with "what year" or "what month" routes to UTILITY/DATE and returns the current year/month, never reaching the LLM. "What year did the Civil War end" → "Today is Saturday, May 16, 2026". User gets a non-sequitur with no indication the LLM was bypassed.
- **Fix direction:** Tighten `_DATE_RE` to require a verb-form trailing word (e.g., `r"what (year|month|date|day)\??\s*(is|are)?\s*(it|today|now)?\s*\??$"`) — anchored to end-of-string or near it, so context-bearing "what year did X happen" falls through to LLM.

### Finding 4.6 — Volume regex false positives in descriptive speech

- **File:** `pi4/core/intent_router.py`
- **Lines:** 90-94
- **Severity:** LOW
- **Risk:** Many casual utterances contain "louder", "softer", "too loud", "more volume" in non-imperative form. These route to COMMAND/VOLUME_* and execute a volume change. User has no audio cue that volume changed unexpectedly.
- **Fix direction:** Anchor volume regexes to imperative forms with word boundaries: `r"\b(make it|turn it|speak)\s+(louder|softer|quieter)\b"` etc., or require the utterance to be short (< 6 words).

### Finding 4.7 — KIDS_MODE regex matches casual phrases

- **File:** `pi4/core/intent_router.py`
- **Lines:** 96, 100
- **Severity:** LOW
- **Risk:** "Adult mode" and "normal mode" are generic enough phrases to appear in non-command speech. False switch to/from kids mode also clears `state.conversation_history` (assistant.py:191, 197) — context loss is visible to the user.
- **Fix direction:** Require imperative prefix or short utterance for KIDS regexes.

---

## 3. Fail-Open Implementation

Spec (intent-router.md "Layer 4: LLM"): "Fail-open: if the router itself throws an exception, falls through to LLM rather than crashing."

**Code (intent_router.py:138-145):**

```python
def classify(self, raw: str, state=None) -> IntentResult:
    try:
        return self._classify(raw, state)
    except Exception as e:
        print(f"[ROUTE] classify() exception ({e}) -- falling through to LLM", flush=True)
        result = IntentResult(ROUTE_LLM, "LLM", CONF_LOW)
        _log(raw, _normalize(raw), result, llm=True)
        return result
```

**Verdict:** Fail-open is present and correctly implemented. Bare `except Exception` covers all reasonable exceptions short of `SystemExit`/`KeyboardInterrupt`. The fail-open path:
1. Logs to stderr (`[ROUTE] classify() exception ...`)
2. Constructs LLM result with CONF_LOW confidence
3. Writes to intent log via `_log()` with `llm=True`
4. Returns to caller — caller never sees the exception

**Sub-concern:** The fail-open `_log` call (line 144) might itself throw if `_intent_logger` is broken. The log call is wrapped in try/except at line 64 (`_log` body: `try: _intent_logger.info(line) except Exception: pass`), so this is safe.

**Severity:** N/A — fail-open is correct and complete. No flag.

---

## 4. State-Dependent Ambiguity

`IntentRouter.classify(raw: str, state=None)` accepts `state` but most layers ignore it. Only `_layer3_ambiguous` uses `state` — and it only uses `time.localtime().tm_hour`, not the passed `state` object.

Currently `state` is `None` in practice (assistant.py:381 calls `router.classify(text, state)` passing the StateManager singleton, but the router never reads its attributes).

### Utterances where missing state causes misclassification

| Utterance | State needed | Available in router? |
|---|---|---|
| "turn it down" | `is_audio_playing` — if no audio, "turn it down" might mean LED brightness, temperature setpoint (not implemented), or volume | No. Router unconditionally routes to VOLUME_DOWN. |
| "stop" | `is_audio_playing` — if no audio, "stop" is a noop or a misclick | No. Router routes to STOP unconditionally (asssistant.py:413 sets `_stop_playback` regardless; harmless). |
| "that's enough" | `is_audio_playing` — same as "stop" | No. Routes to AMBIGUOUS/STOP. |
| "sleepy" / "i'm tired" | `last_interaction` age, `kids_mode`, current hour — router uses ONLY current hour | Partial. Hour is checked; user state (already-engaged conversation, kids mode age cutoff) not considered. |
| "wake up" | `eyes_sleeping` — if not sleeping, command is a noop | No. Router emits REFLEX/WAKE; assistant.py:415 calls `_do_wake` which is idempotent (no-op if already awake). Harmless but inefficient. |
| "kids mode off" while already in adult mode | `kids_mode` flag | No. Router emits COMMAND/KIDS_OFF; assistant.py:188-198 `handle_kids_mode_command` checks current state and returns `kids_reply=None, new_mode=None` if no transition needed. Handled at handler level, not router. |
| "yes" / "no" / "seven" (single-word follow-up answers) | `in_followup_loop` — these are valid only inside a follow-up | The router doesn't see follow-up replies at all. Follow-up loop in assistant.py:582-635 bypasses the router. |

**Sub-finding:** The router's `state=None` parameter is essentially vestigial. `_layer3_ambiguous(norm, state)` receives `state` but uses `time.localtime()` instead. A future change requiring true state-dependent routing would need to wire StateManager attributes into the router.

### Finding 4.8 — Router `state` parameter is unused

- **File:** `pi4/core/intent_router.py`
- **Lines:** 137, 148, 217-225
- **Severity:** LOW
- **Risk:** The `state` parameter is plumbed through `classify` → `_classify` → `_layer3_ambiguous` but never read. Reviewers may assume state-aware logic exists when it does not.
- **Fix direction:** Either remove the parameter as dead code, OR wire actual state checks (e.g., `state.eyes_sleeping` to disambiguate WAKE; `state.kids_mode` to gate KIDS_OFF).

---

## 5. Intent Log Format

**Spec (intent-router.md "Intent Log"):**

```
2026-04-26T14:32:01 | raw="goodnight iris" | norm="goodnight iris" | intent=SLEEP | route=REFLEX | confidence=HIGH | llm=false
2026-04-26T14:33:15 | raw="what is 27 times 43" | norm="what is 27 times 43" | intent=MATH | route=UTILITY | confidence=HIGH | llm=false | result=1161
```

Fields in spec: `timestamp`, `raw`, `norm`, `intent`, `route`, `confidence`, `llm`, `result` (optional).

**Code (intent_router.py:55-66, `_log` function):**

```python
def _log(raw: str, norm: str, result: IntentResult, llm: bool, extra: str = "") -> None:
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = (
        f'{ts} | raw="{raw}" | norm="{norm}" | intent={result.action}'
        f" | route={result.route} | confidence={result.confidence} | llm={str(llm).lower()}"
    )
    if extra:
        line += f" | result={extra}"
    try:
        _intent_logger.info(line)
    except Exception:
        pass
```

**Cross-reference table:**

| Field | In spec | Written by code | Match |
|---|---|---|---|
| timestamp | ✅ | ✅ (line 56, `%Y-%m-%dT%H:%M:%S`) | ✅ |
| raw | ✅ | ✅ | ✅ |
| norm | ✅ | ✅ | ✅ |
| intent | ✅ | ✅ (`result.action`) | ✅ |
| route | ✅ | ✅ | ✅ |
| confidence | ✅ | ✅ | ✅ |
| llm | ✅ | ✅ | ✅ |
| result (optional) | ✅ | ✅ (via `extra` arg) | ✅ |

**Result population:** `_classify` at line 132-133 sets `extra` from `result.payload["result"]` only if `result.payload` exists and contains `"result"`. Currently only MATH sets `payload={"result": math_result}` (line 209). RANDOM_NUMBER does NOT populate `payload`, so its log line omits `result=` even though the spec example would suggest it should be there ("intent=MATH ... result=1161" parallel to "intent=RANDOM_NUMBER ... result=?").

### Finding 4.9 — RANDOM_NUMBER intent log omits the result value

- **File:** `pi4/core/intent_router.py`
- **Lines:** 196-199
- **Severity:** LOW
- **Risk:** When the router answers a random number query (e.g., "pick a random number between 1 and 10" → "7."), the intent log shows the intent and route but not the value returned. Debugging stochastic responses is harder without the value. MATH does include it; RANDOM_NUMBER does not.
- **Fix direction:** Populate `payload={"result": response.rstrip('.')}` in the RANDOM_NUMBER IntentResult.

---

## 6. RANDOM_NUMBER Handler Verification

**Regex (intent_router.py:115-119):**

```python
_RANDOM_RE = re.compile(
    r"\b(pick|choose|give|tell|generate|select|get)\b.{0,30}\brandom\s+(number|integer|digit|num)\b"
    r"|\brandom\s+(number|integer|digit)\b"
    r"|\bpick\s+a\s+number\b|\bgive\s+me\s+a\s+number\b"
)
_RANDOM_RANGE_RE = re.compile(r"\b(?:between|from)\s+([\d,]+)\s+(?:and|to)\s+([\d,]+)\b")
```

**Handler (`_random_number_reply`, lines 122-130):**

```python
def _random_number_reply(norm: str) -> str:
    m = _RANDOM_RANGE_RE.search(norm)
    if m:
        lo = int(m.group(1).replace(",", ""))
        hi = int(m.group(2).replace(",", ""))
        if lo > hi:
            lo, hi = hi, lo
        return f"{random.randint(lo, hi)}."
    return f"{random.randint(1, 100)}."
```

**Test cases per spec:**

| Input | `_RANDOM_RE` matches? | `_RANDOM_RANGE_RE` matches? | Result |
|---|---|---|---|
| `"pick a random number"` | ✅ — `\bpick\b ... \brandom\s+number\b` | ❌ | `random.randint(1, 100)` |
| `"pick a random number between 1 and 10"` | ✅ | ✅ — `(1, 10)` | `random.randint(1, 10)` |
| `"give me a random number between 50 and 100"` | ✅ — `\bgive\b ... \brandom\s+number\b` | ✅ — `(50, 100)` | `random.randint(50, 100)` |

All three pass. ✅

**Additional edge cases:**

| Input | Result |
|---|---|
| `"give me a number"` | ✅ matches `\bgive\s+me\s+a\s+number\b` (no "random" needed) → 1-100 |
| `"pick a number between 1 and 100"` | ✅ matches `\bpick\s+a\s+number\b` + range → 1-100 |
| `"pick a number"` | ✅ matches `\bpick\s+a\s+number\b` → 1-100 |
| `"random number"` | ✅ matches `\brandom\s+(number\|integer\|digit)\b` → 1-100 |
| `"from 5 to 50 pick a random number"` (range before verb) | ✅ `_RANDOM_RE` matches; `_RANDOM_RANGE_RE` matches `from 5 to 50` → 5-50 |
| `"pick a random number between 100 and 50"` (reversed range) | ✅ matches; swap logic at line 127 normalizes to `(50, 100)` |
| `"between 1 and 10"` (no verb, no "random number") | ❌ `_RANDOM_RE` does not match → falls through to LLM. Correct. |
| `"generate a random integer"` | ✅ matches `\bgenerate\b ... \brandom\s+(number\|integer\|digit\|num)\b` → 1-100 |
| `"give me a random digit"` | ✅ matches → 1-100 (note: not capped at 9 despite "digit") ⚠ |

### Finding 4.10 — "random digit" returns 1-100, not 0-9

- **File:** `pi4/core/intent_router.py`
- **Lines:** 115-119, 122-130
- **Severity:** LOW
- **Risk:** The regex matches "random digit" but `_random_number_reply` always returns 1-100 (or the explicit range). User asking for a "random digit" gets numbers up to 100 — semantically wrong.
- **Fix direction:** Inspect which word matched (`number`, `integer`, `digit`, `num`). For "digit" → `random.randint(0, 9)`.

---

## Summary

- **MED:** 1 (Finding 4.5 — "what year" false positive returns current year for historical questions)
- **LOW:** 8 (4.1 spec/code "enough" mismatch; 4.2 missing restart/eye-switch patterns; 4.3 missing timer/converter; 4.4 turn-it-down spec vs code; 4.6 volume false positives; 4.7 kids mode false positives; 4.8 unused state param; 4.9 random_number log omits result; 4.10 random digit returns 1-100)
- **N/A:** Fail-open implementation is correct (Section 3).

The router is a solid implementation but the pattern set is biased toward recall over precision. False positives are common; false negatives (real commands the router misses) are rare. The "what year" case is the most damaging because it silently returns wrong answers to legitimate factual questions. Volume and kids-mode regexes have similar precision issues at lower impact.

*End Task 4.*
