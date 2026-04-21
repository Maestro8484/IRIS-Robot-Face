# IRIS Robot Face — Session Snapshot
**Date:** 2026-04-20
**Session:** S26
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

- **HIGH: Teensy needs manual flash** — mouthSleepFrame + mouthSleepReset firmware built S22B, not yet flashed. Flash before verifying sleep animation.
- **HIGH: Mouth smoke test** — MOUTH:0-8 never confirmed post-installation. Do before any further firmware work.
- **HIGH: IRIS response truncation** — num_predict 120 cuts responses mid-sentence. Fix: raise to 200 in both modelfiles + rebuild iris/iris-kids on GandalfAI.
- **HIGH: IRIS personality deflection** — gemma3:12b safety training overrides system prompt on insults, responds with AI deflection. Fix: add explicit insult handling to HARD RULES in modelfile.
- **MED: Volume persistence** — SPEAKER_VOLUME not in iris_config.json. Web UI persist does not write ALSA state to SD. Volume resets on reboot.
- **MED: Piper sleep/wake routing** — Piper missing at /usr/local/bin/piper. Sleep wakeword says nothing. Route through Wyoming Piper at GandalfAI:10200.
- **MED: iris-kids asterisk** — gemma3 uses *word* emphasis. tts.py strips before TTS (cosmetic only).
- **MED: iris_config.json stale key** — ELEVENLABS_ENABLED still present, silently ignored.
- **LOW: /home/pi/iris_sleep.log** — stale root-level log from pre-S2.

---

## Last Session Changes (S26 — 2026-04-20)
**Task:** Repo hygiene + diagnosis

- Removed wyoming-satellite.service from Pi4 — crash-looping since March 25, never functional, not part of IRIS architecture.
- Removed SNAPSHOT*.md from .gitignore — snapshots now tracked in git.
- All snapshots force-added and pushed from SuperMaster.
- Confirmed wakeword working, full pipeline fires.
- Identified response truncation (num_predict 120) and personality deflection (gemma3:12b safety override) as active HIGH issues.
- Git push rule established: SuperMaster Desktop only.

## Previous Session Changes (S25 — 2026-04-20)
**Task:** Dashboard v3 redesign + deploy
- `tools/iris_dashboard/app.py` — v3 dark-theme, live Status tab, VRAM bar, GPU stats, 15-line terminal, Force Sleep/Wake buttons, /api/action/sleep + /api/action/wake routes.
- GandalfAI: deployed to C:\Users\gandalf\iris_dashboard\app.py, service restarted.

---

## Known TODO (carry-forward)
- Flash Teensy — firmware built S22B, user must click PlatformIO upload
- Fix truncation + personality — modelfile update + ollama rebuild on GandalfAI (handoff below)
- Smoke test mouth TFT: Pi4 SSH -> UDP 127.0.0.1:10500 -> MOUTH:0 through MOUTH:8
- Smoke test sleep animation: flash -> web UI Sleep -> verify BL breathes + sine + Z on TFT
- Smoke test return-to-sleep: trigger wakeword after 9PM -> confirm returns to sleep after reply
- Volume persistence: SPEAKER_VOLUME to iris_config.json + ALSA state write on web UI persist
- Piper standalone routing for iris_sleep.py through Wyoming Piper GandalfAI:10200
- Chatterbox auto-start on GandalfAI boot (manual docker compose up -d after reboot)
- Exaggeration tuning: 0.45 starting point, tune after live voice test

---

## Handoff — S27

**Task:** Fix IRIS response truncation and personality deflection via modelfile update and rebuild.
**Environment:** GandalfAI
**Files:** `ollama/iris_modelfile.txt`, `ollama/iris-kids_modelfile.txt`
**Issue ref:** Active Issues HIGH: truncation, HIGH: personality deflection

**Change spec:**

`ollama/iris_modelfile.txt`:
- PARAMETER num_predict 120 -> 200
- In HARD RULES, append: When someone insults you, curses at you, or is rude: respond as IRIS with dry wit or mild irritation. Never break character. A snarky one-liner is always correct. Examples: "Rude. But fine." / "Bold of you." / "I have heard worse." Never say I am an AI, I do not have feelings, or any variation.

`ollama/iris-kids_modelfile.txt`:
- PARAMETER num_predict 120 -> 200

**Deploy on GandalfAI:**
```
ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt
ollama create iris-kids -f C:\IRIS\IRIS-Robot-Face\ollama\iris-kids_modelfile.txt
ollama list
```

**Smoke test:**
```
curl -s http://localhost:11434/api/generate -d "{\"model\":\"iris\",\"prompt\":\"hello\",\"stream\":false}" | python -c "import sys,json; r=json.load(sys.stdin); print(r['response'])"
```
Confirm: [EMOTION:x] tag present, response not cut off mid-sentence, no markdown.

**Verify:** Multi-sentence question confirms full response. Insult confirms snarky in-character reply, not AI deflection.
**Commit:** "fix: raise num_predict to 200, add insult handling to IRIS modelfile"
**After commit:** Confirm with user before push. Run /snapshot.
