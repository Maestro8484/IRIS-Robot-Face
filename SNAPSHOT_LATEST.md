# IRIS Robot Face — Session Snapshot
**Date:** 2026-04-20
**Session:** S27
**Branch:** `main`
**Last commit:** 61acea3 — fix: track snapshots in git, remove from gitignore

> Architecture, pins, constants, cron, deploy commands: see [IRIS_ARCH.md](IRIS_ARCH.md)

---

## Machine Status

| System | Status |
|---|---|
| Pi4 (192.168.1.200) | Operational. assistant.py running. wyoming-satellite removed S26. |
| GandalfAI (192.168.1.3) | Ollama iris/iris-kids on gemma3:12b. Chatterbox port 8004. IRISDashboard v3 port 8080. |
| Teensy 4.1 | Firmware built clean S22B (mouthSleepFrame). Awaiting manual flash. |
| TTS | Chatterbox primary, Piper fallback. |
| Web UI | Port 5000. Sleep/wake routes operational. |
| Cron sleep/wake | 9PM sleep / 7:30AM wake. Hardened S15. |

---

## Active Issues

- **HIGH: IRIS personality deflection** — gemma3:12b safety training overrides system prompt on insults, responds with AI deflection. Fix: add explicit insult handling to HARD RULES in modelfile + rebuild iris on GandalfAI.
- **HIGH: HOW YOU SPEAK depth guidance missing** — modelfile has correct length philosophy but no concrete tiers. Add 4-line depth guidance to HOW YOU SPEAK, rebuild iris on GandalfAI. (Same Claude Code session as deflection fix.)
- **MED: Piper sleep/wake routing** — Piper missing at /usr/local/bin/piper. Sleep wakeword says nothing. Route through Wyoming Piper at GandalfAI:10200.
- **MED: Volume persistence** — SPEAKER_VOLUME not in iris_config.json. Web UI persist does not write ALSA state to SD. Volume resets on reboot.
- **MED: iris-kids asterisk** — gemma3 uses *word* emphasis. tts.py strips before TTS (cosmetic only).
- **MED: iris_config.json stale key** — ELEVENLABS_ENABLED still present, silently ignored.
- **LOW: /home/pi/iris_sleep.log** — stale root-level log from pre-S2.

---

## Last Session Changes (S27 — 2026-04-20)
**Task:** Snapshot correction, config fix, doc cleanup

- **NUM_PREDICT fixed:** iris_config.json updated from 120 → 200. Persisted to SD (md5 verified). Assistant restarted, [INFO] Ready. confirmed.
- **Teensy confirmed DONE:** /dev/ttyACM0 present, firmware flashed (mouthSleepFrame). Previously marked done by user but lost due to snapshots being gitignored until S26.
- **Mouth smoke test confirmed DONE:** MOUTH:0–8 sent via UDP 127.0.0.1:10500, pipeline confirmed. Previously marked done by user but lost.
- **SNAPSHOT_LATEST.md corrected:** Removed stale HIGH items (Teensy flash, mouth smoke test, truncation) that were already resolved.
- **IRIS_ARCH.md updated:** Active Issues table corrected, Ollama constants updated to reflect gemma3:12b and current num_predict/num_ctx values.
- **CLAUDE.md updated:** Added note on Claude Chat vs Claude Code tool scope and snapshot gitignore history.
- Snapshot gitignore history noted: all user-confirmed task completions prior to S26 were not persisted to git. Snapshot is now authoritative from S27 forward.

## Previous Session Changes (S26 — 2026-04-20)
**Task:** Repo hygiene + diagnosis
- Removed wyoming-satellite.service from Pi4 — crash-looping since March 25, never functional.
- Removed SNAPSHOT*.md from .gitignore — snapshots now tracked in git.
- Confirmed wakeword working, full pipeline fires.
- Git push rule established: SuperMaster Desktop only.

## S25 — 2026-04-20
**Task:** Dashboard v3 redesign + deploy
- `tools/iris_dashboard/app.py` — v3 dark-theme, live Status tab, VRAM bar, GPU stats, 15-line terminal, Force Sleep/Wake buttons.
- GandalfAI: deployed, service restarted.

---

## Known TODO (carry-forward)
- Fix personality deflection + add HOW YOU SPEAK depth tiers — modelfile edit + ollama rebuild GandalfAI (next Claude Code session, handoff below)
- Smoke test sleep animation: web UI Sleep -> verify BL breathes + sine + Z on mouth TFT
- Smoke test return-to-sleep: trigger wakeword after 9PM -> confirm returns to sleep after reply
- Piper standalone routing for iris_sleep.py through Wyoming Piper GandalfAI:10200
- Volume persistence: SPEAKER_VOLUME to iris_config.json + ALSA state write on web UI persist
- Chatterbox auto-start on GandalfAI boot (manual docker compose up -d after reboot)
- Exaggeration tuning: 0.45 starting point, tune after live voice test

---

## Handoff — S28

**Task:** Fix personality deflection + add HOW YOU SPEAK depth guidance to iris modelfile. Rebuild iris on GandalfAI.
**Environment:** GandalfAI
**Files:** `ollama/iris_modelfile.txt` only
**Issue ref:** Active Issues HIGH: personality deflection, HIGH: HOW YOU SPEAK depth guidance

**Change spec:**

`ollama/iris_modelfile.txt`:

1. In the EMOTIONAL STATE AND EXPRESSION section, append after the last sentence:
   When someone is rude, insults you, or curses at you: respond in character with dry wit or brief irritation. One line, then move on. Examples: "Rude. But fine." / "Bold of you." / "I have heard worse." Never say I am an AI, I do not have feelings, or any variation. Never break character.

2. In HOW YOU SPEAK, after the sentence "Match your length to what was actually asked.", add:
   Commands and yes/no: one sentence. Simple factual: one to two. Conversational topics, opinions, questions about places or things: two to four sentences — complete the thought, then stop. If asked for detail or explanation: up to six. Never add a closing remark or summary. End when the answer is done.

`ollama/iris-kids_modelfile.txt`: no changes needed.

**Deploy on GandalfAI:**
```
ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt
ollama list
```

**Smoke test:**
```
curl -s http://localhost:11434/api/generate -d "{\"model\":\"iris\",\"prompt\":\"tell me about Wisconsin Dells\",\"stream\":false}" | python -c "import sys,json; r=json.load(sys.stdin); print(r['response'])"
```
Confirm: [EMOTION:x] tag on line 1, 3-5 sentences, no markdown, not cut off mid-sentence.

Second test — insult handling:
```
curl -s http://localhost:11434/api/generate -d "{\"model\":\"iris\",\"prompt\":\"you are stupid\",\"stream\":false}" | python -c "import sys,json; r=json.load(sys.stdin); print(r['response'])"
```
Confirm: short dry response, no AI deflection (no "I am an AI" or "I don't have feelings").

**Commit:** "fix: add insult handling and depth guidance to iris modelfile"
**After commit:** Confirm with user before push. Run /snapshot.
