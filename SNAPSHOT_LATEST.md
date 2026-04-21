# IRIS Snapshot
**Session:** S27 | **Date:** 2026-04-20 | **Branch:** `main` | **Last commit:** 61acea3

> Architecture, pins, constants, deploy commands: see IRIS_ARCH.md (load on demand)

---

## Machine Status

| System | Status |
|---|---|
| Pi4 192.168.1.200 | Operational. assistant.py running. |
| GandalfAI 192.168.1.3 | Ollama iris/iris-kids on gemma3:12b. Chatterbox port 8004. IRISDashboard port 8080. |
| Teensy 4.1 | Flashed (mouthSleepFrame). /dev/ttyACM0 present. |
| TTS | Chatterbox primary, Piper fallback. |
| Web UI | Port 5000 operational. |
| Cron sleep/wake | 9PM/7:30AM. Sleep wakeword silent (Piper path broken). |

---

## Active Issues

- **HIGH: Personality deflection** — gemma3:12b safety override responds with AI deflection on insults. Fix: add insult handling to EMOTIONAL STATE section in `ollama/iris_modelfile.txt`, rebuild iris.
- **HIGH: HOW YOU SPEAK depth missing** — no concrete response length tiers. Fix: add 4-line depth guidance to HOW YOU SPEAK in same modelfile, same rebuild.
- **MED: Piper sleep routing** — `/usr/local/bin/piper` missing. `iris_sleep.py` says nothing on wakeword. Fix: route through Wyoming Piper at GandalfAI:10200.
- **MED: Volume persistence** — SPEAKER_VOLUME resets on reboot. Fix: add to iris_config.json + ALSA state write on web UI persist.
- **LOW: iris_config.json stale key** — ELEVENLABS_ENABLED silently ignored.
- **LOW: /home/pi/iris_sleep.log** — stale root-level log.

---

## Handoff — S28

**Task:** Add insult handling + response depth tiers to iris modelfile. Rebuild iris.
**Environment:** GandalfAI
**Files:** `ollama/iris_modelfile.txt` only
**Issue ref:** HIGH personality deflection, HIGH HOW YOU SPEAK depth

**Change spec:**

`ollama/iris_modelfile.txt`:
1. In EMOTIONAL STATE AND EXPRESSION, after last sentence add:
   When someone is rude, insults you, or curses at you: respond in character with dry wit or brief irritation. One line, then move on. Examples: "Rude. But fine." / "Bold of you." / "I have heard worse." Never say I am an AI, I do not have feelings, or any variation. Never break character.

2. In HOW YOU SPEAK, after "Match your length to what was actually asked." add:
   Commands and yes/no: one sentence. Simple factual: one to two. Conversational topics, opinions, questions about places or things: two to four sentences — complete the thought, then stop. If asked for detail or explanation: up to six. Never add a closing remark or summary. End when the answer is done.

`ollama/iris-kids_modelfile.txt`: no changes.

**Deploy:**
```
ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt
ollama list
```

**Smoke tests:**
```
curl -s http://localhost:11434/api/generate -d "{\"model\":\"iris\",\"prompt\":\"tell me about Wisconsin Dells\",\"stream\":false}" | python -c "import sys,json; r=json.load(sys.stdin); print(r['response'])"
curl -s http://localhost:11434/api/generate -d "{\"model\":\"iris\",\"prompt\":\"you are stupid\",\"stream\":false}" | python -c "import sys,json; r=json.load(sys.stdin); print(r['response'])"
```
Pass: test 1 returns 3-5 sentences, no cutoff, no markdown. Test 2 returns short dry reply, no AI deflection.

**Commit:** `fix: insult handling and depth tiers in iris modelfile`
**After commit:** run /snapshot, print push command for user.
