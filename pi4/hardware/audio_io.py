"""
hardware/audio_io.py - Audio input/output and volume control
wm8960 HAT, PyAudio, PCM playback with interrupt detection, record, volume.

Key design notes:
- _stop_playback is a module-level Event; import it to call .set() from outside.
- record_command() takes kids_mode as an explicit parameter (not a global).
- play_pcm_speaking() takes a TeensyBridge instance for mouth animation.
- _playback_interrupt_listener() uses adaptive baseline to ignore speaker bleed.
"""

import re
import subprocess
import threading
import time

import numpy as np
import pyaudio

from core.config import (
    SAMPLE_RATE, CHUNK, CHANNELS,
    RECORD_SECONDS, SILENCE_SECS, SILENCE_RMS,
    KIDS_RECORD_SECONDS, KIDS_SILENCE_SECS, KIDS_SILENCE_RMS,
    VOL_CONTROL, VOL_MIN, VOL_MAX, VOL_STEP,
)
from hardware.io import button_pressed


# ── Shared stop-playback event (importable by orchestrator) ───────────────────
_stop_playback = threading.Event()

# ── Interrupt detection constants ─────────────────────────────────────────────
# RMS threshold for mid-playback voice interrupt.
# NOTE: raised from 1200 → 4000 because the external amp (5V 3W, 3.5mm headphone path)
# at -5dB DAC bleeds acoustically into the ReSpeaker mics at ~1200-4500 RMS.
# A human voice on top of that bleed reaches 5000-8000, so 4000 still catches
# interrupts while ignoring IRIS's own speaker output.
INTERRUPT_RMS_THRESHOLD = 4000

# Stop phrases checked via lightweight STT during playback
STOP_PHRASES = {
    "stop", "cancel", "nevermind", "never mind", "quiet", "shut up",
    "be quiet", "stop talking", "that's enough", "enough", "hey jarvis",
    "jarvis stop", "ok stop", "please stop",
}

# Polite filler responses that end the follow-up loop without LLM processing
FOLLOWUP_DISMISSALS = {
    "thank you", "thanks", "thank you very much", "thanks very much",
    "thank you so much", "thanks so much",
    "ok", "okay", "ok thanks", "okay thanks", "ok thank you", "okay thank you",
    "great", "great thanks", "great thank you", "sounds great",
    "got it", "got it thanks", "got it thank you",
    "alright", "all right", "alright thanks", "sounds good", "perfect",
    "no", "no thanks", "no thank you", "nope", "that's all", "that is all",
    "that's it", "that is it", "i'm good", "im good", "i'm all good",
    "cool", "cool thanks", "awesome", "wonderful", "excellent",
}


# ── Device discovery ──────────────────────────────────────────────────────────

def _find_mic_device_index() -> int | None:
    """Find wm8960 capture device by name so index shifts on reboot don't break us."""
    try:
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            if d['maxInputChannels'] > 0 and 'capture' in d['name'].lower():
                p.terminate()
                print(f"[MIC]  Auto-selected device {i}: {d['name']}", flush=True)
                return i
        p.terminate()
    except Exception as e:
        print(f"[MIC]  Auto-detect failed: {e}", flush=True)
    print("[MIC]  Using system default input device", flush=True)
    return None


def _find_wm8960_card() -> int:
    """Return ALSA card number for wm8960 HAT (default 1 if not found)."""
    try:
        out = subprocess.check_output(['aplay', '-l'], text=True)
        for line in out.splitlines():
            if 'wm8960' in line.lower():
                return int(line.split()[1].rstrip(':'))
    except Exception:
        pass
    return 1


# ── Volume control ────────────────────────────────────────────────────────────

def get_volume() -> int:
    out = subprocess.check_output(
        ["amixer", "-c", str(_find_wm8960_card()), "sget", VOL_CONTROL], text=True)
    for line in out.splitlines():
        if "Playback" in line and "[" in line:
            m = re.search(r"Playback (\d+)", line)
            if m:
                return int(m.group(1))
    return 110


def set_volume(level: int) -> int:
    level = max(VOL_MIN, min(VOL_MAX, level))
    subprocess.run(
        ["amixer", "-c", str(_find_wm8960_card()), "sset", VOL_CONTROL, str(level)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return level


def handle_volume_command(text: str) -> str | None:
    """Handle voice volume commands. Returns response string or None if not a volume command."""
    t = text.lower().strip().rstrip(".!?")
    current = get_volume()
    pct_match = re.search(r'(\d+)\s*(?:percent|%)', t)
    if pct_match and 'volume' in t:
        target = max(VOL_MIN, min(VOL_MAX, int(int(pct_match.group(1)) / 100 * VOL_MAX)))
        set_volume(target)
        return f"Volume set to {int(target / VOL_MAX * 100)} percent."
    if any(p in t for p in ("all the way up", "max volume", "volume max",
                             "full volume", "maximum volume", "as loud")):
        set_volume(VOL_MAX); return "Volume set to maximum."
    if any(p in t for p in ("all the way down", "volume low", "minimum volume",
                             "volume minimum", "as quiet")):
        set_volume(VOL_MIN); return "Volume set to minimum."
    if any(p in t for p in ("volume up", "louder", "turn it up", "increase volume",
                             "turn up", "raise volume", "higher volume", "more volume")):
        return f"Volume increased to {int(set_volume(current + VOL_STEP) / VOL_MAX * 100)} percent."
    if any(p in t for p in ("volume down", "quieter", "turn it down", "decrease volume",
                             "lower volume", "turn down", "reduce volume",
                             "less volume", "softer", "too loud")):
        return f"Volume decreased to {int(set_volume(current - VOL_STEP) / VOL_MAX * 100)} percent."
    if any(p in t for p in ("what's the volume", "whats the volume", "current volume",
                             "volume level", "how loud", "what volume")):
        return f"Volume is at {int(current / VOL_MAX * 100)} percent."
    if 'volume' in set(t.split()) and len(t.split()) <= 6:
        return f"Volume is at {int(current / VOL_MAX * 100)} percent."
    return None


# ── Playback interrupt listener ───────────────────────────────────────────────

def _playback_interrupt_listener(pa_ref, stop_event, interrupted_event):
    """
    Background thread: opens a separate mic stream during playback.
    Triggers interrupted_event if button pressed or voice exceeds adaptive threshold.

    Uses an adaptive baseline: first ~0.5 s of playback measures acoustic bleed
    from speaker into mics. Interrupt threshold = max(INTERRUPT_RMS_THRESHOLD,
    bleed_baseline * _VOICE_MULTIPLIER). Self-adjusts to pot position.
    """
    _BASELINE_CHUNKS = int(SAMPLE_RATE / CHUNK * 0.5)
    _VOICE_MULTIPLIER = 4.0

    try:
        mon = pa_ref.open(rate=SAMPLE_RATE, channels=CHANNELS,
                          format=pyaudio.paInt16, input=True,
                          frames_per_buffer=CHUNK)

        # Phase 1: measure speaker-bleed baseline
        baseline_vals = []
        for _ in range(_BASELINE_CHUNKS):
            if stop_event.is_set():
                break
            try:
                data = mon.read(CHUNK, exception_on_overflow=False)
                rms = np.sqrt(np.mean(
                    np.frombuffer(data, dtype=np.int16).astype(np.float32) ** 2))
                baseline_vals.append(rms)
            except Exception:
                break

        if baseline_vals:
            bleed_rms = float(np.percentile(baseline_vals, 90))
            effective_threshold = max(float(INTERRUPT_RMS_THRESHOLD),
                                      bleed_rms * _VOICE_MULTIPLIER)
        else:
            bleed_rms = 0.0
            effective_threshold = float(INTERRUPT_RMS_THRESHOLD)
        print(f"[INT]  Bleed baseline RMS={bleed_rms:.0f}  eff_threshold={effective_threshold:.0f}",
              flush=True)

        # Phase 2: monitor for human voice above adaptive threshold
        speech_frames = []
        speech_detected = False
        while not stop_event.is_set():
            try:
                data = mon.read(CHUNK, exception_on_overflow=False)
            except Exception:
                break
            rms = np.sqrt(np.mean(
                np.frombuffer(data, dtype=np.int16).astype(np.float32) ** 2))
            if rms > effective_threshold:
                if not speech_detected:
                    speech_detected = True
                    speech_frames = [data]
                    print(f"[INT]  Voice detected mid-playback (RMS={rms:.0f})", flush=True)
                else:
                    speech_frames.append(data)
                    # 2 consecutive chunks (~0.13 s) fires interrupt
                    if len(speech_frames) >= 2:
                        print("[INT]  Interrupt triggered", flush=True)
                        interrupted_event.set()
                        _stop_playback.set()
                        break
            else:
                if speech_detected and len(speech_frames) < 1:
                    speech_detected = False
                    speech_frames = []

        mon.stop_stream()
        mon.close()
    except Exception as e:
        print(f"[INT]  Monitor error: {e}", flush=True)


# ── PCM playback ──────────────────────────────────────────────────────────────

def play_pcm(pcm_bytes: bytes, pa, rate: int = 22050):
    """Play mono s16le PCM through the wm8960 headphone output (stereo-expanded)."""
    _stop_playback.clear()
    raw = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
    samples = np.clip(raw * 1.0, -32768, 32767).astype(np.int16)
    stereo = np.column_stack([samples, samples]).flatten().tobytes()
    interrupted = threading.Event()
    pos = [0]

    def callback(in_data, frame_count, time_info, status):
        if interrupted.is_set() or _stop_playback.is_set() or button_pressed():
            interrupted.set()
            return (b"\x00" * frame_count * 4, pyaudio.paComplete)
        chunk = stereo[pos[0]:pos[0] + frame_count * 4]
        pos[0] += frame_count * 4
        if len(chunk) < frame_count * 4:
            return (chunk + b"\x00" * (frame_count * 4 - len(chunk)), pyaudio.paComplete)
        return (chunk, pyaudio.paContinue)

    _int_stop = threading.Event()
    _int_thread = threading.Thread(
        target=_playback_interrupt_listener,
        args=(pa, _int_stop, interrupted),
        daemon=True,
    )
    _int_thread.start()

    stream = pa.open(format=pyaudio.paInt16, channels=2, rate=rate,
                     output=True, frames_per_buffer=512,
                     stream_callback=callback)
    stream.start_stream()
    while stream.is_active():
        time.sleep(0.02)
        if button_pressed() or _stop_playback.is_set():
            interrupted.set()
    stream.stop_stream()
    stream.close()

    _int_stop.set()
    _int_thread.join(timeout=1.0)

    was_interrupted = interrupted.is_set()
    if was_interrupted:
        print("[STOP] Playback interrupted", flush=True)
    _stop_playback.clear()
    return was_interrupted


def play_pcm_speaking(pcm_bytes: bytes, pa, teensy, restore_mouth_idx: int = 0,
                      rate: int = 22050) -> bool:
    """play_pcm with mouth animation. Cycles open/close bitmaps at 120 ms/frame.
    Returns True if playback was interrupted mid-stream."""
    _SPEAK_FRAMES = [0, 1, 5, 1]   # neutral → happy → surprised → happy
    stop_evt = threading.Event()

    def _animate():
        i = 0
        while not stop_evt.wait(0.12):
            teensy.send_command(f"MOUTH:{_SPEAK_FRAMES[i % len(_SPEAK_FRAMES)]}")
            i += 1
        teensy.send_command(f"MOUTH:{restore_mouth_idx}")

    t = threading.Thread(target=_animate, daemon=True)
    t.start()
    was_interrupted = play_pcm(pcm_bytes, pa, rate)
    stop_evt.set()
    t.join(timeout=1.0)
    return was_interrupted


# ── Beeps ─────────────────────────────────────────────────────────────────────

def play_beep(pa):
    rate = 44100
    t = np.linspace(0, 0.2, int(rate * 0.2), False)
    tone = (np.sin(2 * np.pi * 880 * t) * 6000).astype(np.int16)
    stereo = np.column_stack([tone, tone]).flatten()
    stream = pa.open(format=pyaudio.paInt16, channels=2, rate=rate, output=True)
    stream.write(stereo.tobytes())
    stream.stop_stream()
    stream.close()


def play_double_beep(pa):
    rate = 44100
    t = np.linspace(0, 0.12, int(rate * 0.12), False)
    tone = (np.sin(2 * np.pi * 660 * t) * 4000).astype(np.int16)
    gap = np.zeros(int(rate * 0.08), dtype=np.int16)
    sequence = np.concatenate([tone, gap, tone])
    stereo = np.column_stack([sequence, sequence]).flatten()
    stream = pa.open(format=pyaudio.paInt16, channels=2, rate=rate, output=True)
    stream.write(stereo.tobytes())
    stream.stop_stream()
    stream.close()


# ── Record ────────────────────────────────────────────────────────────────────

def record_command(mic, ptt_mode: bool = False, kids_mode: bool = False) -> bytes:
    """
    Record from mic until silence or max duration.
    kids_mode — when True uses KIDS_* thresholds from config.
    ptt_mode  — when True records until button released.
    Returns raw PCM bytes.
    """
    frames = []
    silence = 0
    rec_secs   = KIDS_RECORD_SECONDS if kids_mode else RECORD_SECONDS
    sil_secs   = KIDS_SILENCE_SECS   if kids_mode else SILENCE_SECS
    sil_rms    = KIDS_SILENCE_RMS    if kids_mode else SILENCE_RMS
    max_chunks = int(SAMPLE_RATE / CHUNK * rec_secs)
    sil_limit  = int(SAMPLE_RATE / CHUNK * sil_secs)
    for _ in range(max_chunks):
        f = mic.read(CHUNK, exception_on_overflow=False)
        frames.append(f)
        if ptt_mode:
            if not button_pressed():
                break
        else:
            rms = np.sqrt(np.mean(np.frombuffer(f, dtype=np.int16).astype(np.float32) ** 2))
            silence = silence + 1 if rms < sil_rms else 0
            if silence >= sil_limit:
                break
    return b"".join(frames)
