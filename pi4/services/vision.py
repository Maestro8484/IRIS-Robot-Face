"""
services/vision.py - Camera capture and vision inference
Captures still image via rpicam-still, sends to Ollama vision model on GandalfAI.
"""

import base64
import os
import re
import subprocess
import tempfile
import time

import requests

from core.config import (
    CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_TIMEOUT,
    GANDALF, OLLAMA_PORT, VISION_MODEL, VISION_TRIGGERS,
)
from services.llm import extract_emotion_from_reply


def capture_image() -> bytes | None:
    """Capture a JPEG from the Pi camera. Returns bytes or None on failure."""
    for attempt in range(1, 3):
        tmp = tempfile.mktemp(suffix='.jpg')
        try:
            result = subprocess.run(
                ['rpicam-still', '-o', tmp,
                 '--width', str(CAMERA_WIDTH),
                 '--height', str(CAMERA_HEIGHT),
                 '--nopreview', '--immediate',
                 '-t', str(CAMERA_TIMEOUT)],
                capture_output=True,
                timeout=CAMERA_TIMEOUT / 1000 + 5,
            )
            if result.returncode != 0:
                err = result.stderr.decode(errors='replace')
                lines = [
                    l for l in err.splitlines()
                    if ' ERROR ' in l or ' WARN ' in l or (l and not l.startswith('['))
                ]
                diag = ' | '.join(lines[:4]) if lines else err[-300:]
                print(f"[CAM]  Capture failed (attempt {attempt}): {diag}", flush=True)
                if attempt < 2:
                    time.sleep(0.8)
                    continue
                return None
            with open(tmp, 'rb') as f:
                data = f.read()
            print(f"[CAM]  Captured {len(data) // 1024}KB (attempt {attempt})", flush=True)
            return data
        except Exception as e:
            print(f"[CAM]  Exception (attempt {attempt}): {e}", flush=True)
            if attempt < 2:
                time.sleep(0.8)
                continue
            return None
        finally:
            try:
                os.unlink(tmp)
            except Exception:
                pass
    return None


def is_vision_trigger(text: str) -> bool:
    """Return True if the transcribed text matches a vision trigger phrase."""
    return any(trigger in text.lower().strip().rstrip(".!?") for trigger in VISION_TRIGGERS)


def ask_vision(image_bytes: bytes, prompt: str) -> str:
    """Send image + prompt to Ollama vision model. Returns plain text reply."""
    img_b64 = base64.b64encode(image_bytes).decode()
    vision_prompt = (
        f"Describe what you see in plain spoken sentences only. "
        f"No markdown, no lists, no preamble. 2-3 sentences max. "
        f"The user asked: {prompt}"
    )
    r = requests.post(
        f"http://{GANDALF}:{OLLAMA_PORT}/api/generate",
        json={
            "model": VISION_MODEL,
            "prompt": vision_prompt,
            "images": [img_b64],
            "stream": False,
        },
        timeout=90,
    )
    r.raise_for_status()
    data = r.json()
    reply = data.get("response", "") or data.get("message", {}).get("content", "")
    # Strip thinking blocks
    reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()
    # Strip emotion tag -- vision uses same jarvis model which emits [EMOTION:X]
    _, reply = extract_emotion_from_reply(reply)
    return reply or "I could not make out what I was looking at."
