# Handoff — RD-031: Eliminate log spam / unbounded disk writes  ⚠️ TOP PRIORITY

> **Recommended model: OPUS.** Rationale: this spans three layers (Teensy firmware + systemd/journald
> config + Pi4 bridge Python), the audit is open-ended ("find ANY other spam/unbounded writer"), and the
> stakes are high — a disk/space runout already crippled the Pi4 once (~late May 2026), and the fix
> touches **system-path files that must be SD-persisted individually** (the exact miss behind the S63
> 8-hour outage). Do NOT downgrade to Sonnet; this is judgment + deploy-discipline work, not a one-file edit.

## Why this exists (user directive, S130)

The Pi4 SD/overlay ran out of space ~3 weeks ago and crippled IRIS. User has made eliminating
excessive/spam data-generating activity **first-order priority**. Goal: remove every unbounded or
high-rate writer so space exhaustion cannot recur, and cap the ones that must keep writing.

## Session-start protocol (per CLAUDE.md — do this first)

1. `git status` — branch must be `main`, tree clean.
2. Read `CLAUDE.md`, `SNAPSHOT_LATEST.md` (Active Issues has the RD-031 summary), this file, and
   `ROADMAP.md` RD-031.
3. SSH Pi4 = password auth `pi`/`ohs` (key auth fails). Keep ssh calls < 10 s; split long ops.
4. **System-path persistence rule:** any file outside `/home/pi/` (e.g. `/etc/systemd/journald.conf`)
   must be copied to `/media/root-ro/<same path>` individually with md5 verified — the standard
   `/home/pi` deploy does NOT cover it. This is the S63 failure class.

## Quantified findings (live Pi4, S130 — 2026-06-12)

- Overlay root `/` (and `/media/root-rw`) = **1.9 GB**, ~69 MB used (4%). Lowerdir = SD `/media/root-ro`
  (ro), upperdir = tmpfs RAM. So most writes land in RAM; "disk full" presents as the overlay/tmpfs
  filling. `/var/log/journal` exists but `du`=0 → journal is effectively volatile/RAM here.
- **`[SR] frame=N`** (Teensy sleep-renderer debug print, relayed by bridge as `[EYES] << [SR] frame=…`)
  = **2610 / 5000** recent `assistant` lines (52%). Emitted continuously through the ~10 h nightly sleep.
- All **`[EYES]` serial echo** (`>>` sent / `<<` received) = **3017 / 5000** (60%). Combined with `[SR]`,
  ~**90%** of journal volume is routine serial traffic.
- **journald uncapped:** `/etc/systemd/journald.conf` has no `SystemMaxUse`/`RuntimeMaxUse` (defaults).
  `journalctl --disk-usage` ≈ 73.8 MB at time of audit.
- **`/home/pi/logs` = 48 MB** of daily `iris-YYYYMMDD.log` exports (19 MB on 2026-05-31, 7.7 MB, 6.1 MB…),
  unbounded, no retention. Source: `pi4/scripts/iris_log_export.sh` + `iris-logs.cron` (also
  `pi4/scripts/iris-logs.cron`).
- **`/home/pi/.cache/pip` ≈ 150 MB** stale wheels (`.cache/pip/http-v2/...body`).

## Fix plan — one small batch per target, verify + persist each, do NOT stack unverified

### 1. Firmware — kill the `[SR] frame=N` print  (REPO-ONLY → user flashes)
- Grep `\[SR\] frame` — it's a `Serial.print`/`println` in the sleep renderer (`src/sleep_renderer*.h`)
  or `src/main.cpp` sleep loop. Gate behind a compile-time `#ifdef DEBUG_SR` (default off) or delete.
- Bump `FIRMWARE_VERSION` in `src/config.h` (current live = **S130**) before building. `pio run -e eyes`
  to validate; firmware stays REPO-ONLY; user flashes via `scripts\flash_t41.ps1`.

### 2. Pi4 bridge — gate routine serial logging  (Pi4 deploy)  ← biggest systemic win
- `pi4/hardware/teensy_bridge.py`: the reader/writer log every serial line as `[EYES] >> …` / `[EYES] << …`.
  Add a debug gate (env var or config flag, default off) OR suppress routine frames: `[SR]`, `SLEEP_CFG:`,
  and repetitive `MOUTH:`/`MOUTH_INTENSITY:` echoes. Keep `[VER]`, `FACE:`, errors, and state changes.
- This is the root driver — even with #1 done, the bridge policy is what floods the journal.
- Deploy + md5 RAM=SD + restart `assistant` + verify.

### 3. journald size cap  (SYSTEM PATH — persist individually)
- Edit `/etc/systemd/journald.conf`: set `SystemMaxUse=50M` and `RuntimeMaxUse=50M` (tune to taste).
- Persist: remount-rw `/media/root-ro`, copy to `/media/root-ro/etc/systemd/journald.conf`, md5-verify,
  remount-ro. Then `sudo systemctl restart systemd-journald`; confirm `journalctl --disk-usage` drops/caps.
- Consider version-controlling a copy under `pi4/scripts/` like the cron reference.

### 4. Daily log-export retention  (Pi4 deploy)
- `pi4/scripts/iris_log_export.sh`: add pruning of `iris-*.log` older than N days (e.g. 7), or add a
  `logrotate` rule. Persist script; confirm cron unchanged (`pi4/scripts/iris_cron_reference.txt`).
- One-time: delete the existing backlog in `/home/pi/logs` beyond the retention window.

### 5. One-time pip cache prune
- `rm -rf /home/pi/.cache/pip/*` (≈150 MB). Optionally standardize on `pip --no-cache-dir`.

### 6. Audit pass
- Confirm SD vs RAM location of each writer; identify which path actually filled space in the May incident
  (daily exports are the prime suspect if `/home/pi/logs` is SD-backed). Sweep for any other append-only or
  high-rate file (`find / -xdev -size +20M`, check `/home/pi/logs`, bench JSONL growth, any service writing
  per-frame/per-loop).

## Verification (run after the batch)
- Idle/sleep ~10 min, then `journalctl -u assistant -n 5000 | grep -c '\[SR\] frame'` ≈ 0 and
  `[EYES]` share sharply reduced.
- `journalctl --disk-usage` stable/capped; `du -sh /home/pi/logs` bounded; `df -h` flat across a sleep cycle.

## Rollback
- Firmware: revert the print gate + `FIRMWARE_VERSION`, reflash prior build.
- Bridge/scripts: revert the file + redeploy + SD-persist + restart `assistant`.
- journald.conf: restore the backup to both RAM and `/media/root-ro/etc/systemd/`, restart `systemd-journald`.

## Status terminology reminder
Firmware is REPO-ONLY at session close (user flashes). Don't mark Pi4 changes DEPLOYED/VERIFIED without
md5 RAM=SD + a live check. Update CHANGELOG.md before closing.
