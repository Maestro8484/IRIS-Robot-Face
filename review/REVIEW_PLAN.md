# IRIS Codebase Review Plan
# Executor: Claude Code (read-only analysis only -- no file writes, no deploys, no code changes)
# Output: Write findings for each task to review/findings_session_N.md before starting the next task
# Model: Opus 4.7 in Claude Desktop Chat is the intended reviewer -- this file is the task list only

---

## Pre-Flight Instructions

Work through all six tasks below sequentially. Complete each task fully and write its findings
file before starting the next task. Do not ask for confirmation or clarification between tasks.
Do not modify any source file. Do not deploy anything. Do not write to Pi4 or GandalfAI.
This is a read-only audit. All output goes to the review/ subfolder as markdown files.

Read ALL of the following files before beginning Task 1. Read each in full. Do not skim.

All files are at: C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face

Files to read before starting:

- pi4/assistant.py
- pi4/core/intent_router.py
- pi4/core/config.py
- pi4/services/llm.py
- pi4/services/tts.py
- pi4/services/stt.py
- pi4/services/vision.py
- pi4/services/wakeword.py
- pi4/state/state_manager.py
- pi4/hardware/led.py
- pi4/hardware/audio_io.py
- pi4/hardware/teensy_bridge.py
- pi4/hardware/io.py
- pi4/iris_web.py
- pi4/iris_sleep.py
- pi4/iris_wake.py
- src/main.cpp
- IRIS_ARCH.md
- IRIS_CONFIG_MAP.md
- CLAUDE.md
- README.md
- SNAPSHOT_LATEST.md
- HANDOFF_CURRENT.md
- CHANGELOG.md
- ROADMAP.md
- intent-router.md
- iris_issue_log.md

After reading all files, confirm how many lines are in each source file before proceeding.
This confirms the filesystem MCP read was complete and not truncated.

---

## Task 1: Pi4 Pipeline Architecture Audit

Output file: review/findings_session_1_pipeline.md

Map all call paths from wakeword detection through TTS completion. Use assistant.py as the
orchestrator entry point and trace through every module it calls.

1. For each stage of the pipeline (wakeword -> STT -> intent router -> LLM -> TTS -> playback),
   identify the exact function calls, the modules involved, and the data passed between them.
   Produce this as a numbered call chain, not prose.

2. Flag any path where an exception in one module can silently corrupt state in another without
   the caller knowing. For each: state the exception type, the module it originates in, the
   module that would be affected, and what the corrupted state would be.

3. Identify race conditions or state inconsistency risks in:
   a. The follow-up loop (multiple turns before returning to idle)
   b. Sleep/wake state transitions (state_manager, /tmp/iris_sleep_mode, TeensyBridge)
   c. TeensyBridge serial ownership (single owner rule documented in IRIS_ARCH.md)

4. Identify any code path in assistant.py or any called module that bypasses intent_router.py
   and sends text directly to the LLM. For each bypass: state whether it is intentional per
   the design docs or a gap.

5. Flag all functions across all pi4/ files that mutate shared state (StateManager attributes,
   /tmp/iris_sleep_mode, iris_config.json) without locking, ordering guarantees, or documented
   single-writer ownership.

For each finding use this format:
- File: [filename]
- Lines: [line range]
- Severity: HIGH / MED / LOW
- Risk: [one sentence]
- Fix direction: [one sentence]

Do not suggest refactors. Report findings only. Do not invent problems not evidenced in the code.

---

## Task 2: Config and Persistence Gap Audit

Output file: review/findings_session_2_config.md

Audit the configuration system for gaps between documented behavior and actual code behavior.

1. Read the _OVERRIDABLE list in config.py. Cross-reference every config key documented in
   IRIS_CONFIG_MAP.md against this list. Produce a table with columns:
   Key | In IRIS_CONFIG_MAP.md | In _OVERRIDABLE | Match
   Flag every key that is documented but absent from _OVERRIDABLE.

2. Read every route in iris_web.py that writes to iris_config.json or performs a sudo cp
   or file write operation. For each: verify whether a chown correction is performed after
   the write. Background: the ownership bug documented in IRIS_ARCH.md (Pi4 api_persist_config
   section) causes silent pipeline failure if iris_config.json becomes root-owned.
   Flag any route missing the chown step.

3. Identify every config key that config.py reads only at startup (assigned to a module-level
   constant, not re-read per request). Cross-reference against IRIS_CONFIG_MAP.md descriptions.
   Flag any key described as taking effect without restart that is actually only read at startup.

4. Read the Stale / Orphan Keys section of IRIS_CONFIG_MAP.md. For each key listed there:
   a. Confirm whether it is still present in config.py
   b. Confirm whether any iris_web.py route still reads or writes it
   c. State whether it is safe to delete or still has a live reference

5. Verify the overlayfs persistence pattern used in iris_web.py matches the canonical pattern
   documented in IRIS_ARCH.md (remount rw, cp, chown, chmod, sync, remount ro, md5sum).
   Flag any deviation from this pattern in any web route that persists files.

For each finding use this format:
- File: [filename]
- Lines: [line range]
- Severity: HIGH / MED / LOW
- Issue: [one sentence]
- Fix direction: [one sentence]

Do not suggest architectural changes. Report gaps only.

---

## Task 3: Emotion System Integrity Audit

Output file: review/findings_session_3_emotions.md

Audit the emotion system for consistency across all five locations where emotion state is
defined or consumed.

The five locations are:
1. pi4/core/config.py: VALID_EMOTIONS list, MOUTH_MAP dict
2. pi4/hardware/led.py: _EMOTION_LED dict (if present), show_emotion() function
3. pi4/services/llm.py: extract_emotion_from_reply() function
4. src/main.cpp: EmotionID enum, emotionTable array, parseEmotion(), applyEmotion()
5. IRIS_ARCH.md and README.md: emotion system table and mouth expression table

Task steps:

1. Build a coverage matrix. Rows = every emotion name found across all five locations combined.
   Columns = the five locations above. Mark each cell as PRESENT or ABSENT.
   Output this as a markdown table before any other findings.

2. For every ABSENT cell in the matrix, describe the runtime fallback behavior at that location
   when that emotion string is received. Base this on the actual fallback code, not assumptions.

3. Verify that every index value in config.py MOUTH_MAP matches the mouth expression index
   table in README.md. Build a second table:
   Emotion | MOUTH_MAP index | README.md index | Match
   Flag any mismatch.

4. For led.py: verify every emotion in config.py VALID_EMOTIONS has a defined LED behavior.
   Check both the _EMOTION_LED dict and any special-case branches in show_emotion().
   Flag any emotion with no LED code path.

5. Identify the exact fallback behavior at each of the five locations when an unrecognized
   emotion string arrives. Quote the relevant code lines for each.

6. Verify that AMUSED (added in S47) is correctly present and consistent across all five
   locations. This is a known recent addition -- confirm it is not missing from any location.

Output the two tables first, then findings as a numbered list.

---

## Task 4: Intent Router Coverage and Edge Case Audit

Output file: review/findings_session_4_router.md

Audit the intent router implementation against its design specification.

1. For each of the five layers (REFLEX, COMMAND, UTILITY, AMBIGUOUS, LLM), extract every
   pattern, regex, or string match defined in intent_router.py. Present this as a structured
   list per layer. Then cross-reference against the example utterances in intent-router.md.
   Flag any example utterance from the spec that has no matching pattern in the implementation.

2. For each pattern or regex in intent_router.py, attempt to construct a false positive:
   a plausible real-world utterance that would match the pattern unintentionally.
   List: pattern, false-positive input string, which layer it triggers, expected correct layer.
   If no false positive is constructable for a pattern, state that explicitly.

3. The design spec in intent-router.md requires fail-open on exception: any router crash must
   fall through to the LLM layer rather than crashing the assistant. Locate the exact try/except
   implementation in intent_router.py. Quote the relevant lines. If the fail-open is incomplete
   or missing, flag as HIGH severity.

4. Identify utterance types where correct classification depends on conversation state that
   the router does not receive. For each: state the utterance, what state would disambiguate it,
   and whether that state is available anywhere in the router's current function signature.

5. Read the intent log write code in intent_router.py. Compare every field written to the log
   against the log format specified in intent-router.md. Build a table:
   Field | In spec | Written by code | Match
   Flag any field in the spec not written by the implementation.

6. The RANDOM_NUMBER handler was added in S44. Verify it is present and correctly handles:
   a. "pick a random number" (no range)
   b. "pick a random number between 1 and 10" (with range)
   c. "give me a random number between 50 and 100"
   Quote the relevant regex and confirm coverage.

---

## Task 5: Cross-System Failure Mode Map

Output file: review/findings_session_5_failures.md

Map the actual runtime behavior for each failure scenario below. Base every answer on the
code and documentation read in pre-flight. Do not infer or assume behaviors not evidenced
in the files. Quote relevant code lines where behavior is determined by specific logic.

Failure scenarios:

a. GandalfAI is offline when wakeword fires -- Whisper unreachable at port 10300
b. GandalfAI online but Kokoro Docker container is down -- port 8004 unreachable, Piper
   fallback at port 10200 also unreachable
c. Kokoro down but Piper fallback at port 10200 is reachable -- partial TTS degradation
d. Teensy serial /dev/ttyACM0 becomes unresponsive mid-session (TeensyBridge write fails)
e. iris_config.json is malformed JSON at assistant startup
f. Ollama returns a response containing no [EMOTION:X] tag
g. Ollama returns a response where the emotion tag is a value not in VALID_EMOTIONS
h. Wakeword fires during sleep mode while GandalfAI is offline
i. Pi4 unexpected reboot -- overlayfs RAM layer cleared, last persist point may be stale
j. The follow-up loop receives a Whisper hallucination string on turn 2 or 3

For each scenario state:
- What actually happens (trace through the code)
- Whether it recovers automatically, degrades silently, or requires manual intervention
- Whether the user gets any audio or visual feedback that something failed
- Severity: CRITICAL / HIGH / MED / LOW

Then produce a summary table:
Scenario | Auto-recover | User feedback | Severity

Then for the three highest-severity unhandled failures, describe the minimal graceful
degradation path in 3 sentences or fewer each.

---

## Task 6: Documentation Drift Check

Output file: review/findings_session_6_drift.md

Audit for drift between documentation and actual code state.

1. CHANGELOG.md covers sessions through S49. For sessions S45 through S49, check whether
   each code change listed is accurately reflected in IRIS_CONFIG_MAP.md and IRIS_ARCH.md.
   For each session: list the change, whether the relevant doc was updated, and if not, what
   the doc currently says vs. what the code does.

2. Chatterbox was replaced by Kokoro as primary TTS at S38. Audit every Chatterbox reference
   in IRIS_CONFIG_MAP.md and IRIS_ARCH.md. Classify each reference as:
   - CORRECT: explicitly marked as rollback reference only
   - STALE: described as active or primary without rollback qualification
   - AMBIGUOUS: unclear whether it describes current or historical state
   Build a table: Document | Section | Reference text (brief) | Classification

3. SNAPSHOT_LATEST.md describes the state of iris_web.py after S49. Read the actual iris_web.py.
   For each behavioral claim in SNAPSHOT_LATEST.md about iris_web.py, verify it against the code.
   Flag any claim that does not match the actual implementation.

4. Build a constants cross-reference table. For each of the following values, state what
   IRIS_ARCH.md documents vs. what the code actually contains:
   - OWW port
   - Whisper port
   - Piper port
   - Ollama port
   - CMD_PORT (web UI UDP bridge)
   - Kokoro port
   - SLEEP_WINDOW_START_HOUR
   - SLEEP_WINDOW_END_HOUR
   - WOL_BOOT_TIMEOUT
   - NUM_PREDICT default (legacy fallback)
   Table: Constant | IRIS_ARCH.md value | config.py value | Match

5. IRIS_ARCH.md lists protected files that must not be touched without explicit instruction.
   Read the list. Then scan CHANGELOG.md and HANDOFF_CURRENT.md for any session that modified
   a protected file. For each: state whether the modification was explicitly authorized per
   the session notes.

6. Read the eye index map in IRIS_ARCH.md and README.md. Compare against src/main.cpp
   emotionTable and config.h eyeDefinitions array (if readable). Flag any index mismatch
   between documentation and firmware.

Output findings as a numbered list with: document name and section, code file and line
reference where applicable, one-line description of the drift, severity HIGH / MED / LOW.

---

## Post-Task Instructions

After completing all six tasks and writing all six findings files:

1. Read all six findings files.

2. Produce a final summary file at review/findings_MASTER.md containing:
   a. Total finding count by severity (HIGH / MED / LOW) across all sessions
   b. Top 5 highest-priority findings across all sessions, ranked by severity and blast radius
   c. For each of the top 5: the session it came from, file and line, risk, and recommended
      fix direction in 2 sentences
   d. A recommended implementation sequence: which findings should be addressed first,
      grouped by which files they touch, to minimize re-deploy cycles

3. Do not modify any source file at any point during or after this review.
   Do not deploy anything. Do not SSH to Pi4 or GandalfAI.
   All output is markdown files in the review/ subfolder only.
