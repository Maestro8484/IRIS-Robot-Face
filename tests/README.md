# IRIS Pytest Stubs

These tests are repo-only checks for Pi4 Python modules. They are designed to
run on SuperMaster without IRIS hardware attached.

Run from the repo root:

```powershell
python -m pytest tests/ -v
```

The fixtures in `tests/conftest.py` mock serial, UDP, audio, ALSA subprocess,
and network paths. A failing test is acceptable when it identifies a real logic
gap for Claude Code review.
