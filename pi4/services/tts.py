"""
services/tts.py - Text-to-speech (Chatterbox primary, ElevenLabs secondary, Wyoming Piper fallback)
Returns raw s16le PCM bytes at 48000 Hz mono.

synthesize(text) → bytes   — public entry point, routes CB → EL → Piper on failure
spoken_numbers(text) → str — pre-processes numeric tokens for natural TTS
"""

import json
import re
import socket

import numpy as np
import requests

from core.config import (
    CHATTERBOX_BASE_URL, CHATTERBOX_VOICE, CHATTERBOX_EXAGGERATION, CHATTERBOX_ENABLED,
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL, ELEVENLABS_ENABLED,
    GANDALF, PIPER_PORT, PIPER_VOICE,
    SAMPLE_RATE, CHANNELS,
)
from services.wyoming import wy_send, read_line


# ── Chatterbox TTS ────────────────────────────────────────────────────────────

def _cb_treble_boost(data: np.ndarray, sr: int) -> np.ndarray:
    """
    FFT-based high-shelf boost to compensate for Chatterbox Turbo's clone low-pass characteristic.
    Chatterbox clone output has ~95% energy below 2kHz; normal speech should peak around 2-4kHz.
    Applies a smooth +10dB shelf rising from ~1kHz to ~6kHz.
    """
    n = len(data)
    if n < 64:
        return data
    F = np.fft.rfft(data.astype(np.float64))
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    # tanh shelf: 0dB at low freqs, +10dB at high freqs, centred at 3kHz, width 2kHz
    gain_db = 10.0 * 0.5 * (1.0 + np.tanh((freqs - 3000.0) / 2000.0))
    gain_linear = 10.0 ** (gain_db / 20.0)
    boosted = np.fft.irfft(F * gain_linear, n)
    return np.clip(boosted, -32768.0, 32767.0)


def _synthesize_chatterbox(text: str) -> bytes:
    """Chatterbox-TTS-Server /tts endpoint, clone mode. Returns s16le PCM at 48000 Hz."""
    import miniaudio
    url = f"{CHATTERBOX_BASE_URL}/tts"
    payload = {
        "text": text,
        "voice_mode": "clone",
        "reference_audio_filename": CHATTERBOX_VOICE,
        "exaggeration": CHATTERBOX_EXAGGERATION,
        "output_format": "wav",
    }
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    wav_bytes = resp.content
    if len(wav_bytes) < 44:
        raise RuntimeError(f"[CB] Response too short: {len(wav_bytes)} bytes")
    decoded = miniaudio.decode(
        wav_bytes,
        output_format=miniaudio.SampleFormat.SIGNED16,
        nchannels=1,
        sample_rate=48000,
    )
    raw = np.frombuffer(bytes(decoded.samples), dtype=np.int16).astype(np.float32)
    boosted = _cb_treble_boost(raw, 48000).astype(np.int16)
    pcm = boosted.tobytes()
    print(f"[CB]   OK {len(wav_bytes)}b WAV → {len(pcm)}b PCM ({decoded.duration:.1f}s) [treble+10dB]", flush=True)
    return pcm


# ── ElevenLabs ────────────────────────────────────────────────────────────────

def _synthesize_elevenlabs(text: str) -> bytes:
    """ElevenLabs TTS → raw s16le PCM at 48000 Hz. Returns MP3-decoded samples."""
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
        sample_rate=48000,
    )
    raw = np.frombuffer(bytes(decoded.samples), dtype=np.int16).astype(np.float32)

    # ElevenLabs is mastered ~16 dB quieter than Piper (measured RMS ~2000 vs ~15000).
    _EL_TARGET_RMS = 5500.0
    _rms = float(np.sqrt(np.mean(raw ** 2))) if raw.size else 0.0
    if _rms > 10.0:
        _peak_safe = 32700.0 / float(np.max(np.abs(raw)))
        _norm_gain = min(_EL_TARGET_RMS / _rms, _peak_safe * 2.5)
        raw = np.clip(raw * _norm_gain, -32768.0, 32767.0)
        print(f"[EL]   Norm gain={_norm_gain:.2f}x  RMS {_rms:.0f}→{np.sqrt(np.mean(raw**2)):.0f}",
              flush=True)

    samples_padded = np.concatenate([
        np.zeros(int(48000 * 0.08), dtype=np.int16),
        raw.astype(np.int16),
        np.zeros(int(48000 * 0.08), dtype=np.int16),
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
                import miniaudio
                raw = b"".join(audio_chunks)
                return bytes(miniaudio.convert_frames(
                    miniaudio.SampleFormat.SIGNED16, 1, 22050, raw,
                    miniaudio.SampleFormat.SIGNED16, 1, 48000,
                ))
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

    text = re.sub(r'(\d+)\s*[°º]?F\b',
                  lambda m: _int_to_words(int(m.group(1))) + " degrees", text)
    text = re.sub(r'(\d+)\s*mph\b',
                  lambda m: _int_to_words(int(m.group(1))) + " miles per hour",
                  text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s*%',
                  lambda m: _int_to_words(int(m.group(1))) + " percent", text)
    text = re.sub(r'\b(\d+)\b',
                  lambda m: _int_to_words(int(m.group(1))) if int(m.group(1)) <= 999 else m.group(0),
                  text)
    return text


# ── Public entry point ────────────────────────────────────────────────────────

# Phrases that bypass Chatterbox and go directly to Piper (system state announcements)
_PIPER_DIRECT_PHRASES = {
    "good night",
    "goodnight",
    "good morning",
    "going to sleep",
    "waking up",
    "i am going to sleep now",
    "i'm going to sleep now",
}

def synthesize(text: str) -> bytes:
    """Chatterbox first; ElevenLabs second; Piper fallback. Returns s16le PCM at 48000 Hz.
    Sleep/wake phrases route directly to Piper regardless of CHATTERBOX_ENABLED.
    """
    text = spoken_numbers(text)
    # Strip markdown and speech markers that must never reach TTS
    text = re.sub(r'\*+', '', text)                          # bold/italic asterisks
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)      # _italic_ and __bold__
    text = re.sub(r'#+\s*', '', text)                        # headers
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)     # markdown links
    text = re.sub(r'`[^`]*`', '', text)                      # inline code
    text = re.sub(r'\[chuckle\]|\[laugh\]|\[sigh\]|\[gasp\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\x00-\x7F]+', ' ', text).strip()      # existing non-ASCII strip (keep)

    # Route sleep/wake system phrases directly to Piper - bypass Chatterbox
    _text_check = text.lower().strip().rstrip('.')
    if any(_text_check == p or _text_check.startswith(p) for p in _PIPER_DIRECT_PHRASES):
        print(f"[TTS]  Piper direct route (system phrase): '{text}'", flush=True)
        try:
            return _synthesize_piper(text)
        except Exception as e:
            print(f"[PIPER] Direct route failed: {e}", flush=True)

    if CHATTERBOX_ENABLED:
        try:
            return _synthesize_chatterbox(text)
        except Exception as e:
            print(f"[CB]   Failed: {e} -- falling back", flush=True)
    if ELEVENLABS_ENABLED:
        try:
            return _synthesize_elevenlabs(text)
        except Exception as e:
            print(f"[EL]   Failed: {e} -- falling back to Piper", flush=True)
    return _synthesize_piper(text)
