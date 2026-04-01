# Git History Purge — Credential Removal

The ElevenLabs API key `sk_752184d377335347d38c185ba56a1bebe9deba4da50ce082`
and SSH passwords are still present in git history. This document covers how
to fully erase them.

**Recommendation:** Rotate the ElevenLabs key NOW at elevenlabs.io before
proceeding — assume it is compromised since it was public.

---

## Method: git-filter-repo (recommended)

### 1. Install git-filter-repo

```powershell
pip install git-filter-repo
```

### 2. Create a replacements file

Create `C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face\replacements.txt`:

```
sk_752184d377335347d38c185ba56a1bebe9deba4da50ce082==>ELEVENLABS_API_KEY_REDACTED
ohs==>SSH_PASSWORD_REDACTED
5309==>SSH_PASSWORD_REDACTED
```

### 3. Run the purge (rewrites ALL history)

```powershell
cd "C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face"
git filter-repo --replace-text replacements.txt --force
```

This rewrites every commit in every branch that contains any of those strings.

### 4. Re-add the remote (filter-repo removes it as a safety measure)

```powershell
git remote add origin https://github.com/Maestro8484/IRIS-Robot-Face.git
```

### 5. Force-push all branches

```powershell
git push origin --force --all
git push origin --force --tags
```

### 6. Clean up

Delete `replacements.txt` — it contains the live key text:
```powershell
Remove-Item replacements.txt
```

---

## After purging

- Any existing clones of the repo will have the old history. Ask collaborators
  to re-clone (not pull/rebase onto old history).
- GitHub may cache the old commits briefly — contact GitHub support to purge
  cached views if needed.
- Delete `replacements.txt` immediately after use.

---

## Pi4 — set the API key via environment

Since `assistant.py` now reads `os.environ.get("ELEVENLABS_API_KEY", "")`,
add the key to the Pi4's environment:

```bash
# On Pi4 (remember to persist to SD):
echo 'ELEVENLABS_API_KEY=your_new_key_here' | sudo tee -a /etc/environment
sudo mount -o remount,rw /media/root-ro
sudo cp /etc/environment /media/root-ro/etc/environment
sudo mount -o remount,ro /media/root-ro
```

Reboot or `source /etc/environment` + restart `assistant.service`.
