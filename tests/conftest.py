from __future__ import annotations

import socket
import sys
import types
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
PI4_DIR = ROOT_DIR / "pi4"

for path in (str(PI4_DIR), str(ROOT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch):
    """Fail fast if a test accidentally tries real TCP or HTTP I/O."""

    def blocked_create_connection(*args, **kwargs):
        raise AssertionError(f"unexpected network connection: args={args!r} kwargs={kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", blocked_create_connection)

    try:
        import requests
    except Exception:
        return

    def blocked_request(self, method, url, *args, **kwargs):
        raise AssertionError(f"unexpected HTTP request: {method} {url}")

    monkeypatch.setattr(requests.sessions.Session, "request", blocked_request)


@pytest.fixture
def fake_config():
    return types.SimpleNamespace(
        BASE_MOUNT_PORT="mock://iris-servo",
        BASE_MOUNT_BAUD=115200,
        CMD_PORT=10500,
        GESTURE_SENSOR_REQUIRED=False,
    )


@pytest.fixture
def mock_audio(monkeypatch):
    state = {"volume": 70, "commands": [], "pcm": [], "wol_beeps": 0}
    module = types.ModuleType("hardware.audio_io")

    def handle_volume_command(direction):
        state["commands"].append(direction)

    def get_volume():
        return state["volume"]

    def set_volume(value, allow_zero=False):
        state["volume"] = value

    def play_pcm(pcm, pa=None):
        state["pcm"].append((pcm, pa))

    def play_wol_beep(pa=None):
        state["wol_beeps"] += 1

    module.handle_volume_command = handle_volume_command
    module.get_volume = get_volume
    module.set_volume = set_volume
    module.play_pcm = play_pcm
    module.play_wol_beep = play_wol_beep
    module._find_mic_device_index = lambda: 0

    monkeypatch.setitem(sys.modules, "hardware.audio_io", module)
    return state


@pytest.fixture
def mock_alsa(monkeypatch):
    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append((cmd, args, kwargs))
        return types.SimpleNamespace(returncode=0, stdout="1\n", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    return calls


@pytest.fixture
def mock_udp(monkeypatch):
    sent = []

    class FakeUdpSocket:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.closed = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.close()

        def setsockopt(self, *args):
            return None

        def sendto(self, payload, address):
            sent.append((payload, address))
            return len(payload)

        def close(self):
            self.closed = True

    monkeypatch.setattr(socket, "socket", FakeUdpSocket)
    return sent


@pytest.fixture
def mock_serial(monkeypatch):
    class FakeSerial:
        instances = []
        next_lines = []

        def __init__(self, port, baudrate, timeout=1):
            self.port = port
            self.baudrate = baudrate
            self.timeout = timeout
            self.is_open = True
            self.writes = []
            self.lines = list(FakeSerial.next_lines)
            FakeSerial.instances.append(self)

        def readline(self):
            if self.lines:
                return self.lines.pop(0)
            return b""

        def write(self, payload):
            self.writes.append(payload)
            return len(payload)

        def close(self):
            self.is_open = False

    module = types.ModuleType("serial")
    module.Serial = FakeSerial
    monkeypatch.setitem(sys.modules, "serial", module)
    return FakeSerial
