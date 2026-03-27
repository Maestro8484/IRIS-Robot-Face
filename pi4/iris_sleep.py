#!/usr/bin/env python3
# iris_sleep.py — Triggered by cron at 9:00 PM
# Sets sleep flag, sends EYES:SLEEP + MOUTH:8 to Teensy, plays "Goodnight." TTS.
import serial, time, subprocess, os

TEENSY_PORT = '/dev/ttyACM0'
TEENSY_BAUD = 115200
LOG = '/var/log/iris_sleep.log'

def log(msg):
    print(msg, flush=True)

try:
    ser = serial.Serial(TEENSY_PORT, TEENSY_BAUD, timeout=2)
    time.sleep(0.5)
    ser.write(b'EYES:SLEEP\n')
    time.sleep(0.1)
    ser.write(b'MOUTH:8\n')
    ser.close()
    log('[SLEEP] Serial commands sent')
except Exception as e:
    log(f'[SLEEP] Serial error: {e}')

open('/tmp/iris_sleep_mode', 'w').close()
log('[SLEEP] Sleep flag created')

subprocess.run([
    'bash', '-c',
    'echo "Goodnight." | /usr/local/bin/piper --model /home/pi/piper/en_US-ryan-high.onnx '
    '--output_raw | aplay -r 22050 -f S16_LE -t raw -'
])
log('[SLEEP] Sleep mode activated')
