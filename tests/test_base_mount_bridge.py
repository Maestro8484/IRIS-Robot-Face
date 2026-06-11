from __future__ import annotations

import builtins
import importlib
import sys

import pytest


def _load_bridge(monkeypatch, mock_audio):
    sys.modules.pop("hardware.base_mount_bridge", None)
    bridge = importlib.import_module("hardware.base_mount_bridge")
    bridge.CMD_PORT = 10500
    bridge._mute_restore[0] = 70
    return bridge


class _TouchFile:
    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


@pytest.mark.parametrize(
    ("gesture", "expected_action", "expected_effect"),
    [
        ("VOL+", "VOL+", ("audio", "louder")),
        ("VOL-", "VOL-", ("audio", "quieter")),
        ("STOP", "STOP", ("udp", b"STOP")),
        ("LISTEN", "LISTEN", ("listen", "/tmp/iris_manual_listen")),
        ("FORWARD", "LISTEN", ("listen", "/tmp/iris_manual_listen")),
        ("BACKWARD", "WAKE", ("udp", b"EYES:WAKE")),
        ("CW", "MUTE", ("mute", 0)),
        ("CCW", "SKIP", ("noop", None)),
        ("SLEEP", "SLEEP", ("udp", b"EYES:SLEEP")),
        ("WAKE", "WAKE", ("udp", b"EYES:WAKE")),
        ("MUTE", "MUTE", ("mute", 0)),
    ],
)
def test_gesture_map_dispatch(
    gesture,
    expected_action,
    expected_effect,
    monkeypatch,
    mock_audio,
    mock_udp,
    fake_config,
):
    bridge = _load_bridge(monkeypatch, mock_audio)
    gesture_map = dict(bridge._DEFAULT_GESTURE_MAP)
    gesture_map.update({"SLEEP": "SLEEP", "WAKE": "WAKE", "MUTE": "MUTE"})
    monkeypatch.setattr(bridge, "_load_gesture_map", lambda: gesture_map)

    touched = []

    def fake_open(path, mode="r", *args, **kwargs):
        touched.append((path, mode))
        return _TouchFile()

    action = bridge._load_gesture_map().get(gesture, "SKIP")
    assert action == expected_action

    if expected_effect[0] == "listen":
        monkeypatch.setattr(builtins, "open", fake_open)
    elif expected_effect[0] == "mute":
        mock_audio["volume"] = 45

    bridge.BaseMountBridge(fake_config)._dispatch(action)

    kind, expected = expected_effect
    if kind == "audio":
        assert mock_audio["commands"][-1] == expected
    elif kind == "udp":
        assert mock_udp[-1] == (expected, ("127.0.0.1", 10500))
    elif kind == "listen":
        assert touched == [(expected, "w")]
    elif kind == "mute":
        assert mock_audio["volume"] == expected


def test_mute_action_state(monkeypatch, mock_audio, fake_config):
    bridge = _load_bridge(monkeypatch, mock_audio)
    bridge._mute_restore[0] = 70
    mock_audio["volume"] = 42
    subject = bridge.BaseMountBridge(fake_config)

    subject._dispatch("MUTE")
    assert mock_audio["volume"] == 0
    assert bridge._mute_restore[0] == 42

    subject._dispatch("MUTE")
    assert mock_audio["volume"] == 42


def test_listen_invocation_paths(monkeypatch, mock_audio, mock_udp, fake_config):
    bridge = _load_bridge(monkeypatch, mock_audio)
    touched = []

    def fake_open(path, mode="r", *args, **kwargs):
        touched.append((path, mode))
        return _TouchFile()

    monkeypatch.setattr(builtins, "open", fake_open)
    subject = bridge.BaseMountBridge(fake_config)

    subject._dispatch(bridge._DEFAULT_GESTURE_MAP["FORWARD"])
    subject._dispatch("LISTEN")
    subject._dispatch("STOP")
    subject._dispatch("SLEEP")
    subject._dispatch("WAKE")

    assert touched == [
        ("/tmp/iris_manual_listen", "w"),
        ("/tmp/iris_manual_listen", "w"),
    ]
    assert mock_udp == [
        (b"STOP", ("127.0.0.1", 10500)),
        (b"EYES:SLEEP", ("127.0.0.1", 10500)),
        (b"EYES:WAKE", ("127.0.0.1", 10500)),
    ]


class _OneLineSerial:
    is_open = True

    def __init__(self, line):
        self._line = line
        self._used = False

    def readline(self):
        if not self._used:
            self._used = True
            return self._line
        raise KeyboardInterrupt

    def close(self):
        self.is_open = False


def test_serial_parse_health_line(monkeypatch, mock_audio, fake_config):
    bridge = _load_bridge(monkeypatch, mock_audio)
    dispatched = []
    subject = bridge.BaseMountBridge(fake_config)
    subject._ser = _OneLineSerial(b"HEALTH person=OK paj=DEGRADED\n")

    monkeypatch.setattr(bridge, "_load_gesture_map", lambda: bridge._DEFAULT_GESTURE_MAP)
    monkeypatch.setattr(subject, "_dispatch", lambda action: dispatched.append(action))

    with pytest.raises(KeyboardInterrupt):
        subject._read_loop()

    assert dispatched == []


def test_invalid_gesture_string(monkeypatch, mock_audio, fake_config):
    bridge = _load_bridge(monkeypatch, mock_audio)
    dispatched = []
    subject = bridge.BaseMountBridge(fake_config)
    subject._ser = _OneLineSerial(b"NOT_A_REAL_GESTURE\n")

    monkeypatch.setattr(bridge, "_load_gesture_map", lambda: bridge._DEFAULT_GESTURE_MAP)
    monkeypatch.setattr(subject, "_dispatch", lambda action: dispatched.append(action))

    with pytest.raises(KeyboardInterrupt):
        subject._read_loop()

    assert dispatched == []
