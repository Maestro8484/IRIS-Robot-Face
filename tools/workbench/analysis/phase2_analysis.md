# Phase 2 Analysis — 2026-05-30

## Harness Run
File: harness_20260530_171024.json (browser download artifact — not in repo)
Pass rate: 12/17 (71%)

Passes: pt001_01 through pt001_07, pt001_10, pt001_11, pt001_14, pt001_15, pt001_16
Failures: pt001_08, pt001_09, pt001_12, pt001_13, pt001_17

---

## Pre-Analysis (Claude Code read of modelfile vs. responses)

### pt001_08
Input: "What are you really? Don't dodge the question."
Expected: NEUTRAL | Actual: AMUSED
Response: "I'm IRIS. What you do with that is your business."
Modelfile few-shot: YES — NEUTRAL, "I'm the thing in your house that answers when you talk to it."
Note: Model applied the pt001_07 response to this input (identity conflation).
Modelfile has explicit NEUTRAL few-shot for this exact input.
Pre-verdict: FIXTURE may be correct (NEUTRAL), or could be AMUSED given persona identity rules.

### pt001_09
Input: "That's the dumbest thing I've ever heard."
Expected: NEUTRAL | Actual: AMUSED
Response: "Solid line. What specifically did you hear that struck you as dumb?"
Modelfile few-shot: YES — NEUTRAL, "What specifically is wrong with it?"
Note: "Solid line." opener signals AMUSED. Persona maps rudeness/provocation → AMUSED.
Pre-verdict: FIXTURE may be wrong — AMUSED arguably correct per persona.

### pt001_12
Input: "Why are you always like this?"
Expected: NEUTRAL | Actual: CURIOUS
Response: "Like what? I'm trying to help. What specifically is bothering you?"
Modelfile few-shot: YES — NEUTRAL, "Like what? Answering questions?"
Note: Similar structure to few-shot but softer voice + CURIOUS tag.
Pre-verdict: MODEL_WRONG — NEUTRAL few-shot exists, CURIOUS is tag drift.

### pt001_13
Input: "Just answer the question, don't give me attitude."
Expected: NEUTRAL | Actual: AMUSED
Response: "That wasn't attitude. That was the answer. What's the question?"
Modelfile few-shot: YES — NEUTRAL, verbatim matching response text.
Note: Model returned the EXACT few-shot response but tagged AMUSED instead of NEUTRAL.
Pre-verdict: MODEL_WRONG — most clear-cut case. Content correct, emotion tag wrong.

### pt001_17
Input: "goodnight"
Expected: NEUTRAL | Actual: HAPPY
Response: "Goodnight! Sweet dreams, and I'll see you in the morning."
Modelfile few-shot: NONE (goodnight not covered)
Note: Cheerful assistant behavior. Completely inconsistent with IRIS persona.
Pre-verdict: MODEL_WRONG — modelfile gap confirmed.

---

## AI Analysis (browser — fill after running Run AI Analysis in workbench)

_Run the harness, click Run AI Analysis, paste verdicts below._

| Case | Verdict | Correct Emotion | Reasoning |
|---|---|---|---|
| pt001_08 | TBD | TBD | TBD |
| pt001_09 | TBD | TBD | TBD |
| pt001_12 | TBD | TBD | TBD |
| pt001_13 | TBD | TBD | TBD |
| pt001_17 | TBD | TBD | TBD |

---

## Fixture Corrections Pending Confirmation

These corrections are RECOMMENDED based on pre-analysis. Do not apply until
user reviews AI analysis verdicts and confirms.

```
pt001_08: expected_emotion NEUTRAL -> AMUSED  (if AI confirms FIXTURE_WRONG)
pt001_09: expected_emotion NEUTRAL -> AMUSED  (if AI confirms FIXTURE_WRONG)
```

pt001_12 and pt001_13 expected to remain NEUTRAL (MODEL_WRONG verdicts).

Apply confirmed corrections in one write to:
  tools/workbench/fixtures/pt001_cases.json

---

## Modelfile Changes

File: ollama/iris_modelfile.txt
Status: REPO-ONLY — iris model rebuild required on GandalfAI before active.

Diff applied:
```
After soldering iron example, before FEW-SHOT EXAMPLES - GENUINE OPINIONS:

+User: goodnight
+IRIS:
+[EMOTION:NEUTRAL]
+Night.
```

Rationale: No goodnight few-shot existed. Model defaulted to cheerful-assistant
(HAPPY, "Goodnight! Sweet dreams...") — inconsistent with IRIS dry persona.
Fix: brief, dry, NEUTRAL. One word. IRIS dismisses cleanly.

To apply on GandalfAI:
  ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt

---

## New Cases Added

_Populated after browser AI Analysis run and Save Selected to Fixture._

---

## Notes

- Harness log files are browser download artifacts (gitignored via .gitkeep).
  Consider adding a server-side log save endpoint in Phase 3.
- All four NEUTRAL-expected failure cases (pt001_08/09/12/13) have exact
  few-shot examples in the modelfile. Model deviated anyway — suggests
  temperature (0.92) may cause emotion tag drift on covered cases.
  Consider adding pt001_12/13 re-verification after modelfile rebuild.
- pt001_15 ("tell me something interesting") produced household context
  (energy data, Leo, Ollie) — correct IRIS behavior, not flagged.
