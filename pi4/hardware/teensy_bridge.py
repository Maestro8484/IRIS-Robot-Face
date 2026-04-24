"""
hardware/teensy_bridge.py - Teensy 4.0 serial bridge
SINGLE OWNER of /dev/ttyACM0. No other module may open this port.
All other callers (iris_web.py, cron scripts) must use UDP → 127.0.0.1:CMD_PORT.

Provides:
  TeensyBridge(port, baud)
    .send_emotion(emotion)      — sends EMOTION:<X>\n
    .send_command(cmd)          — sends <cmd>\n (raw, no prefix)
    .close()                    — stops reader thread, closes serial
"""

import threading
import time

import serial

from core.config import TEENSY_PORT, TEENSY_BAUD


class TeensyBridge:
    def __init__(self, port: str = TEENSY_PORT, baud: int = TEENSY_BAUD):
        self._port = port
        self._baud = baud
        self._ser = None
        self._lock = threading.Lock()
        self._active = True
        threading.Thread(target=self._reader, daemon=True).start()

    def _open(self):
        try:
            s = serial.Serial(self._port, self._baud, timeout=1)
            s.reset_input_buffer()
            print(f"[EYES] Teensy connected on {self._port}", flush=True)
            return s
        except (serial.SerialException, OSError):
            return None

    def _reader(self):
        while self._active:
            with self._lock:
                if self._ser is None or not self._ser.is_open:
                    self._ser = self._open()
            if self._ser is None:
                time.sleep(5)
                continue
            try:
                line = self._ser.readline().decode(errors="ignore").strip()
                if line:
                    print(f"[EYES] << {line}", flush=True)
            except (serial.SerialException, OSError):
                print("[EYES] Serial disconnected -- will retry", flush=True)
                with self._lock:
                    try:
                        self._ser.close()
                    except Exception:
                        pass
                    self._ser = None
                time.sleep(5)

    def send_emotion(self, emotion: str) -> bool:
        with self._lock:
            if self._ser is None or not self._ser.is_open:
                return False
            try:
                self._ser.write(f"EMOTION:{emotion}\n".encode())
                self._ser.flush()
                print(f"[EYES] >> EMOTION:{emotion}", flush=True)
                return True
            except (serial.SerialException, OSError) as e:
                print(f"[EYES] Send failed: {e}", flush=True)
                try:
                    self._ser.close()
                except Exception:
                    pass
                self._ser = None
                return False

    def send_command(self, cmd: str) -> bool:
        """Send a raw command string (no EMOTION: prefix) to the Teensy."""
        with self._lock:
            if self._ser is None or not self._ser.is_open:
                return False
            try:
                self._ser.write(f"{cmd}\n".encode())
                self._ser.flush()
                print(f"[EYES] >> {cmd}", flush=True)
                return True
            except (serial.SerialException, OSError) as e:
                print(f"[EYES] Send failed: {e}", flush=True)
                try:
                    self._ser.close()
                except Exception:
                    pass
                self._ser = None
                return False

    def close(self):
        self._active = False
        with self._lock:
            if self._ser:
                try:
                    self._ser.close()
                except Exception:
                    pass
