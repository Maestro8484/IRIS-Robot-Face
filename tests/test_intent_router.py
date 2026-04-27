#!/usr/bin/env python3
"""
Loop 1: Offline unit tests for IntentRouter.
Run on SuperMaster -- no Pi4, no hardware required.

Usage (from repo root):
    python tests/test_intent_router.py
"""

import sys
import os

# Add pi4/ to path so core.* and services.* imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pi4"))

# Silence the iris_config.json FileNotFoundError print (expected on SuperMaster)
import io
import contextlib

with contextlib.redirect_stdout(io.StringIO()):
    from core.intent_router import (
        IntentRouter,
        ROUTE_REFLEX, ROUTE_COMMAND, ROUTE_UTILITY, ROUTE_AMBIGUOUS, ROUTE_LLM,
    )


router = IntentRouter()

PASS = 0
FAIL = 0


def check(n: int, text: str, exp_route: str, exp_action: str = None,
          exp_payload_result: str = None, allow_routes: tuple = None):
    global PASS, FAIL
    result = router.classify(text)
    ok_route = (result.route == exp_route) or (allow_routes and result.route in allow_routes)
    ok_action = (exp_action is None) or (result.action == exp_action)
    ok_payload = (exp_payload_result is None) or (
        result.payload and result.payload.get("result") == exp_payload_result
    )
    if ok_route and ok_action and ok_payload:
        PASS += 1
        print(f"  PASS  [{n:02d}] '{text}' -> {result.route}/{result.action}"
              + (f" result={result.payload.get('result')}" if result.payload and "result" in result.payload else ""))
    else:
        FAIL += 1
        want = f"{exp_route}/{exp_action or '*'}"
        if allow_routes:
            want = f"({'/'.join(allow_routes)})/{exp_action or '*'}"
        got  = f"{result.route}/{result.action}"
        if result.payload and "result" in result.payload:
            got += f" result={result.payload['result']}"
        print(f"  FAIL  [{n:02d}] '{text}'  want={want}  got={got}")


print("\nLoop 1 -- IntentRouter unit tests\n")

# Layer 0: REFLEX
check(1,  "go to sleep",              ROUTE_REFLEX,    "SLEEP")
check(2,  "goodnight",                ROUTE_REFLEX,    "SLEEP")
check(3,  "good night iris",          ROUTE_REFLEX,    "SLEEP")
check(4,  "stop talking",             ROUTE_REFLEX,    "STOP")
check(5,  "shut up",                  ROUTE_REFLEX,    "STOP")
check(6,  "wake up",                  ROUTE_REFLEX,    "WAKE")

# Layer 1: COMMAND
check(7,  "volume up",                ROUTE_COMMAND,   "VOLUME_UP")
check(8,  "turn it up",               ROUTE_COMMAND,   "VOLUME_UP")
check(9,  "kids mode on",             ROUTE_COMMAND,   "KIDS_ON")

# Layer 2: UTILITY
check(10, "what time is it",          ROUTE_UTILITY,   "TIME")
check(11, "what is 27 times 43",      ROUTE_UTILITY,   "MATH",  exp_payload_result="1161")
check(12, "what day is it",           ROUTE_UTILITY,   "DATE")

# Layer 4: LLM
check(13, "tell me a story",          ROUTE_LLM,       "LLM")
check(14, "you're annoying",          ROUTE_LLM,       "LLM")

# Layer 3: AMBIGUOUS (or REFLEX/STOP depending on impl)
check(15, "that's enough",            ROUTE_AMBIGUOUS, "STOP",
          allow_routes=(ROUTE_AMBIGUOUS, ROUTE_REFLEX))
check(16, "sleepy",                   ROUTE_AMBIGUOUS)

# Case 17: modelfile forbidden phrase block -- verify the block exists in file
modelfile_path = os.path.join(os.path.dirname(__file__), "..", "ollama", "iris_modelfile.txt")
try:
    with open(modelfile_path, encoding="utf-8") as f:
        mf = f.read()
    if "As a large language model" in mf and "NEVER say" in mf:
        PASS += 1
        print(f"  PASS  [17] modelfile contains 'NEVER say' forbidden phrase block")
    else:
        FAIL += 1
        print(f"  FAIL  [17] modelfile missing 'NEVER say' block (expected after Batch 3-F edit)")
except FileNotFoundError:
    FAIL += 1
    print(f"  FAIL  [17] iris_modelfile.txt not found at {modelfile_path}")

print(f"\nResult: {PASS} PASS  {FAIL} FAIL  (total {PASS+FAIL}/17)")
if FAIL:
    print("\nSome tests failed. Do not proceed to Loop 2.")
    sys.exit(1)
else:
    print("\nAll 17 passed. Proceed to Loop 2.")
    sys.exit(0)
