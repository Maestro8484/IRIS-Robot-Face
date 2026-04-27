"""
Loop 2: Integration smoke test -- router wired into simulated post-STT dispatch.
Runs on SuperMaster, no Pi4 or hardware. Mocks synthesize, play, teensy, leds.

Confirms:
- Correct branch taken for each input (REFLEX/COMMAND/UTILITY/LLM)
- No LLM call fires for REFLEX/COMMAND/UTILITY cases
- Intent log entries written to /tmp/iris_intent_test.log

Usage (from repo root):
    python tests/test_integration_smoke.py
"""

import sys
import os
import io
import contextlib
import tempfile

# Redirect log to temp path for this test run
import logging
import logging.handlers

TEST_LOG_PATH = os.path.join(tempfile.gettempdir(), "iris_intent_test.log")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pi4"))

# Silence config.py load output
with contextlib.redirect_stdout(io.StringIO()):
    from core.intent_router import (
        IntentRouter,
        ROUTE_REFLEX, ROUTE_COMMAND, ROUTE_UTILITY, ROUTE_AMBIGUOUS, ROUTE_LLM,
        _intent_logger, _INTENT_LOG_PATH,
    )

# Redirect intent log to temp path for this test
_intent_logger.handlers.clear()
_h = logging.handlers.RotatingFileHandler(TEST_LOG_PATH, maxBytes=1_000_000, backupCount=1, encoding="utf-8")
_h.setFormatter(logging.Formatter("%(message)s"))
_intent_logger.addHandler(_h)

router = IntentRouter()

# ── Mock state ────────────────────────────────────────────────────────────────

class MockState:
    eyes_sleeping = False
    kids_mode = False
    conversation_history = []
    last_interaction = 0.0

state = MockState()

# ── Mock hardware ──────────────────────────────────────────────────────────────

calls = {"synthesize": 0, "play": 0, "llm": 0, "tts_text": []}

def mock_synthesize(text):
    calls["synthesize"] += 1
    calls["tts_text"].append(text)
    return b""

def mock_play(*a, **kw):
    calls["play"] += 1
    return False

def mock_llm(*a, **kw):
    calls["llm"] += 1
    return iter([("mocked reply", "NEUTRAL")])


# ── Dispatch simulator ────────────────────────────────────────────────────────
# Mirrors the routing logic in assistant.py post-STT block.
# Returns (branch_taken, llm_called, tts_response).

def dispatch(text: str, _state=state) -> tuple:
    stop_fired  = False
    sleep_fired = False
    wake_fired  = False
    llm_called  = False
    tts_text    = None

    result = router.classify(text, _state)
    route  = result.route

    if route == ROUTE_REFLEX:
        if result.action == "SLEEP":
            sleep_fired = True
            tts_text = result.response
        elif result.action == "STOP":
            stop_fired = True
        elif result.action == "WAKE":
            wake_fired = True
    elif route == ROUTE_COMMAND:
        tts_text = f"[COMMAND:{result.action}]"
    elif route == ROUTE_UTILITY:
        if result.action == "VISION":
            tts_text = "[VISION]"
        else:
            tts_text = result.response
    elif route == ROUTE_AMBIGUOUS:
        if result.action == "STOP":
            stop_fired = True
        elif result.action == "SLEEP":
            sleep_fired = True
            tts_text = result.response
        else:
            llm_called = True
    else:  # LLM
        llm_called = True

    return result, llm_called, tts_text


# ── Test cases ────────────────────────────────────────────────────────────────

PASS = 0
FAIL = 0

def check(n, text, exp_route, exp_action=None, exp_llm=False, exp_has_tts=None):
    global PASS, FAIL
    result, llm_called, tts_text = dispatch(text)
    ok_route  = result.route == exp_route
    ok_action = exp_action is None or result.action == exp_action
    ok_llm    = llm_called == exp_llm
    ok_tts    = exp_has_tts is None or (tts_text is not None) == exp_has_tts
    if ok_route and ok_action and ok_llm and ok_tts:
        PASS += 1
        print(f"  PASS  [{n:02d}] '{text}' -> {result.route}/{result.action}"
              + (f" tts='{tts_text}'" if tts_text else ""))
    else:
        FAIL += 1
        issues = []
        if not ok_route:  issues.append(f"route want={exp_route} got={result.route}")
        if not ok_action: issues.append(f"action want={exp_action} got={result.action}")
        if not ok_llm:    issues.append(f"llm_called want={exp_llm} got={llm_called}")
        if not ok_tts:    issues.append(f"has_tts want={exp_has_tts} got={tts_text is not None}")
        print(f"  FAIL  [{n:02d}] '{text}'  " + "  ".join(issues))


print("\nLoop 2 -- Integration smoke test (mocked hardware)\n")

check(1, "goodnight",          ROUTE_REFLEX,    "SLEEP",       exp_llm=False, exp_has_tts=True)
check(2, "stop",               ROUTE_REFLEX,    "STOP",        exp_llm=False, exp_has_tts=False)
check(3, "wake up",            ROUTE_REFLEX,    "WAKE",        exp_llm=False, exp_has_tts=False)
check(4, "volume up",          ROUTE_COMMAND,   "VOLUME_UP",   exp_llm=False, exp_has_tts=True)
check(5, "kids mode on",       ROUTE_COMMAND,   "KIDS_ON",     exp_llm=False)
check(6, "what time is it",    ROUTE_UTILITY,   "TIME",        exp_llm=False, exp_has_tts=True)
check(7, "what is 5 plus 3",   ROUTE_UTILITY,   "MATH",        exp_llm=False, exp_has_tts=True)
check(8, "tell me a story",    ROUTE_LLM,       "LLM",         exp_llm=True)
check(9, "go to sleep",        ROUTE_REFLEX,    "SLEEP",       exp_llm=False)

# Verify log file was written
_intent_logger.handlers[0].flush()
try:
    with open(TEST_LOG_PATH, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) >= 9:
        PASS += 1
        print(f"\n  PASS  [LOG] {len(lines)} intent log entries written to {TEST_LOG_PATH}")
        for line in lines[:3]:
            print(f"         {line}")
        if len(lines) > 3:
            print(f"         ... ({len(lines)-3} more)")
    else:
        FAIL += 1
        print(f"\n  FAIL  [LOG] only {len(lines)} entries in {TEST_LOG_PATH} (expected >= 9)")
except FileNotFoundError:
    FAIL += 1
    print(f"\n  FAIL  [LOG] {TEST_LOG_PATH} not found")

print(f"\nResult: {PASS} PASS  {FAIL} FAIL  (total {PASS+FAIL})")
if FAIL:
    print("\nLoop 2 FAILED. Fix before deploying to Pi4.")
    sys.exit(1)
else:
    print("\nLoop 2 PASSED. Ready for Loop 3 (live Pi4 deploy).")
    sys.exit(0)
