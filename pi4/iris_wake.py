#!/usr/bin/env python3
# iris_wake.py — Triggered by cron at 7:30 AM
# Clears sleep flag, sends EYES:WAKE + MOUTH:0 to Teensy.
import serial, time, os

TEENSY_PORT = '/dev/ttyACM0'
TEENSY_BAUD = 115200

def log(msg):
    print(msg, flush=True)

try:
    ser = serial.Serial(TEENSY_PORT, TEENSY_BAUD, timeout=2)
    time.sleep(0.5)
    ser.write(b'EYES:WAKE\n')
    time.sleep(0.1)
    ser.write(b'MOUTH:0\n')
    ser.close()
    log('[WAKE] Serial commands sent')
except Exception as e:
    log(f'[WAKE] Serial error: {e}')

try:
    os.remove('/tmp/iris_sleep_mode')
    log('[WAKE] Sleep flag cleared')
except FileNotFoundError:
    log('[WAKE] No sleep flag to clear')

log('[WAKE] Wake mode activated')
