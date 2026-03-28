"""
services/llm.py - LLM output helpers
extract_emotion_from_reply and clean_llm_reply are pure functions with no
external dependencies — safe to import anywhere.

ask_ollama() and conversation state remain in assistant.py until StateManager
is introduced (those functions depend on runtime globals).
"""

import re

from core.config import VALID_EMOTIONS, EMOTION_TAG_RE


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
    Does NOT strip the emotion tag — call extract_emotion_from_reply first.
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
