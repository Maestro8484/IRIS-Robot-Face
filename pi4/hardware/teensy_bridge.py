"""
hardware/teensy_bridge.py - Teensy 4.1 serial bridge (eyes + mouth TFT)
SINGLE OWNER of /dev/ttyIRIS_EYES. No other module may open this port.
All other callers (iris_web.py, cron scripts) must use UDP → 127.0.0.1:CMD_PORT.

Provides:
  TeensyBridge(port, baud)
    .send_emotion(emotion)      — sends EMOTION:<X>\n
    .send_command(cmd)          — sends <cmd>\n (raw, no prefix)
    .close()                    — stops reader thread, closes serial
"""

import os
import threading
import time

import serial

from core.config import TEENSY_PORT, TEENSY_BAUD

# RD-031: routine high-rate serial traffic was ~90% of journal volume — inbound
# sleep-frame echoes ([SR] …) plus per-turn outbound MOUTH/MOUTH_INTENSITY updates
# (2 Hz during TTS + idle breathe). Suppress those echoes by default. Set
# IRIS_DEBUG_SERIAL=1 to log every serial line again. Errors, DROPs,
# connect/disconnect, [VER] and FACE: state are always logged.
DEBUG_SERIAL = os.environ.get("IRIS_DEBUG_SERIAL", "").lower() not in ("", "0", "false", "no")

# Outbound command prefixes that fire at high rate (mouth animation / idle breathe).
_ROUTINE_TX_PREFIXES = ("MOUTH:", "MOUTH_INTENSITY:")
# Inbound line prefixes that are routine per-frame chatter.
_ROUTINE_RX_PREFIXES = ("[SR]",)


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
        except (serial.SerialException, OSError) as e:
            print(f"[EYES] Cannot open {self._port}: {e} -- will retry", flush=True)
            return None

    def _reader(self):
        while self._active:
            # Snapshot the handle under the lock: a concurrent failed send sets
            # self._ser = None, and reading the attribute unlocked mid-loop used
            # to raise an uncaught AttributeError that silently killed this
            # thread -- no reconnect ever, all sends DROP until service restart.
            with self._lock:
                if self._ser is None or not self._ser.is_open:
                    self._ser = self._open()
                ser = self._ser
            if ser is None:
                time.sleep(5)
                continue
            try:
                line = ser.readline().decode(errors="ignore").strip()
                if line and (DEBUG_SERIAL or not line.startswith(_ROUTINE_RX_PREFIXES)):
                    print(f"[EYES] << {line}", flush=True)
            except (serial.SerialException, OSError):
                print("[EYES] Serial disconnected -- will retry", flush=True)
                with self._lock:
                    try:
                        ser.close()
                    except Exception:
                        pass
                    if self._ser is ser:
                        self._ser = None
                time.sleep(5)
            except Exception as e:
                # Belt-and-braces: the reader thread must never die. Anything
                # unexpected (e.g. races on a handle being torn down by a send)
                # logs and retries instead of silently ending reconnects.
                print(f"[EYES] Reader error: {e} -- will retry", flush=True)
                time.sleep(5)

    def send_emotion(self, emotion: str) -> bool:
        with self._lock:
            if self._ser is None or not self._ser.is_open:
                print(f"[EYES] DROP EMOTION:{emotion} -- port not open", flush=True)
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
                print(f"[EYES] DROP {cmd} -- port not open", flush=True)
                return False
            try:
                self._ser.write(f"{cmd}\n".encode())
                self._ser.flush()
                if DEBUG_SERIAL or not cmd.startswith(_ROUTINE_TX_PREFIXES):
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
