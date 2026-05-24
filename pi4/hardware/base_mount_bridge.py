import json
import socket
import threading
import time

from core.config import CMD_PORT
from hardware.audio_io import handle_volume_command

_CONFIG_PATH = "/home/pi/iris_config.json"

_DEFAULT_GESTURE_MAP = {
    "VOL+":   "VOL+",
    "VOL-":   "VOL-",
    "STOP":   "STOP",
    "LISTEN": "LISTEN",
}


def _load_gesture_map():
    try:
        with open(_CONFIG_PATH) as f:
            cfg = json.load(f)
        return cfg.get("GESTURE_MAP", _DEFAULT_GESTURE_MAP)
    except Exception:
        return _DEFAULT_GESTURE_MAP


class BaseMountBridge:
    def __init__(self, config):
        self._port = getattr(config, "BASE_MOUNT_PORT", "/dev/ttyACM1")
        self._baud = getattr(config, "BASE_MOUNT_BAUD", 115200)
        self._ser = None

    def start(self):
        import serial as _serial
        try:
            self._ser = _serial.Serial(self._port, self._baud, timeout=1)
            print(f"[BASE] Teensy 4.0 connected on {self._port}", flush=True)
        except Exception as e:
            print(f"[BASE] WARN: could not open {self._port}: {e}", flush=True)
            return
        threading.Thread(target=self._read_loop, daemon=True).start()

    def _dispatch(self, action):
        if action == "VOL+":
            try:
                handle_volume_command("louder")
            except Exception as e:
                print(f"[BASE] VOL+ error: {e}", flush=True)
        elif action == "VOL-":
            try:
                handle_volume_command("quieter")
            except Exception as e:
                print(f"[BASE] VOL- error: {e}", flush=True)
        elif action == "STOP":
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.sendto(b"STOP", ("127.0.0.1", CMD_PORT))
            except Exception as e:
                print(f"[BASE] STOP error: {e}", flush=True)
        elif action == "LISTEN":
            try:
                open("/tmp/iris_manual_listen", "w").close()
            except Exception as e:
                print(f"[BASE] LISTEN error: {e}", flush=True)
        elif action == "SKIP":
            pass
        else:
            print(f"[BASE] unknown action: {action!r}", flush=True)

    def _read_loop(self):
        _err_logged = False
        while True:
            try:
                if self._ser is None or not self._ser.is_open:
                    import serial as _serial
                    self._ser = _serial.Serial(self._port, self._baud, timeout=1)
                    print(f"[BASE] Reconnected on {self._port}", flush=True)
                    _err_logged = False
                line = self._ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                gesture_map = _load_gesture_map()
                action = gesture_map.get(line, "SKIP")
                print(f"[GESTURE] gesture={line} action={action}", flush=True)
                if action != "SKIP":
                    self._dispatch(action)
            except Exception as e:
                if not _err_logged:
                    print(f"[BASE] Serial error: {e} -- reconnecting in 5s", flush=True)
                    _err_logged = True
                try:
                    if self._ser:
                        self._ser.close()
                except Exception:
                    pass
                self._ser = None
                time.sleep(5)
