from __future__ import annotations

import time as pytime

import pytest

from core import intent_router as router_mod
from core.intent_router import (
    IntentRouter,
    ROUTE_AMBIGUOUS,
    ROUTE_COMMAND,
    ROUTE_LLM,
    ROUTE_REFLEX,
    ROUTE_UTILITY,
)


@pytest.fixture
def router():
    return IntentRouter()


def _fixed_time(hour: int):
    return pytime.struct_time((2026, 5, 29, hour, 15, 0, 4, 149, -1))


@pytest.mark.parametrize(
    ("phrase", "action"),
    [
        ("go to sleep", "SLEEP"),
        ("good night iris", "SLEEP"),
        ("wake up", "WAKE"),
        ("stop talking", "STOP"),
        ("cancel", "STOP"),
    ],
)
def test_layer0_reflex(router, phrase, action):
    result = router.classify(phrase)

    assert result.route == ROUTE_REFLEX
    assert result.action == action


@pytest.mark.parametrize(
    ("phrase", "action"),
    [
        ("volume up", "VOLUME_UP"),
        ("turn it down", "VOLUME_DOWN"),
        ("kids mode on", "KIDS_ON"),
        ("kids mode off", "KIDS_OFF"),
        ("set volume to 50 percent", "VOLUME_PCT"),
    ],
)
def test_layer1_command(router, phrase, action):
    result = router.classify(phrase)

    assert result.route == ROUTE_COMMAND
    assert result.action == action


def test_layer2_utility(router, monkeypatch):
    monkeypatch.setattr(router_mod.random, "randint", lambda lo, hi: lo)
    monkeypatch.setattr(router_mod.time, "localtime", lambda: _fixed_time(10))

    math_result = router.classify("what is 27 times 43")
    time_result = router.classify("what time is it")
    date_result = router.classify("what day is it")
    random_result = router.classify("pick a random number between 5 and 10")

    assert (math_result.route, math_result.action, math_result.payload["result"]) == (
        ROUTE_UTILITY,
        "MATH",
        "1161",
    )
    assert (time_result.route, time_result.action) == (ROUTE_UTILITY, "TIME")
    assert (date_result.route, date_result.action) == (ROUTE_UTILITY, "DATE")
    assert (random_result.route, random_result.action, random_result.payload["result"]) == (
        ROUTE_UTILITY,
        "RANDOM_NUMBER",
        "5",
    )


def test_layer3_ambiguous(router, monkeypatch):
    enough = router.classify("that's enough")

    monkeypatch.setattr(router_mod.time, "localtime", lambda: _fixed_time(22))
    sleepy_night = router.classify("sleepy")

    monkeypatch.setattr(router_mod.time, "localtime", lambda: _fixed_time(14))
    sleepy_day = router.classify("sleepy")

    turn_down = router.classify("turn it down")

    assert (enough.route, enough.action) == (ROUTE_AMBIGUOUS, "STOP")
    assert (sleepy_night.route, sleepy_night.action) == (ROUTE_AMBIGUOUS, "SLEEP")
    assert (sleepy_day.route, sleepy_day.action) == (ROUTE_AMBIGUOUS, "LLM")
    assert (turn_down.route, turn_down.action) == (ROUTE_COMMAND, "VOLUME_DOWN")


@pytest.mark.parametrize("phrase", ["tell me a story", "what should we build next"])
def test_layer4_llm_fallthrough(router, phrase):
    result = router.classify(phrase)

    assert result.route == ROUTE_LLM
    assert result.action == "LLM"


def test_failopen_on_exception(monkeypatch):
    def explode(self, raw, state):
        raise RuntimeError("forced classifier failure")

    monkeypatch.setattr(IntentRouter, "_classify", explode)

    result = IntentRouter().classify("anything at all")

    assert result.route == ROUTE_LLM
    assert result.action == "LLM"
