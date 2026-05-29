from __future__ import annotations

import sys
import types

import pytest

import iris_post


class FakeLeds:
    def __init__(self, n=3):
        self.n = n
        self.writes = []

    def _write(self, colors):
        self.writes.append(colors[0])


def _stub_check(layer, check, status=iris_post.PASS):
    def _inner(self):
        return self.record(layer, check, status)

    return _inner


@pytest.fixture
def quiet_post(monkeypatch):
    monkeypatch.setattr(iris_post._POST, "log", lambda self, line: None)
    monkeypatch.setattr(iris_post.time, "sleep", lambda seconds: None)


@pytest.fixture
def all_checks_pass(monkeypatch):
    patches = {
        "l0_serial": ("L0", "serial"),
        "l0_mic": ("L0", "mic"),
        "l0_camera": ("L0", "camera"),
        "l0_gesture": ("L0", "gesture"),
        "l1_gandalf": ("L1", "gandalf"),
        "l1_services": ("L1", "services"),
        "l1_models": ("L1", "models"),
        "l2_display": ("L2", "display"),
        "l3_router": ("L3", "router"),
        "l3_tts": ("L3", "tts"),
        "l3_llm": ("L3", "llm"),
        "l3_intent_log": ("L3", "intent log"),
        "l4_config": ("L4", "config"),
        "l4_md5": ("L4", "md5"),
        "l4_ownership": ("L4", "ownership"),
    }
    for method, (layer, check) in patches.items():
        monkeypatch.setattr(iris_post._POST, method, _stub_check(layer, check))


def test_layer_color_sequence(quiet_post, all_checks_pass):
    leds = FakeLeds()

    iris_post.run_post(leds=leds, verbose=False)

    assert leds.writes[:5] == [
        iris_post._LED_LAYERS[0],
        iris_post._LED_LAYERS[1],
        iris_post._LED_LAYERS[2],
        iris_post._LED_LAYERS[3],
        iris_post._LED_LAYERS[4],
    ]


def test_pass_outcome(quiet_post, all_checks_pass):
    leds = FakeLeds()

    result = iris_post.run_post(leds=leds, verbose=False)

    assert result["verdict"] == "AUTHORIZED"
    assert result["n_fail"] == 0
    assert iris_post._LED_PASS in leds.writes
    assert leds.writes[-1] == (0, 60, 80)


def test_fail_outcome(quiet_post, all_checks_pass, monkeypatch):
    leds = FakeLeds()
    monkeypatch.setattr(iris_post._POST, "l2_display", _stub_check("L2", "display", iris_post.FAIL))

    result = iris_post.run_post(leds=leds, verbose=False)

    assert result["verdict"] == "FAIL"
    assert result["n_fail"] == 1
    assert result["checks"][7]["layer"] == "L2"
    assert result["checks"][7]["status"] == iris_post.FAIL
    assert iris_post._LED_FAIL in leds.writes
    assert leds.writes[-1] == iris_post._LED_FAIL


def _install_missing_smbus(monkeypatch):
    module = types.ModuleType("smbus")

    def absent_bus(bus_id):
        raise OSError(f"no test bus {bus_id}")

    module.SMBus = absent_bus
    monkeypatch.setitem(sys.modules, "smbus", module)


def test_gesture_sensor_required_false(quiet_post, monkeypatch):
    _install_missing_smbus(monkeypatch)
    monkeypatch.setattr(iris_post, "GESTURE_SENSOR_REQUIRED", False)

    post = iris_post._POST(leds=None, teensy=None, pa=None, verbose=False)

    assert post.l0_gesture() == iris_post.WARN
    assert post.results[-1]["status"] == iris_post.WARN


def test_gesture_sensor_required_true(quiet_post, monkeypatch):
    _install_missing_smbus(monkeypatch)
    monkeypatch.setattr(iris_post, "GESTURE_SENSOR_REQUIRED", True)

    post = iris_post._POST(leds=None, teensy=None, pa=None, verbose=False)

    assert post.l0_gesture() == iris_post.FAIL
    assert post.results[-1]["status"] == iris_post.FAIL
