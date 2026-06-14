<#
.SYNOPSIS
    Flash the LEGACY Teensy 4.1 (eyes+mouth) firmware built from the May-23 (S62b,
    commit d6c33c6) snapshot — a T4.1-quiet-period reference build for bisecting
    "sensor not detected / no tracking" hardware-vs-firmware.

    This is a DETOUR / DIAGNOSTIC build. It is NOT the production firmware.

.USAGE
    From project root:
        .\scripts\flash_t41_legacy.ps1
    Rebuild the legacy hex in the worktree first, then flash:
        .\scripts\flash_t41_legacy.ps1 -Rebuild

.NOTES
    Source lives in an isolated git worktree so the current working tree is untouched:
        C:\Users\SuperMaster\Documents\PlatformIO\iris-legacy-S62b
    Same Pi4 / udev (/dev/ttyIRIS_EYES) / serial path as flash_t41.ps1 — fully linked
    to the current live system.

    CAVEATS of this legacy build (know before you read the journal):
      * NO [VER] line — versioning was added after May 23. Judge the flash by the
        "[DBG] Person Sensor detected" / "No Person Sensor found" and "FACE:" lines,
        NOT by a firmware= string.
      * Pre-S91 sensor probe (no 1500 ms boot guard) — a genuinely different detection
        path, which is the point of this datapoint.
      * Older eye-index map (pre-strikingBlue) — web UI EYE:n may map to different eyes.

    To return to normal firmware, just use .\scripts\flash_t41.ps1 again.
#>

param([switch]$Rebuild)

$PI4      = "pi@192.168.1.200"
$root     = Split-Path -Parent $PSScriptRoot
$WT       = "C:\Users\SuperMaster\Documents\PlatformIO\iris-legacy-S62b"
$hexLocal = Join-Path $WT ".pio\build\eyes\firmware.hex"
$hexPi4   = "/tmp/eyes.hex"

Set-Location $root

Write-Host "==================================================================" -ForegroundColor Magenta
Write-Host " LEGACY FLASH — May-23 S62b (d6c33c6) DIAGNOSTIC build" -ForegroundColor Magenta
Write-Host " No [VER] line expected. Watch for Person Sensor + FACE: lines." -ForegroundColor Magenta
Write-Host "==================================================================" -ForegroundColor Magenta

# 1 — (optional) rebuild the legacy hex in the isolated worktree
if ($Rebuild) {
    Write-Host "[T41-LEGACY] Rebuilding env:eyes in worktree..." -ForegroundColor Cyan
    pio run -e eyes -d $WT
    if ($LASTEXITCODE -ne 0) { Write-Host "[T41-LEGACY] Build FAILED." -ForegroundColor Red; exit 1 }
}

if (-not (Test-Path $hexLocal)) {
    Write-Host "[T41-LEGACY] Hex not found: $hexLocal  (run with -Rebuild)" -ForegroundColor Red
    exit 1
}

# 2 — Copy hex to Pi4
Write-Host "[T41-LEGACY] Copying legacy hex to Pi4..." -ForegroundColor Cyan
scp -o StrictHostKeyChecking=no $hexLocal "${PI4}:${hexPi4}"
if ($LASTEXITCODE -ne 0) { Write-Host "[T41-LEGACY] scp FAILED." -ForegroundColor Red; exit 1 }

# 3 — Flash via Pi4 (identical mechanism to flash_t41.ps1: explicit ttyIRIS_EYES reset)
Write-Host "[T41-LEGACY] Flashing via Pi4 (/dev/ttyIRIS_EYES reset -> upload -> restart)..." -ForegroundColor Cyan
ssh -o StrictHostKeyChecking=no $PI4 @"
sudo systemctl stop assistant && \
sleep 1 && \
printf 'import serial,time\ns=serial.Serial(\042/dev/ttyIRIS_EYES\042,134)\ntime.sleep(0.5)\ns.close()\n' | python3 && \
sleep 2 && \
sudo teensy_loader_cli --mcu=TEENSY41 -w -v $hexPi4 && \
sudo systemctl start assistant && \
echo '[T41-LEGACY] Flash complete. Verifying...' && \
sleep 4 && \
journalctl -u assistant -n 12 --no-pager | grep -E 'Person|FACE|Ready|ERROR' || true
"@

if ($LASTEXITCODE -eq 0) {
    Write-Host "[T41-LEGACY] Done. No [VER] is expected. Check Person Sensor + FACE: lines above." -ForegroundColor Green
} else {
    Write-Host "[T41-LEGACY] Flash may have failed -- check Pi4 journal." -ForegroundColor Yellow
}
