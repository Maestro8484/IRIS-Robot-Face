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
    _json_warn_fired = False

    try:
        with requests.post(url, json=payload, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                try:
                    data = json.loads(raw_line)
                except json.JSONDecodeError:
                    if not _json_warn_fired:
                        print("[LLM]  Malformed JSON line skipped (further skips suppressed)", flush=True)
                        _json_warn_fired = True
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


# ── Response length classifier ─────────────────────────────────────────────────

# Patterns that signal a short answer is sufficient
_SHORT_PATTERNS = (
    "what time", "what's the time", "what day", "what date",
    "how old", "who made", "who created", "what is your name", "what's your name",
    "are you", "can you", "do you", "did you", "will you",
    "yes or no", "true or false",
    "hello", "hi iris", "hey iris", "good morning", "good night", "good evening",
    "thank you", "thanks", "okay", "ok", "got it", "nevermind", "never mind",
    "stop", "pause", "quit", "restart",
    "turn on", "turn off", "set volume", "volume up", "volume down",
    "what's the weather", "what is the weather",
    "remind me", "set a timer", "set timer",
)

# Patterns that signal a long response is appropriate
_LONG_PATTERNS = (
    "explain", "explain to me", "explain how", "explain why", "explain what",
    "how does", "how do", "how would", "how should", "how can",
    "tell me about", "tell me everything", "tell me more",
    "what is the difference", "what's the difference", "compare",
    "walk me through", "walk me through it", "step by step", "step-by-step",
    "give me a list", "list of", "list the", "list all",
    "what are all the", "what are the different", "what are some",
    "write a", "write me a", "create a", "create me a",
    "make a list", "make me a",
    "story", "tell me a story", "tell a story",
    "recipe", "instructions for", "how to make", "how to build", "how to fix",
    "what are the steps", "what are the stages",
    "pros and cons", "advantages and disadvantages",
    "history of", "background on", "overview of",
    "describe", "describe the", "describe how",
    "what do you think about", "what do you think of",
    "give me your opinion", "give me advice",
    "debug", "troubleshoot", "diagnose",
    "brainstorm", "ideas for", "suggest some", "suggestions for",
    "in detail", "more detail", "more information", "more info",
    "elaborate", "expand on", "go deeper",
    "summary of", "summarize",
)

# Patterns that signal MAX tokens needed
_MAX_PATTERNS = (
    "everything about", "tell me everything", "complete guide",
    "comprehensive", "full explanation", "all you know",
    "write a long", "write me a long", "write a detailed",
    "essay", "full story", "long story",
    "all the steps", "all the details",
)


def classify_response_length(text: str,
                              short: int = None,
                              medium: int = None,
                              long: int = None,
                              max_val: int = None) -> int:
    """
    Examine a user utterance and return an appropriate num_predict value.

    Falls back to config constants if overrides not provided.
    Priority: MAX > LONG > SHORT > MEDIUM (default).
    """
    # Import lazily to avoid circular imports
    from core.config import (
        NUM_PREDICT_SHORT  as _S,
        NUM_PREDICT_MEDIUM as _M,
        NUM_PREDICT_LONG   as _L,
        NUM_PREDICT_MAX    as _X,
    )
    _short  = short   if short   is not None else _S
    _medium = medium  if medium  is not None else _M
    _long   = long    if long    is not None else _L
    _max    = max_val if max_val is not None else _X

    t = text.lower().strip().rstrip(".!?,;:")
    words = t.split()
    word_count = len(words)

    # MAX tier
    if any(p in t for p in _MAX_PATTERNS):
        return _max

    # LONG tier
    if any(p in t for p in _LONG_PATTERNS):
        # Scale within long tier by question complexity (word count proxy)
        if word_count > 15:
            return _max
        return _long

    # SHORT tier -- only if clearly a simple query
    if any(t.startswith(p) or t == p for p in _SHORT_PATTERNS):
        return _short

    # Heuristic: questions under 6 words with no complexity signals -> short
    if word_count <= 5 and t.endswith("?"):
        return _short

    # Heuristic: question word present and moderate length -> medium
    if any(t.startswith(qw) for qw in ("what", "who", "where", "when", "which")):
        if word_count <= 10:
            return _medium
        return _long

    # Default: medium
    return _medium
