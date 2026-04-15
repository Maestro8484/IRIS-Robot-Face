# IRIS Task B — LLM Streaming + Sentence-Chunked TTS
**Prepared:** 2026-04-15
**Depends on:** Task A complete (model swap done, mistral-small3.2:24b confirmed working)
**Machine:** GandalfAI (repo edits) + Pi4 (SSH deploy)

---

## PRE-FLIGHT (output before touching anything)

```
Branch:             main  (git branch --show-current MUST output "main")
Last commit:        [hash + message]
Working tree:       [must be clean — if dirty STOP]
Task this session:  Add stream_ollama() generator to llm.py; replace blocking LLM+TTS
                    block in assistant.py with streaming producer/consumer loop.
Files to modify:    pi4/services/llm.py
                    pi4/assistant.py
Files NOT touched:  pi4/services/tts.py, pi4/hardware/audio_io.py, pi4/core/config.py,
                    pi4/services/stt.py, pi4/services/wakeword.py, pi4/services/vision.py,
                    pi4/hardware/*, pi4/state/*, src/ (any firmware), iris_config.json,
                    alsa-init.sh, SNAPSHOT_LATEST.md (until /snapshot at session end)
Risk:               Mic stop timing — if _speaking_started gate misfires, mic stays open
                    during first TTS chunk and feeds back into recording. Check journal for
                    [REC] lines appearing during [TTS] chunk lines.
Rollback:           git revert HEAD, redeploy both files, systemctl restart assistant.
```

Do not proceed until user confirms.

---

## WHY

`ask_ollama()` uses `stream: False`. Full LLM generation completes before `synthesize()` is called.
120-token story = 15-25 second stall before first audio byte on maxed-VRAM card.
Streaming + sentence chunking targets first audio in 3-5 seconds.

---

## STEP 1 — Read both files from repo BEFORE any edits

```powershell
Get-Content C:\IRIS\IRIS-Robot-Face\pi4\services\llm.py
Get-Content C:\IRIS\IRIS-Robot-Face\pi4\assistant.py
```

Confirm content matches known state. Do NOT edit without reading first this session.

---

## STEP 2 — New `pi4/services/llm.py`

Write the FULL file (not a snippet). Preserve all existing functions:
`extract_emotion_from_reply`, `clean_llm_reply`, `ask_ollama`.
Add new functions: `_split_sentences` (internal helper) and `stream_ollama` (generator).

Key requirements for `stream_ollama`:
- `stream: True` in payload
- Extracts `[EMOTION:X]` tag from the first ~40 chars of buffered tokens
- Yields `(chunk_text, emotion)` tuples — emotion is set on first yield only, None on rest
- Flushes complete sentences from buffer as tokens arrive (split on `.!?` + whitespace)
- Flushes remainder on `done: True`
- Raises `RuntimeError` on exception so caller can fall back to `ask_ollama`

```python
def _split_sentences(text: str) -> list:
    """
    Split on sentence boundaries (.!?) followed by whitespace or end.
    Minimum 8 chars per chunk to avoid splitting abbreviations like 'Dr.' or 'U.S.'.
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
                        emotion_done = True
                done = data.get("done", False)
                parts = _split_sentences(buffer)
                if done:
                    for p in parts:
                        cleaned = clean_llm_reply(p)
                        if cleaned:
                            out_emotion = emotion if first_yield else None
                            first_yield = False
                            yield cleaned, out_emotion
                    buffer = ""
                    break
                elif len(parts) > 1:
                    for p in parts[:-1]:
                        cleaned = clean_llm_reply(p)
                        if cleaned:
                            out_emotion = emotion if first_yield else None
                            first_yield = False
                            yield cleaned, out_emotion
                    buffer = parts[-1]
    except Exception as e:
        raise RuntimeError(f"[LLM] stream_ollama failed: {e}") from e
```

---

## STEP 3 — Changes to `pi4/assistant.py`

**Read the full file first.** Make TWO targeted changes only.

### Change 1 — Import

Add `stream_ollama` to the existing llm import line:
```python
from services.llm import extract_emotion_from_reply, clean_llm_reply, stream_ollama
```

### Change 2 — Add `_build_messages()` helper

Read the current `ask_ollama()` to understand how it builds messages (date inject, person context).
Add `_build_messages()` as a standalone function near `ask_ollama()`:

```python
def _build_messages() -> list:
    import datetime
    now = datetime.datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")
    date_inject = {"role": "system", "content": f"Today is {date_str}."}
    _pname = state.person_context.get("name")
    if _pname and _pname in PERSON_SYSTEM_LINES:
        person_inject = {"role": "system", "content": PERSON_SYSTEM_LINES[_pname]}
        return [date_inject, person_inject] + list(state.conversation_history)
    return [date_inject] + list(state.conversation_history)
```

Note: verify `PERSON_SYSTEM_LINES` exists in current assistant.py before adding this. If it
doesn't exist, simplify to just date inject + conversation history.

### Change 3 — Replace the blocking LLM+TTS block

Find the block that calls `ask_ollama(text)` and then `synthesize(reply)` in sequence.
It looks roughly like:

```python
            print(f"[LLM]  Thinking... (model={get_model()})", flush=True)
            try: reply, emotion = ask_ollama(text)
            except Exception as e: ...
            emit_emotion(teensy, leds, emotion)
            try: pcm_data = synthesize(reply)
            except Exception as e: ...
            leds.show_speaking(); mic.stop_stream()
            _interrupted = play_pcm_speaking(pcm_data, pa, teensy)
```

IMPORTANT: Before replacing, confirm the user turn has been added to `state.conversation_history`
BEFORE this block (not inside `ask_ollama`). If `ask_ollama` appends the user turn internally,
move that append before the streaming block.

Replace with:

```python
            print(f"[LLM]  Streaming... (model={get_model()})", flush=True)
            reply_parts = []
            _interrupted = False
            _speaking_started = False
            _emotion_set = False
            try:
                for chunk, chunk_emotion in stream_ollama(
                    _build_messages(), get_model(), NUM_PREDICT
                ):
                    if chunk_emotion is not None and not _emotion_set:
                        emit_emotion(teensy, leds, chunk_emotion)
                        _emotion_set = True
                    reply_parts.append(chunk)
                    print(f"[TTS]  chunk: '{chunk}'", flush=True)
                    try:
                        pcm_data = synthesize(chunk)
                    except Exception as e:
                        print(f"[ERR]  TTS chunk: {e}", flush=True)
                        continue
                    if not _speaking_started:
                        leds.show_speaking()
                        mic.stop_stream()
                        _speaking_started = True
                    _interrupted = play_pcm_speaking(pcm_data, pa, teensy)
                    if _interrupted:
                        print("[STOP] Interrupted mid-stream", flush=True)
                        break
            except Exception as e:
                print(f"[ERR]  LLM stream: {e}", flush=True)
                leds.show_error(); time.sleep(1)
                if _speaking_started:
                    mic.start_stream()
                show_idle_for_mode(leds); continue

            if not _emotion_set:
                emit_emotion(teensy, leds, "NEUTRAL")
            if not _speaking_started:
                mic.stop_stream()

            reply = " ".join(reply_parts).strip()
            print(f"[LLM]  full: '{reply}'", flush=True)

            if button_pressed(): time.sleep(0.4)
```

Note: `NUM_PREDICT` — verify this constant exists in the current file. If not, use the numeric
value from `core/config.py`.

---

## STEP 4 — Deploy to Pi4

```bash
# Write to Pi4 RAM
sshpass -p 'ohs' scp pi4/services/llm.py pi@192.168.1.200:/home/pi/services/llm.py
sshpass -p 'ohs' scp pi4/assistant.py pi@192.168.1.200:/home/pi/assistant.py

# Persist both to SD
sshpass -p 'ohs' ssh pi@192.168.1.200 "
  sudo mount -o remount,rw /media/root-ro &&
  sudo cp /home/pi/services/llm.py /media/root-ro/home/pi/services/llm.py &&
  sudo cp /home/pi/assistant.py /media/root-ro/home/pi/assistant.py &&
  sudo mount -o remount,ro /media/root-ro"

# Verify md5
sshpass -p 'ohs' ssh pi@192.168.1.200 "
  md5sum /home/pi/services/llm.py /media/root-ro/home/pi/services/llm.py &&
  md5sum /home/pi/assistant.py /media/root-ro/home/pi/assistant.py"

# Restart and confirm
sshpass -p 'ohs' ssh pi@192.168.1.200 "
  sudo systemctl restart assistant &&
  sleep 3 &&
  journalctl -u assistant -n 30 --no-pager"
```

Confirm `[INFO] Ready.` in journal before closing.

---

## STEP 5 — Live test

Say "tell me a story."
- First audio should arrive within 4 seconds
- Watch journal: `[TTS] chunk:` lines should appear before full reply completes
- If `[REC]` lines appear during `[TTS]` chunk output → mic stop timing bug, re-check
  `_speaking_started` gate logic

---

## SESSION END

1. State: what changed, what did NOT change, any mic/timing issues observed.

2. Commit and push (user confirmation required before push):
```bash
git add -A
git commit -m "feat: S17 Task B — LLM streaming + sentence-chunked TTS"
git push origin main
```

3. Run `/snapshot`. Update Section 14 — CHANGES THIS SESSION with Task B outcome.
   Update Section 15 — PENDING HIGH if mic feedback issue observed.
