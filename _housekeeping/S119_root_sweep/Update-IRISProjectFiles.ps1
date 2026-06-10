#Requires -Version 5
# Update-IRISProjectFiles.ps1
# Copies attachment-worthy IRIS project files to .\project-upload-staging\
# and prints a summary table with last-commit info for each file.

$RepoRoot = $PSScriptRoot
$Staging  = Join-Path $RepoRoot "project-upload-staging"

$Files = @(
    "SNAPSHOT_LATEST.md",
    "HANDOFF_CURRENT.md",
    "CLAUDE.md",
    "IRIS_ARCH.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "WORKFLOW_RULE.md",
    "AGENTS.md",
    "IRIS_CONFIG_MAP.md",
    "PRIMER.md",
    "README.md",
    "docs/iris_issue_log.md",
    "docs/MAESTRO_QUICKREF.md",
    "docs/intent-router.md",
    "docs/sysmap.json",
    "docs/servo_teensy40_wiring.md",
    "docs/guides/GUIDE-settings.md",
    "docs/guides/GUIDE-settings.docx"
)

# --- Prepare staging folder ---
if (Test-Path $Staging) {
    Remove-Item "$Staging\*" -Recurse -Force
} else {
    New-Item -ItemType Directory -Path $Staging | Out-Null
}

# --- Pre-scan for duplicate basenames so we can apply parent prefix ---
$basenameCounts = @{}
foreach ($rel in $Files) {
    $base = Split-Path ($rel -replace '/', '\') -Leaf
    $basenameCounts[$base] = ($basenameCounts[$base] -as [int]) + 1
}

# --- Process each file ---
$rows = @()

foreach ($rel in $Files) {
    $src  = Join-Path $RepoRoot ($rel -replace '/', '\')
    $base = Split-Path $src -Leaf

    # Prefix with immediate parent folder name when basename is not unique
    if ($basenameCounts[$base] -gt 1) {
        $parent  = Split-Path (Split-Path $src -Parent) -Leaf
        $destName = "${parent}_${base}"
    } else {
        $destName = $base
    }

    if (-not (Test-Path $src)) {
        $rows += [PSCustomObject]@{
            File       = $rel
            StagedAs   = $destName
            Date       = "MISSING"
            CommitHash = ""
            Message    = "(file not found in repo)"
        }
        continue
    }

    Copy-Item $src (Join-Path $Staging $destName) -Force

    $gitOut = & git -C $RepoRoot log -1 --format="%h %ad %s" --date=short -- $rel 2>$null
    if ($gitOut) {
        $hash    = ($gitOut -split ' ')[0]
        $date    = ($gitOut -split ' ')[1]
        $message = ($gitOut -split ' ', 3)[2]
    } else {
        $hash    = "untracked"
        $date    = "---"
        $message = "(no git history)"
    }

    $rows += [PSCustomObject]@{
        File       = $rel
        StagedAs   = $destName
        Date       = $date
        CommitHash = $hash
        Message    = $message
    }
}

# --- Print summary table ---
Write-Host ""
Write-Host "=== IRIS Project File Staging Summary ===" -ForegroundColor Cyan
Write-Host ""

$colFile = 42
$colDate = 12
$colHash = 9
$colMsg  = 55

$header  = "{0,-$colFile} {1,-$colDate} {2,-$colHash} {3}" -f "File", "Last Date", "Hash", "Commit Message"
$divider = "-" * ($colFile + $colDate + $colHash + $colMsg + 3)

Write-Host $header -ForegroundColor Yellow
Write-Host $divider

foreach ($r in $rows) {
    $color = if ($r.Date -eq "MISSING") { "Red" } else { "White" }
    $line  = "{0,-$colFile} {1,-$colDate} {2,-$colHash} {3}" -f `
        $r.File, $r.Date, $r.CommitHash, `
        ($r.Message.Substring(0, [Math]::Min($r.Message.Length, $colMsg)))
    Write-Host $line -ForegroundColor $color
}

Write-Host ""
$copied  = ($rows | Where-Object { $_.Date -ne "MISSING" }).Count
$missing = ($rows | Where-Object { $_.Date -eq "MISSING" }).Count
Write-Host "Copied: $copied   Missing/skipped: $missing" -ForegroundColor Cyan
Write-Host "Staging folder: $Staging" -ForegroundColor Cyan
Write-Host ""

# --- Open staging folder in Explorer ---
Start-Process explorer.exe $Staging
