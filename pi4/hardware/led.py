"""
hardware/led.py - APA102 LED driver
3x APA102 RGB LEDs via SPI bus 0, CE1.
All animation methods are non-blocking (run in daemon threads).
Call stop_anim() or any show_* to cancel the running animation.
"""

import math
import threading
import time

import spidev


class APA102:
    def __init__(self, n: int = 3):
        self.n = n
        self.spi = spidev.SpiDev()
        self.spi.open(0, 1)
        self.spi.max_speed_hz = 1_000_000
        self._pixels = [(0, 0, 0)] * n
        self._lock = threading.Lock()
        self._anim_thread = None
        self._stop_anim = threading.Event()

    # ── Low-level write ───────────────────────────────────────────────────────

    def _write(self, pixels):
        buf = [0x00] * 4
        for r, g, b in pixels:
            buf += [0xFF, b, g, r]
        buf += [0xFF] * 4
        with self._lock:
            self.spi.xfer2(buf)

    # ── Single-frame helpers ──────────────────────────────────────────────────

    def set_all(self, r: int, g: int, b: int):
        self._write([(r, g, b)] * self.n)

    def set_pixel(self, i: int, r: int, g: int, b: int):
        px = list(self._pixels)
        px[i] = (r, g, b)
        self._pixels = px
        self._write(px)

    def off(self):
        self._write([(0, 0, 0)] * self.n)

    # ── Animation control ─────────────────────────────────────────────────────

    def stop_anim(self):
        self._stop_anim.set()
        if self._anim_thread and self._anim_thread.is_alive():
            self._anim_thread.join(timeout=2)
        self._stop_anim.clear()

    def _run_anim(self, fn):
        self.stop_anim()
        self._anim_thread = threading.Thread(target=fn, daemon=True)
        self._anim_thread.start()

    # ── Status animations ─────────────────────────────────────────────────────

    def show_idle(self):
        def anim():
            steps = 80; period = 5.0; floor = 1; peak = 7
            while not self._stop_anim.is_set():
                for i in range(steps):
                    if self._stop_anim.is_set():
                        return
                    t = i / steps
                    s = (math.sin(2 * math.pi * t - math.pi / 2) + 1) / 2
                    v = int(floor + (peak - floor) * (s ** 1.8))
                    self._write([(0, v, v)] * self.n)
                    time.sleep(period / steps)
        self._run_anim(anim)

    def show_idle_kids(self):
        def anim():
            steps = 80; period = 4.0; floor = 1; peak = 6
            while not self._stop_anim.is_set():
                for i in range(steps):
                    if self._stop_anim.is_set():
                        return
                    t = i / steps
                    s = (math.sin(2 * math.pi * t - math.pi / 2) + 1) / 2
                    v = int(floor + (peak - floor) * (s ** 1.8))
                    self._write([(v, v, 0)] * self.n)
                    time.sleep(period / steps)
        self._run_anim(anim)

    def show_kids_mode_on(self):
        def anim():
            for _ in range(3):
                if self._stop_anim.is_set():
                    return
                self._write([(10, 10, 0)] * self.n); time.sleep(0.15)
                self._write([(0, 0, 0)] * self.n);     time.sleep(0.10)
        self._run_anim(anim)

    def show_kids_mode_off(self):
        def anim():
            for _ in range(3):
                if self._stop_anim.is_set():
                    return
                self._write([(0, 10, 10)] * self.n); time.sleep(0.15)
                self._write([(0, 0, 0)] * self.n);     time.sleep(0.10)
        self._run_anim(anim)

    def show_wake(self):
        self.stop_anim(); self.set_all(8, 8, 8)

    def show_recording(self):
        self.stop_anim(); self.set_all(12, 0, 0)

    def show_thinking(self):
        def anim():
            i = 0
            while not self._stop_anim.is_set():
                px = [(0, 0, 0)] * self.n
                px[i % self.n] = (0, 0, 10)
                self._write(px); time.sleep(0.12); i += 1
        self._run_anim(anim)

    def show_speaking(self):
        self.stop_anim(); self.set_all(0, 8, 0)

    def show_error(self):
        def anim():
            for _ in range(6):
                if self._stop_anim.is_set():
                    return
                self._write([(12, 0, 0)] * self.n); time.sleep(0.1)
                self._write([(0, 0, 0)] * self.n);  time.sleep(0.1)
        self._run_anim(anim)

    def show_followup(self):
        def anim():
            while not self._stop_anim.is_set():
                for v in list(range(0, 9, 3)) + list(range(9, 0, -3)):
                    if self._stop_anim.is_set():
                        return
                    self._write([(v, 0, v)] * self.n); time.sleep(0.04)
        self._run_anim(anim)

    def show_ptt(self):
        self.stop_anim(); self.set_all(8, 6, 0)

    # ── Emotion-linked LED breathing ──────────────────────────────────────────

    _EMOTION_LED = {
        "NEUTRAL":   (0,  8,  8, 4.0, False),  # soft cyan, 4s
        "HAPPY":     (10, 8,  0, 3.0, False),  # warm yellow, 3s
        "CURIOUS":   (0,  10,10, 3.5, False),  # bright cyan, 3.5s
        "ANGRY":     (10,  0, 0, 2.0, False),  # red, 2s fast
        "SLEEPY":    (4,   0, 6, 6.0, False),  # dim purple, 6s slow
        "SURPRISED": (12, 12,12, 0.3, True),   # white flash → cyan
        "SAD":       (0,   0, 6, 6.0, False),  # dim blue, 6s
        "CONFUSED":  (8,   0, 8, 2.5, False),  # pulsing magenta, 2.5s
    }

    def show_emotion(self, emotion: str):
        cfg = self._EMOTION_LED.get(emotion.upper(), self._EMOTION_LED["NEUTRAL"])
        r, g, b, period, flash = cfg

        if flash:
            def anim():
                for _ in range(4):
                    if self._stop_anim.is_set(): return
                    self._write([(12, 12, 12)] * self.n); time.sleep(0.10)
                    if self._stop_anim.is_set(): return
                    self._write([(0, 0, 0)] * self.n);    time.sleep(0.08)
                steps = list(range(1, 9, 1))
                while not self._stop_anim.is_set():
                    for v in steps:
                        if self._stop_anim.is_set(): return
                        self._write([(0, v, v)] * self.n); time.sleep(0.04)
                    for v in reversed(steps):
                        if self._stop_anim.is_set(): return
                        self._write([(0, v, v)] * self.n); time.sleep(0.04)
            self._run_anim(anim)
        else:
            half = period / 2.0
            steps = max(10, int(half / 0.04))
            def anim(r=r, g=g, b=b, steps=steps, half=half):
                while not self._stop_anim.is_set():
                    for i in range(steps):
                        if self._stop_anim.is_set(): return
                        v = i / steps
                        self._write([(int(r * v), int(g * v), int(b * v))] * self.n)
                        time.sleep(half / steps)
                    for i in range(steps):
                        if self._stop_anim.is_set(): return
                        v = max(0.07, 1.0 - i / steps)
                        self._write([(int(r * v), int(g * v), int(b * v))] * self.n)
                        time.sleep(half / steps)
            self._run_anim(anim)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def close(self):
        self.stop_anim()
        self.off()
        self.spi.close()
