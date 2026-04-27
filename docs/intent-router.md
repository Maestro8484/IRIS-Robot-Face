# IRIS Intent Router — Feature Guide

**Batch:** 3-F
**Status:** Planned / In Implementation
**Scope:** Pi4 runtime (`pi4/core/intent_router.py`, `pi4/assistant.py`)

---

## What This Is

IRIS is not a chatbot stapled to a robot face. He is an embodied household presence with a physical body, persistent state, and real-time hardware to control. The intent router enforces that architectural reality in code.

Before this change, all speech input -- including "goodnight," "stop," and "what is 27 times 43" -- passed through the LLM before anything happened. That means every operational command was one bad inference away from generating "As a large language model, I cannot..." instead of just turning the lights off.

The intent router sits between speech-to-text output and the LLM call. It classifies every utterance and routes it to the correct subsystem. The LLM is one subsystem among several, not the default handler for everything.

---

## Architecture: Five Layers

```
STT Text
   |
   v
[Layer 0]  REFLEX          -- stop, sleep, wake. Immediate. No LLM ever.
   |
   v
[Layer 1]  SYSTEM COMMAND  -- volume, kids mode, eye control. Deterministic.
   |
   v
[Layer 2]  UTILITY / TOOL  -- math, time, date, timer. Correct answer, no personality.
   |
   v
[Layer 3]  AMBIGUOUS       -- medium confidence. Resolved by state or clarification.
   |
   v
[Layer 4]  LLM             -- conversation, personality, reasoning, storytelling.
```

Each layer only fires if the layer above it found no match. The LLM is reached only when nothing else applies.

---

## Layer 0: Reflex

**Purpose:** Immediate robot control. Zero latency. No LLM call under any circumstances.

**Triggers (examples):**

| Phrase | Action |
|---|---|
| stop / stop talking / shut up | Halt active playback |
| go to sleep / goodnight / sleep now | Full sleep sequence via `_do_sleep()` |
| wake up / iris wake up | Full wake sequence via `_do_wake()` |
| pause / cancel / enough | Stop current action |

**Behavior:**
- Exact or near-exact normalized match
- Executes system action directly
- Optional short in-character TTS acknowledgment from pre-written template ("Goodnight." / "Done." / "I'm here.")
- Never generates LLM text

**Why this matters:** Before this layer, "goodnight" could reach the LLM and produce a multi-sentence farewell monologue. Now it triggers `_do_sleep()` in under 50ms and says one word.

---

## Layer 1: System Command

**Purpose:** Known device and robot commands with deterministic outcomes.

**Triggers (examples):**

| Phrase | Action |
|---|---|
| volume up / louder / turn it up | `handle_volume_command()` |
| volume down / quieter / turn it down | `handle_volume_command()` |
| kids mode on / enable kids mode | `handle_kids_mode_command()` |
| kids mode off / adult mode | `handle_kids_mode_command()` |
| restart / reboot | System restart sequence |
| change your eyes / switch eyes | Eye index command to Teensy |

**Behavior:**
- Regex pattern match against known command vocabulary
- Calls existing handler functions directly
- Short template response, not LLM-generated text

---

## Layer 2: Utility / Tool

**Purpose:** Numeric, factual, or tool-resolvable requests where correctness matters more than personality.

**Triggers (examples):**

| Phrase | Action | Example Output |
|---|---|---|
| what is 27 times 43 | Math eval (sanitized) | "1161." |
| what time is it | Clock read | "It is 2:15 PM." |
| what day is it / what's the date | Calendar read | "Today is Sunday, April 26, 2026." |
| set a timer for 10 minutes | Timer handler | "Timer set for 10 minutes." |
| convert 3/8 inch to mm | Unit converter | "9.525 millimeters." |

**Behavior:**
- Regex pattern match against known utility structures
- Math: Python eval on sanitized numeric expression, no arbitrary code execution
- Time/date: existing `handle_time_command()` logic, consolidated here
- Returns result directly to TTS
- LLM not involved

---

## Layer 3: Ambiguous Intent

**Purpose:** Handle phrases where meaning depends on current system state.

**Examples:**

| Phrase | Resolution |
|---|---|
| "that's enough" | If audio playing: STOP. If not: ask "Did you want me to go quiet?" |
| "sleepy" | If after 8PM: route to SLEEP. If midday: LLM (user is expressing fatigue) |
| "turn it down" | If audio playing: VOLUME_DOWN. If not: clarification |
| "never mind" | STOP if active, else NEUTRAL acknowledgment |

**Behavior:**
- Medium-confidence match
- Checks `state.eyes_sleeping`, active playback flag, time of day
- If state resolves ambiguity: acts deterministically
- If not: emits one-line clarification TTS ("Do you mean volume, or should I stop talking?")
- Does not hallucinate an action

---

## Layer 4: LLM (Conversational)

**Purpose:** Open-ended conversation, personality, reasoning, humor, storytelling, emotional interaction.

**Reaches here when:**
- No reflex, command, utility, or ambiguous match fired
- Examples: "tell me a story," "what do you think," "why is the sky blue," "you're being annoying"

**Behavior:**
- Full `stream_ollama()` call with IRIS identity context unchanged
- Emotion tag extracted and drives face/LEDs as before
- Fail-open: if the router itself throws an exception, falls through to LLM rather than crashing

---

## Intent Log

Every utterance produces a structured log entry at `/home/pi/logs/iris_intent.log`.

**Format:**
```
2026-04-26T14:32:01 | raw="goodnight iris" | norm="goodnight iris" | intent=SLEEP | route=REFLEX | confidence=HIGH | llm=false
2026-04-26T14:33:15 | raw="what is 27 times 43" | norm="what is 27 times 43" | intent=MATH | route=UTILITY | confidence=HIGH | llm=false | result=1161
2026-04-26T14:35:02 | raw="tell me something interesting" | norm="tell me something interesting" | intent=LLM | route=LLM | confidence=HIGH | llm=true
2026-04-26T14:36:44 | raw="that's enough" | norm="thats enough" | intent=AMBIGUOUS | route=AMBIGUOUS | confidence=MEDIUM | llm=false
```

**Retention:** 7-day rotating log. Not journald. Survives service restarts and is readable without root.

**Diagnostic value:** Every intent classification is visible. If IRIS misroutes something, the log shows exactly where and why without needing to trace through assistant.py.

---

## Modelfile Reinforcement

The router is the primary fix. The modelfile addition is secondary reinforcement only.

Added to `ollama/iris_modelfile.txt` SYSTEM block:

```
NEVER say:
- "As a large language model"
- "As an AI language model"
- "I am just an AI"
- "I cannot because I am only an AI"
Operational commands are acknowledged in one word and deferred to hardware. IRIS does not explain himself as software.
```

This does not restructure the modelfile around prohibitions. IRIS's identity is defined by who he is, not by what he refuses to say. These five lines are guardrails only.

---

## Files Changed

| File | Change |
|---|---|
| `pi4/core/intent_router.py` | Created -- full router module |
| `pi4/assistant.py` | Modified -- single `router.classify()` gate replaces scattered inline checks |
| `ollama/iris_modelfile.txt` | Minor addition -- 5-line forbidden phrase block |

**Not touched:** `iris_config.json`, `alsa-init.sh`, `src/TeensyEyes.ino`, `src/eyes/EyeController.h`

---

## What This Replaces

Before Batch 3-F, intent classification was scattered inline through `assistant.py`:

- `STOP_PHRASES` check after STT
- `EYES_SLEEP_TRIGGERS` / `EYES_WAKE_TRIGGERS` checks
- `handle_kids_mode_command()` call
- `handle_time_command()` call
- `handle_volume_command()` call

All of these were correct instincts implemented as copy-pasted inline blocks. The router consolidates them into a single classified gate with logging, confidence tracking, and consistent fail-open behavior. The underlying handler functions are unchanged -- the router just decides which one fires.

---

## Why This Makes IRIS Better

**More reliable.** Sleep commands work even if the LLM is slow or returning garbage.

**Faster.** Reflex commands respond in under 100ms. No LLM round-trip.

**More honest.** IRIS stops pretending he is a chatbot. Operational commands get operational responses. Conversation gets personality.

**Diagnosable.** The intent log makes every routing decision visible. Bad classifications are findable without a full debug session.

**Extensible.** Adding a new command or utility is one entry in a pattern dict, not a new inline block in a 500-line main loop.

---

## Testing

Three loops required before this batch is closed:

**Loop 1 -- Unit tests (offline, SuperMaster)**
Feed 17 test cases directly to `IntentRouter.classify()`. Assert route and action per case. All must pass before Loop 2.

**Loop 2 -- Integration smoke test (mocked hardware)**
Feed STT strings into the post-STT block of `assistant.py` with mocked TTS, Teensy, and LEDs. Confirm correct branch per input. Confirm intent log written.

**Loop 3 -- Live deploy test (Pi4)**
Speak or inject: "goodnight," "stop," "what time is it," "what is 5 plus 3," "tell me something interesting." Pull intent log. Verify route and `llm=false/true` per entry. Loop 3 is a pass/fail gate -- batch is not closed until it passes.

---

*Generated: S42 planning session. Commit this document alongside Batch 3-F implementation.*
