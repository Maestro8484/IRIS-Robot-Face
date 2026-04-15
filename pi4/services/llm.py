#!/usr/bin/env python3
"""
services/llm.py - LLM output helpers and streaming interface

extract_emotion_from_reply and clean_llm_reply are pure functions with no
external dependencies -- safe to import anywhere.

stream_ollama() streams sentence-boundary chunks from Ollama /api/chat.
ask_ollama() is retained in assistant.py for the followup loop and vision path.
"""

import json
import re

import requests

from core.config import VALID_EMOTIONS, EMOTION_TAG_RE, GANDALF, OLLAMA_PORT


def extract_emotion_from_reply(raw: str) -> tuple:
    """
    Parse [EMOTION:X] tag from the start of an LLM reply.
    Returns (emotion, cleaned_reply). Falls back to NEUTRAL if tag missing/invalid.
    """
    m = EMOTION_TAG_RE.match(raw)
    if m:
        emotion = m.group(1).upper()
        reply = raw[m.end():].strip()
        if emotion not in VALID_EMOTIONS:
            emotion = "NEUTRAL"
        return emotion, reply
    return "NEUTRAL", raw.strip()


def clean_llm_reply(text: str) -> str:
    """
    Strip markdown artifacts from LLM output.
    Does NOT strip the emotion tag -- call extract_emotion_from_reply first.
    """
    text = re.sub(r'[*_#`]', '', text)
    text = re.sub(r'^[-=]{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n+', ' ', text)
    openers = [
        r"^okay[,!.]?\s+here[''\u2019s]*\s+(a|is|one)[^.]*[.!]?\s*",
        r"^here[''\u2019s]*\s+(a|is|one)[^.]*[.!]?\s*",
        r"^sure[,!.]?\s*",
        r"^of course[,!.]?\s*",
        r"^alright[,!.]?\s*",
    ]
    for pat in openers:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)
    return text.strip()


def _split_sentences(text: str) -> list:
    """
    Split text on sentence boundaries (.!?) followed by whitespace or end of string.
    Minimum 8 chars per chunk to avoid splitting abbreviations like Dr. or U.S.
    Returns list of non-empty stripped strings.
    """
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    result = []
    carry = ""
    for part in parts:
        carry = (carry + " " + part).strip() if carry else part
        if len(carry) >= 8:
            result.append(carry)
            carry = ""
    if carry:
        result.append(carry)
    return [r for r in result if r.strip()]


def stream_ollama(messages: list, model: str, num_predict: int):
    """
    Stream sentence-boundary chunks from Ollama /api/chat with stream=True.

    Yields (chunk_text, emotion) tuples:
      - First yield: emotion is the extracted [EMOTION:X] value (or 'NEUTRAL' if absent).
      - Subsequent yields: emotion is None.
      - chunk_text is a clean spoken sentence ready for TTS.

    Caller assembles full reply from chunks for history and followup detection.
    Raises RuntimeError on connection or HTTP failure so caller can handle gracefully.
    """
    url = f"http://{GANDALF}:{OLLAMA_PORT}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"num_predict": num_predict},
    }

    emotion = "NEUTRAL"
    emotion_done = False
    first_yield = True
    buffer = ""

    try:
        with requests.post(url, json=payload, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                try:
                    data = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue

                token = data.get("message", {}).get("content", "")
                buffer += token

                # Extract emotion tag from buffered content as soon as possible
                if not emotion_done:
                    stripped = buffer.lstrip()
                    m = EMOTION_TAG_RE.match(stripped)
                    if m:
                        emotion = m.group(1).upper()
                        if emotion not in VALID_EMOTIONS:
                            emotion = "NEUTRAL"
                        buffer = stripped[m.end():]
                        emotion_done = True
                    elif len(buffer) > 40:
                        # No tag found after 40 chars -- assume NEUTRAL and proceed
                        emotion_done = True

                done = data.get("done", False)

                if done:
                    # Flush all remaining buffer as final chunks
                    parts = _split_sentences(buffer)
                    for p in parts:
                        cleaned = clean_llm_reply(p)
                        if cleaned:
                            out_emotion = emotion if first_yield else None
                            first_yield = False
                            yield cleaned, out_emotion
                    buffer = ""
                    break
                else:
                    # Yield complete sentences, hold last (may be incomplete)
                    parts = _split_sentences(buffer)
                    if len(parts) > 1:
                        for p in parts[:-1]:
                            cleaned = clean_llm_reply(p)
                            if cleaned:
                                out_emotion = emotion if first_yield else None
                                first_yield = False
                                yield cleaned, out_emotion
                        buffer = parts[-1]

    except Exception as e:
        raise RuntimeError(f"[LLM] stream_ollama failed: {e}") from e
