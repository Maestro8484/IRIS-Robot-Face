# restore_chatterbox.ps1
# Restores Chatterbox TTS and removes Kokoro on GandalfAI.
# Run on GandalfAI: powershell -ExecutionPolicy Bypass -File C:\Users\gandalf\restore_chatterbox.ps1

$compose = "C:\IRIS\docker\docker-compose.yml"

Write-Host "[1/5] Stopping Kokoro container if running..." -ForegroundColor Cyan
docker stop kokoro-tts 2>$null
docker rm kokoro-tts 2>$null
Write-Host "    Done." -ForegroundColor Green

Write-Host "[2/5] Writing restored docker-compose.yml (whisper + piper + chatterbox)..." -ForegroundColor Cyan
$content = @'
name: iris

services:

  wyoming-whisper:
    image: lscr.io/linuxserver/faster-whisper:gpu
    container_name: wyoming-whisper
    restart: unless-stopped
    runtime: nvidia
    ports:
      - "10300:10300"
    volumes:
      - C:/IRIS/docker/whisper:/config
    environment:
      - TZ=America/Denver
      - WHISPER_MODEL=large-v3-turbo
      - WHISPER_LANG=en
      - WHISPER_BEAM=1
      - COMPUTE_TYPE=int8_float16
      - NVIDIA_VISIBLE_DEVICES=all

  wyoming-piper:
    image: rhasspy/wyoming-piper
    container_name: wyoming-piper
    restart: unless-stopped
    ports:
      - "10200:10200"
    volumes:
      - C:/IRIS/docker/piper/data:/data
    command:
      - --voice
      - en_US-lessac-medium
    environment:
      - TZ=America/Denver

  chatterbox:
    image: chatterbox-tts-server:cu128
    container_name: chatterbox-tts-server-cu128
    restart: unless-stopped
    runtime: nvidia
    ports:
      - "8004:8000"
    volumes:
      - C:/IRIS/chatterbox/model_cache:/app/model_cache
      - C:/IRIS/chatterbox/reference_audio:/app/reference_audio
      - C:/IRIS/chatterbox/outputs:/app/outputs
      - C:/IRIS/chatterbox/voices:/app/voices
      - C:/IRIS/chatterbox/logs:/app/logs
      - C:/IRIS/chatterbox/config.yaml:/app/config.yaml
      - C:/Users/gandalf/.cache/huggingface:/app/hf_cache
    environment:
      - TZ=America/Denver
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
      - HF_HOME=/app/hf_cache
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/ || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
              options:
                memory: 4g
'@
[System.IO.File]::WriteAllText($compose, $content, [System.Text.Encoding]::UTF8)
Write-Host "    Written." -ForegroundColor Green

Write-Host "[3/5] Starting chatterbox..." -ForegroundColor Cyan
docker compose -f $compose up -d chatterbox
Write-Host "    Started." -ForegroundColor Green

Write-Host "[4/5] Confirming wyoming-whisper and wyoming-piper still running..." -ForegroundColor Cyan
docker ps --filter name=wyoming-whisper --format "{{.Names}} {{.Status}}"
docker ps --filter name=wyoming-piper --format "{{.Names}} {{.Status}}"

Write-Host "[5/5] Chatterbox status:" -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep 2
    $status = docker ps --filter name=chatterbox-tts-server-cu128 --format "{{.Status}}" 2>$null
    if ($status -match "Up") {
        Write-Host "    Chatterbox is Up: $status" -ForegroundColor Green
        $ready = $true
        break
    }
}
if (-not $ready) {
    Write-Host "    Chatterbox did not start. Check: docker logs chatterbox-tts-server-cu128" -ForegroundColor Red
    exit 1
}
Write-Host "`nRollback complete. Chatterbox restored on port 8004." -ForegroundColor Green
Write-Host "Pi4 tts.py and config.py must be reverted manually via git:" -ForegroundColor Yellow
Write-Host "  git checkout HEAD -- pi4/services/tts.py pi4/core/config.py" -ForegroundColor Yellow
Write-Host "  Then deploy to Pi4 and restart assistant." -ForegroundColor Yellow
