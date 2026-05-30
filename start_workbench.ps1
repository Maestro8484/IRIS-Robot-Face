$root = $PSScriptRoot
$workbenchDir = Join-Path $root "tools\workbench"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$workbenchDir'; python -m http.server 8080"

Start-Sleep 1

$url = "http://localhost:8080"
$launched = $false
foreach ($browser in @("chrome.exe", "msedge.exe")) {
    try {
        Start-Process $browser $url
        $launched = $true
        break
    } catch { }
}
if (-not $launched) {
    Start-Process $url
}

Write-Host "IRIS Workbench running at http://localhost:8080"
Write-Host "Close the Python server window to stop"
