#!/bin/bash
# IRIS log export — runs every 15 min via /etc/cron.d/iris-logs
# Captures assistant.service journal for current boot to SD card.
# Keeps last 30 daily log files (~12 MB max at typical usage).
sudo mount -o remount,rw /media/root-ro
mkdir -p /media/root-ro/home/pi/logs
journalctl -u assistant.service --boot --output=short \
  > /media/root-ro/home/pi/logs/iris-$(date +%Y%m%d).log 2>/dev/null
ls -t /media/root-ro/home/pi/logs/iris-*.log 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null
sync
sudo mount -o remount,ro /media/root-ro
