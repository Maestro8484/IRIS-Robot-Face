# IRIS Quick Reference — Personal Notes

## Component File Map
- LED animations: `pi4/hardware/led.py`
- Config storage: `pi4/iris_config.json`
- Web UI backend: `pi4/iris_web.py`
- Web UI frontend: `pi4/iris_web.html`
- Config docs: `IRIS_CONFIG_MAP.md`
- Intent routing: `pi4/core/intent_router.py`
- LLM calls: `pi4/services/llm.py`
- TTS: `pi4/services/tts.py`
- Sleep/wake: `pi4/assistant.py` (_do_sleep, _do_wake)
- Firmware: `src/main.cpp`

## Common Tasks → Files
- Change LED color/animation: `led.py`
- Add web UI control: `iris_web.py` + `iris_web.html`
- Add config setting: `iris_config.json` + `IRIS_CONFIG_MAP.md`
- Modify LLM persona: `ollama/iris_modelfile.txt` (then rebuild on GandalfAI)
- Add intent router layer: `intent_router.py`
- Fix wakeword: `assistant.py` (OWW config)
- Adjust emotion behavior: `config.py` (VALID_EMOTIONS), `led.py`, `src/main.cpp`

## Deploy Cheat Sheet
Pi4: `rsync -av --exclude='.git' C:/Users/SuperMaster/Documents/PlatformIO/IRIS-Robot-Face/pi4/ pi@192.168.1.200:/home/pi/`
Persist: `sudo mount -o remount,rw /media/root-ro && sudo cp [file] /media/root-ro/home/pi/[path] && sync && sudo mount -o remount,ro /media/root-ro`
Teensy flash: `pio run -t upload` (requires PROG button)
GandalfAI model: `ollama create iris -f C:\IRIS\IRIS-Robot-Face\ollama\iris_modelfile.txt`

## Prompts I Use
(paste irisFAST, other common prompts here)