"""
hardware/teensy_bridge.py - Teensy serial bridge
Single owner of /dev/ttyACM0. All serial I/O goes through this module.
All other callers must use UDP → 127.0.0.1:CMD_PORT.
"""
# TODO: move TeensyBridge class and _find_mic_device_index here from assistant.py
