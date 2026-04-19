# IRIS Mission Control Dashboard

Flask dashboard deployed on GandalfAI as a Windows service.
Accessible at http://192.168.1.3:8080 from any LAN browser.

## Files
- app.py — Flask server, serves dashboard UI and /api/status + /api/restart endpoints
- install_service.py — pywin32 Windows service wrapper

## Dependencies (already installed on GandalfAI)
- Python 3.14
- flask, paramiko, pywin32, requests

## Data sources
- GPU/VRAM: Prometheus at localhost:9090 (nvidia_smi_* metrics)
- Service status: port checks on localhost
- Pi4 logs + assistant status: paramiko SSH to 192.168.1.200 (pi/ohs, password auth)

## Service management
```
net stop IRISDashboard
net start IRISDashboard
Get-Service IRISDashboard
```

## Editing
Edit app.py directly on GandalfAI at C:\Users\gandalf\iris_dashboard\app.py, then restart the service.
For URL or string changes, use sftp_write (PowerShell mangles & in URLs).
