0. Create Safe Refactor Branch
git checkout -b refactor/assistant-modularization
git push -u origin refactor/assistant-modularization
1. Initialize Claude Code Session (Paste Once)
You are working on a production hardware-integrated AI system.

Rules:
- Do NOT guess pins, ports, device paths, or hardware behavior
- Do NOT refactor multiple systems at once
- Preserve current behavior unless explicitly told to change it
- Only modify files explicitly mentioned
- Return FULL updated files, not partial snippets
- If uncertain, stop and ask instead of guessing

Architecture direction:
- Single serial owner for Teensy
- Centralized state management
- Modular separation of hardware vs services vs orchestration
2. Create Module Structure (NO logic movement yet)
TASK:
Create the following files with empty class/function scaffolding only. Do NOT move any logic yet.

- hardware/teensy_bridge.py
- hardware/audio_io.py
- hardware/io.py
- services/stt.py
- services/tts.py
- services/llm.py
- services/wakeword.py
- services/vision.py
- state/state_manager.py
- core/config.py

CONSTRAINTS:
- Do not modify assistant.py
- No logic movement yet
- Only create files

OUTPUT:
Return full contents of all new files
3. Commit Baseline
git add .
git commit -m "Scaffold modular architecture (no logic moved)"
4. Extract Teensy Serial Layer (FIRST CRITICAL MOVE)
TASK:
Move all Teensy serial communication logic from assistant.py into hardware/teensy_bridge.py.

CONTEXT:
- Only one module may access /dev/ttyACM0
- assistant.py must call into this module instead of writing to serial directly

CONSTRAINTS:
- Do not change behavior
- Do not refactor unrelated logic
- Keep command formats identical

OUTPUT:
Return full updated:
- assistant.py
- hardware/teensy_bridge.py
5. TEST (MANDATORY)

Check:

Eyes respond
Mouth responds
No duplicate serial access
No crashes
6. Commit
git add .
git commit -m "Extract Teensy serial bridge"
7. Extract Audio System
TASK:
Extract all microphone input, playback, interruption, and volume control logic from assistant.py into hardware/audio_io.py.

CONSTRAINTS:
- Preserve behavior exactly
- Do not modify Teensy logic
- Do not refactor logic, only move

OUTPUT:
Return full updated:
- assistant.py
- hardware/audio_io.py
8. TEST

Check:

Wake word still triggers
Audio playback works
Interrupt works
9. Commit
git add .
git commit -m "Extract audio IO layer"
10. Extract Wake Word
TASK:
Move wake word detection logic from assistant.py into services/wakeword.py.

CONSTRAINTS:
- Do not change thresholds or behavior
- assistant.py should call into this module

OUTPUT:
Return full updated:
- assistant.py
- services/wakeword.py
11. TEST
12. Commit
git add .
git commit -m "Extract wakeword service"
13. Extract STT
TASK:
Move speech-to-text logic into services/stt.py.

CONSTRAINTS:
- Preserve current model usage and endpoints
- No behavior change

OUTPUT:
Return full updated:
- assistant.py
- services/stt.py
14. TEST
15. Commit
git add .
git commit -m "Extract STT service"
16. Extract TTS
TASK:
Move text-to-speech logic into services/tts.py.

CONSTRAINTS:
- Preserve voice, API usage, playback flow

OUTPUT:
Return full updated:
- assistant.py
- services/tts.py
17. TEST
18. Commit
git add .
git commit -m "Extract TTS service"
19. Extract LLM
TASK:
Move LLM interaction logic into services/llm.py.

CONSTRAINTS:
- Preserve prompt flow
- Preserve API endpoints (Ollama etc.)

OUTPUT:
Return full updated:
- assistant.py
- services/llm.py
20. TEST
21. Commit
git add .
git commit -m "Extract LLM service"
22. Introduce State Manager (CRITICAL FIX)
TASK:
Create a centralized StateManager class in state/state_manager.py to track:

- listening state
- speaking state
- sleep state (eyes)
- follow-up mode
- interruption state

Then replace all global state variables in assistant.py with this object.

CONSTRAINTS:
- Do not change behavior
- Only replace state storage

OUTPUT:
Return full updated:
- assistant.py
- state/state_manager.py
23. TEST (IMPORTANT)

Check:

sleep/wake works correctly
no desync in eyes
no stuck states
24. Commit
git add .
git commit -m "Introduce centralized state manager"
25. Rename Entry Point
git mv assistant.py main.py
26. Convert to Orchestrator
TASK:
Refactor main.py so it acts only as an orchestrator:

- calls services (wakeword, stt, llm, tts)
- uses StateManager
- sends output to hardware modules

CONSTRAINTS:
- Do not change system behavior
- Do not reimplement logic
- Only reorganize flow

OUTPUT:
Return full updated main.py
27. TEST FULL SYSTEM
Full voice loop
Interruptions
Teensy expressions
Vision triggers (if active)
28. Commit
git add .
git commit -m "Convert assistant into modular orchestrator"
29. Remove Hardcoded Secrets
TASK:
Remove any hardcoded API keys from the codebase and replace with environment variable usage.

CONSTRAINTS:
- Do not break functionality
- Use os.getenv

OUTPUT:
Return updated files
30. Create .env
notepad .env

Add:

ELEVENLABS_API_KEY=your_key_here
31. Commit
git add .
git commit -m "Move secrets to environment variables"
32. Add CI Pipeline

Create file:

mkdir .github\workflows
notepad .github\workflows\ci.yml

Paste:

name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install deps
        run: |
          pip install -r requirements.txt || echo "no requirements"

      - name: Lint
        run: |
          pip install ruff
          ruff check .

      - name: Import test
        run: |
          python -c "import main"
33. Commit
git add .
git commit -m "Add CI pipeline"
34. Final Push
git push
35. Validation Checklist (Do Not Skip)
Only ONE file accesses serial
No global state variables remain
assistant.py no longer exists
main.py is orchestration only
Each module has single responsibility
System still behaves exactly the same
Bottom Line

Do it in this order.
Do not combine steps.
Test between every move.

If something breaks, stop immediately and fix before proceeding.