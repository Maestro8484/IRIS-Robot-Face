"""
services/tts.py - Text-to-speech (ElevenLabs primary, Wyoming Piper fallback)
Returns raw s16le PCM bytes at 22050 Hz mono.

synthesize(text) → bytes   — public entry point, routes EL → Piper on failure
spoken_numbers(text) → str — pre-processes numeric tokens for natural TTS
"""

import json
import re
import socket

import numpy as np
import requests

from core.config import (
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL, ELEVENLABS_ENABLED,
    GANDALF, PIPER_PORT, PIPER_VOICE,
    SAMPLE_RATE, CHANNELS,
)
from services.wyoming import wy_send, read_line


# ── ElevenLabs ────────────────────────────────────────────────────────────────

def _synthesize_elevenlabs(text: str) -> bytes:
    """ElevenLabs TTS → raw s16le PCM at 22050 Hz. Returns MP3-decoded samples."""
    import miniaudio
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.85,
            "style": 0.15,
            "use_speaker_boost": True,
        },
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    mp3 = resp.content
    if len(mp3) < 100:
        raise RuntimeError(f"[EL] Response too short: {len(mp3)} bytes")

    decoded = miniaudio.decode(
        mp3,
        output_format=miniaudio.SampleFormat.SIGNED16,
        nchannels=1,
        sample_rate=22050,
    )
    raw = np.frombuffer(bytes(decoded.samples), dtype=np.int16).astype(np.float32)

    # ElevenLabs is mastered ~16 dB quieter than Piper (measured RMS ~2000 vs ~15000).
    # Normalise to target RMS; allow modest peak clipping (broadcast-style compression)
    # so perceived loudness matches Piper fallback voice.
    _EL_TARGET_RMS = 5500.0
    _rms = float(np.sqrt(np.mean(raw ** 2))) if raw.size else 0.0
    if _rms > 10.0:
        _peak_safe = 32700.0 / float(np.max(np.abs(raw)))
        _norm_gain = min(_EL_TARGET_RMS / _rms, _peak_safe * 2.5)
        raw = np.clip(raw * _norm_gain, -32768.0, 32767.0)
        print(f"[EL]   Norm gain={_norm_gain:.2f}x  RMS {_rms:.0f}→{np.sqrt(np.mean(raw**2)):.0f}",
              flush=True)

    # Pad 80 ms silence before/after to absorb PAM8403 pop/thump transient
    samples_padded = np.concatenate([
        np.zeros(int(22050 * 0.08), dtype=np.int16),
        raw.astype(np.int16),
        np.zeros(int(22050 * 0.08), dtype=np.int16),
    ])
    pcm = samples_padded.tobytes()
    print(f"[EL]   OK {len(mp3)}b MP3 → {len(pcm)}b PCM ({decoded.duration:.1f}s)", flush=True)
    return pcm


# ── Piper (Wyoming) ───────────────────────────────────────────────────────────

def _synthesize_piper(text: str) -> bytes:
    """Piper TTS fallback via Wyoming protocol on GandalfAI."""
    with socket.create_connection((GANDALF, PIPER_PORT), timeout=60) as s:
        wy_send(s, "synthesize", {"text": text, "voice": {"name": PIPER_VOICE}})
        s.settimeout(60)
        audio_chunks = []
        buf = b""
        while True:
            line, buf = read_line(s, buf)
            hdr = json.loads(line.decode())
            etype = hdr.get("type", "")
            dlen = hdr.get("data_length", 0)
            plen = hdr.get("payload_length", 0)
            while len(buf) < dlen + plen:
                buf += s.recv(8192)
            pcm = buf[dlen:dlen + plen]
            buf = buf[dlen + plen:]
            if etype == "audio-chunk" and pcm:
                audio_chunks.append(pcm)
            elif etype == "audio-stop":
                return b"".join(audio_chunks)
            elif etype == "error":
                raise RuntimeError(f"Piper error: {hdr}")


# ── Number normalisation ──────────────────────────────────────────────────────

def spoken_numbers(text: str) -> str:
    """Convert numeric tokens to spoken English before TTS (no inflect dependency)."""
    _ONES = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
        "seventeen", "eighteen", "nineteen",
    ]
    _TENS = ["", "", "twenty", "thirty", "forty", "fifty",
             "sixty", "seventy", "eighty", "ninety"]

    def _int_to_words(n: int) -> str:
        if n < 0:
            return "negative " + _int_to_words(-n)
        if n < 20:
            return _ONES[n]
        if n < 100:
            rest = (" " + _ONES[n % 10]) if n % 10 else ""
            return _TENS[n // 10] + rest
        if n < 1000:
            rest = (" " + _int_to_words(n % 100)) if n % 100 else ""
            return _ONES[n // 100] + " hundred" + rest
        return str(n)

    # Temperature: 50F / 50°F / 50ºF
    text = re.sub(r'(\d+)\s*[°º]?F\b',
                  lambda m: _int_to_words(int(m.group(1))) + " degrees", text)
    # Speed: 2mph / 2 mph
    text = re.sub(r'(\d+)\s*mph\b',
                  lambda m: _int_to_words(int(m.group(1))) + " miles per hour",
                  text, flags=re.IGNORECASE)
    # Percent: 46%
    text = re.sub(r'(\d+)\s*%',
                  lambda m: _int_to_words(int(m.group(1))) + " percent", text)
    # Bare integers ≤ 999
    text = re.sub(r'\b(\d+)\b',
                  lambda m: _int_to_words(int(m.group(1))) if int(m.group(1)) <= 999 else m.group(0),
                  text)
    return text


# ── Public entry point ────────────────────────────────────────────────────────

def synthesize(text: str) -> bytes:
    """ElevenLabs first; Piper fallback on any failure. Returns s16le PCM at 22050 Hz."""
    text = spoken_numbers(text)
    if ELEVENLABS_ENABLED:
        try:
            return _synthesize_elevenlabs(text)
        except Exception as e:
            print(f"[EL]   Failed: {e} -- falling back to Piper", flush=True)
    return _synthesize_piper(text)
