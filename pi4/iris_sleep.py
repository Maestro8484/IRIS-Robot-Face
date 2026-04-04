#!/usr/bin/env python3
# iris_sleep.py — Triggered by cron at 9:00 PM
# Sends EYES:SLEEP + MOUTH:8 via UDP to assistant.py (which owns the serial port).
import socket, subprocess, time, sys, os

# Ensure log directory exists, then redirect stdout+stderr for cron visibility
os.makedirs('/home/pi/logs', exist_ok=True)
sys.stdout = open('/home/pi/logs/iris_sleep.log', 'a', buffering=1)
sys.stderr = sys.stdout

sys.path.insert(0, '/home/pi')
from core.config import CMD_PORT

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

try:
    open('/tmp/iris_sleep_mode', 'w').close()
    log('[SLEEP] /tmp/iris_sleep_mode written')
except Exception as e:
    log(f'[SLEEP] Flag write error: {e}')

try:
    subprocess.run([
        'bash', '-c',
        'echo "Goodnight." | /usr/local/bin/piper'
        ' --model /home/pi/piper/en_US-ryan-high.onnx'
        ' --output_raw | aplay -r 22050 -f S16_LE -t raw -'
    ], timeout=15)
except Exception as e:
    log(f'[SLEEP] Piper TTS error (non-fatal): {e}')

log('[SLEEP] Sleep mode activated')
