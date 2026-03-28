#!/usr/bin/env python3
# iris_sleep.py — Triggered by cron at 9:00 PM
# Sends EYES:SLEEP + MOUTH:8 via UDP to assistant.py (which owns the serial port).
import socket, subprocess, time

CMD_PORT = 10500

def log(msg):
    print(msg, flush=True)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(b'EYES:SLEEP\n', ('127.0.0.1', CMD_PORT))
        time.sleep(0.1)
        s.sendto(b'MOUTH:8\n', ('127.0.0.1', CMD_PORT))
    log('[SLEEP] UDP commands sent to assistant.py')
except Exception as e:
    log(f'[SLEEP] UDP error: {e}')

subprocess.run([
    'bash', '-c',
    'echo "Goodnight." | /usr/local/bin/piper --model /home/pi/piper/en_US-ryan-high.onnx '
    '--output_raw | aplay -r 22050 -f S16_LE -t raw -'
])
log('[SLEEP] Sleep mode activated')
