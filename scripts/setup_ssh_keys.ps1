<#
.SYNOPSIS
    One-time SSH key setup: SuperMaster -> Pi4.
    After this runs, flash_t41.ps1 and flash_t40.ps1 need zero password prompts.

.USAGE
    .\scripts\setup_ssh_keys.ps1
    Enter password "ohs" ONCE when prompted. Never again after that.
#>

$PI4     = "pi@192.168.1.200"
$keyPath = "$env:USERPROFILE\.ssh\id_ecdsa"

# ── 1. Generate key if needed ─────────────────────────────────────────────────
if (Test-Path "$keyPath.pub") {
    Write-Host "[KEY] Key already exists at $keyPath.pub -- skipping generation." -ForegroundColor Yellow
} else {
    Write-Host "[KEY] Generating ECDSA key (no passphrase)..." -ForegroundColor Cyan
    ssh-keygen -t ecdsa -b 256 -f $keyPath -N ""
    if ($LASTEXITCODE -ne 0) { Write-Host "[KEY] keygen FAILED." -ForegroundColor Red; exit 1 }
    Write-Host "[KEY] Key generated." -ForegroundColor Green
}

$pubkey = (Get-Content "$keyPath.pub" -Raw).Trim()

# ── 2. Install key on Pi4 — ONE password prompt ───────────────────────────────
Write-Host ""
Write-Host "[KEY] Installing public key on Pi4." -ForegroundColor Cyan
Write-Host "[KEY] Enter password: ohs" -ForegroundColor Yellow
Write-Host ""

$installCmd = "mkdir -p ~/.ssh && echo '$pubkey' >> ~/.ssh/authorized_keys && sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh && echo '[KEY] Key installed in RAM'"
ssh -o StrictHostKeyChecking=no $PI4 $installCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "[KEY] Install FAILED. Check Pi4 is reachable and password is correct." -ForegroundColor Red
    exit 1
}

# ── 3. Persist authorized_keys to SD (key auth now active — no password) ─────
Write-Host "[KEY] Persisting to SD card (survives reboot)..." -ForegroundColor Cyan
ssh -o StrictHostKeyChecking=no $PI4 @'
sudo mount -o remount,rw /media/root-ro
sudo mkdir -p /media/root-ro/home/pi/.ssh
sudo cp /home/pi/.ssh/authorized_keys /media/root-ro/home/pi/.ssh/authorized_keys
sudo chown -R pi:pi /media/root-ro/home/pi/.ssh
sudo chmod 700 /media/root-ro/home/pi/.ssh
sudo chmod 600 /media/root-ro/home/pi/.ssh/authorized_keys
sync
sudo mount -o remount,ro /media/root-ro
echo '[KEY] Persisted to SD OK'
'@

# ── 4. Verify ─────────────────────────────────────────────────────────────────
Write-Host "[KEY] Verifying passwordless connection..." -ForegroundColor Cyan
$result = ssh -o StrictHostKeyChecking=no -o PasswordAuthentication=no $PI4 "echo OK" 2>&1
if ($result -eq "OK") {
    Write-Host ""
    Write-Host "[KEY] SUCCESS. SSH key auth is working." -ForegroundColor Green
    Write-Host "[KEY] flash_t41.ps1 and flash_t40.ps1 will now run without password prompts." -ForegroundColor Green
} else {
    Write-Host "[KEY] Verification failed: $result" -ForegroundColor Red
    Write-Host "[KEY] Pi4 sshd may need PubkeyAuthentication enabled -- check /etc/ssh/sshd_config" -ForegroundColor Yellow
}
