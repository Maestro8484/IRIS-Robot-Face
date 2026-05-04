# iris-git-helper.ps1
# IRIS Project Git Helper
# Purpose:
#   Simple PowerShell menu for checking status, committing, pushing, and reviewing git state
#   for the IRIS-Robot-Face project.
#
# Safe defaults:
#   - Does not auto-add everything without asking.
#   - Does not push without asking.
#   - Shows status before and after actions.
#   - Assumes repo path:
#       C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face

$ErrorActionPreference = "Stop"

# =========================
# CONFIG
# =========================

$RepoPath = "C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face"
$ExpectedBranch = "main"

# =========================
# HELPERS
# =========================

function Write-Header {
    param([string]$Text)

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host " $Text" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
}

function Write-Warn {
    param([string]$Text)
    Write-Host "WARNING: $Text" -ForegroundColor Yellow
}

function Write-Good {
    param([string]$Text)
    Write-Host "OK: $Text" -ForegroundColor Green
}

function Write-Bad {
    param([string]$Text)
    Write-Host "ERROR: $Text" -ForegroundColor Red
}

function Pause-IRIS {
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Confirm-YesNo {
    param([string]$Prompt)

    $answer = Read-Host "$Prompt [y/N]"
    return ($answer -eq "y" -or $answer -eq "Y")
}

function Ensure-GitAvailable {
    try {
        git --version | Out-Null
    }
    catch {
        Write-Bad "Git is not available in this PowerShell session."
        Write-Host "Install Git for Windows or reopen PowerShell after Git is installed."
        exit 1
    }
}

function Ensure-RepoPath {
    if (-not (Test-Path $RepoPath)) {
        Write-Bad "Repo path not found:"
        Write-Host $RepoPath
        exit 1
    }

    Set-Location $RepoPath

    if (-not (Test-Path ".git")) {
        Write-Bad "This folder does not appear to be a Git repository:"
        Write-Host $RepoPath
        exit 1
    }
}

function Get-CurrentBranch {
    return (git branch --show-current).Trim()
}

function Show-RepoSummary {
    Write-Header "IRIS Git Summary"

    Write-Host "Repo:   $RepoPath"
    Write-Host "Branch: $(Get-CurrentBranch)"
    Write-Host ""

    Write-Host "Last 3 commits:"
    git log --oneline -3

    Write-Host ""
    Write-Host "Status:"
    git status --short
}

function Check-Branch {
    $branch = Get-CurrentBranch

    if ($branch -ne $ExpectedBranch) {
        Write-Warn "You are on branch '$branch', expected '$ExpectedBranch'."
        Write-Warn "Do not commit/push unless this is intentional."
        return $false
    }

    Write-Good "On expected branch: $ExpectedBranch"
    return $true
}

function Show-FullStatus {
    Write-Header "Git Status"
    git status
}

function Show-ShortStatus {
    Write-Header "Git Short Status"
    git status --short
}

function Show-RecentCommits {
    Write-Header "Recent Commits"
    git log --oneline -10
}

function Show-Diff {
    Write-Header "Unstaged Diff"
    git diff

    Write-Header "Staged Diff"
    git diff --cached
}

function Stage-SelectedFiles {
    Write-Header "Stage Selected Files"

    git status --short

    Write-Host ""
    Write-Host "Enter file paths to stage, separated by commas."
    Write-Host "Example:"
    Write-Host "docs/S48_session_close.md, HANDOFF_CURRENT.md"
    Write-Host ""
    Write-Warn "Avoid 'git add .' unless you truly mean to stage everything."

    $inputFiles = Read-Host "Files to stage"

    if ([string]::IsNullOrWhiteSpace($inputFiles)) {
        Write-Warn "No files entered. Nothing staged."
        return
    }

    $files = $inputFiles.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }

    foreach ($file in $files) {
        if (Test-Path $file) {
            git add -- "$file"
            Write-Good "Staged: $file"
        }
        else {
            Write-Warn "File not found, skipped: $file"
        }
    }

    Show-ShortStatus
}

function Stage-AllFiles {
    Write-Header "Stage All Files"

    Write-Warn "This will stage ALL tracked, modified, deleted, and untracked files."
    Write-Warn "For IRIS, selected staging is usually safer."

    if (Confirm-YesNo "Stage everything with git add -A?") {
        git add -A
        Write-Good "All changes staged."
    }
    else {
        Write-Warn "Cancelled."
    }

    Show-ShortStatus
}

function Unstage-AllFiles {
    Write-Header "Unstage All Files"

    if (Confirm-YesNo "Unstage all currently staged files?") {
        git restore --staged .
        Write-Good "All files unstaged."
    }
    else {
        Write-Warn "Cancelled."
    }

    Show-ShortStatus
}

function Commit-StagedFiles {
    Write-Header "Commit Staged Files"

    $staged = git diff --cached --name-only

    if ([string]::IsNullOrWhiteSpace($staged)) {
        Write-Warn "No staged files found. Nothing to commit."
        return
    }

    Write-Host "Staged files:"
    git diff --cached --name-status

    Write-Host ""
    $message = Read-Host "Commit message"

    if ([string]::IsNullOrWhiteSpace($message)) {
        Write-Warn "Empty commit message. Cancelled."
        return
    }

    if (Confirm-YesNo "Commit staged files with message: '$message'?") {
        git commit -m "$message"
        Write-Good "Commit created."
    }
    else {
        Write-Warn "Commit cancelled."
    }

    Show-RepoSummary
}

function Commit-OnlyFile {
    Write-Header "Commit One File Only"

    git status --short

    Write-Host ""
    $file = Read-Host "Enter exact file path to commit only"
    if ([string]::IsNullOrWhiteSpace($file)) {
        Write-Warn "No file entered. Cancelled."
        return
    }

    if (-not (Test-Path $file)) {
        Write-Bad "File not found: $file"
        return
    }

    $message = Read-Host "Commit message"
    if ([string]::IsNullOrWhiteSpace($message)) {
        Write-Warn "Empty commit message. Cancelled."
        return
    }

    Write-Host ""
    Write-Warn "This uses: git commit --only <file> -m <message>"
    Write-Warn "It commits only the selected file, even if other files are staged."

    if (Confirm-YesNo "Commit only '$file'?") {
        git commit --only "$file" -m "$message"
        Write-Good "Commit created for only: $file"
    }
    else {
        Write-Warn "Commit cancelled."
    }

    Show-RepoSummary
}

function Push-OriginMain {
    Write-Header "Push to GitHub"

    $branch = Get-CurrentBranch

    if ($branch -ne $ExpectedBranch) {
        Write-Warn "Current branch is '$branch', expected '$ExpectedBranch'."
        if (-not (Confirm-YesNo "Push anyway?")) {
            Write-Warn "Push cancelled."
            return
        }
    }

    Write-Host "This will run:"
    Write-Host "git push origin $branch" -ForegroundColor Yellow
    Write-Host ""

    if (Confirm-YesNo "Push current branch to origin?") {
        git push origin $branch
        Write-Good "Push complete."
    }
    else {
        Write-Warn "Push cancelled."
    }

    Show-RepoSummary
}

function Pull-OriginMain {
    Write-Header "Pull Latest From GitHub"

    $branch = Get-CurrentBranch

    Write-Warn "Only pull if you are sure you want to update local files from GitHub."

    if (Confirm-YesNo "Run git pull origin $branch?") {
        git pull origin $branch
        Write-Good "Pull complete."
    }
    else {
        Write-Warn "Pull cancelled."
    }

    Show-RepoSummary
}

function Run-SafeCheck {
    Write-Header "IRIS Safe Git Check"

    Ensure-GitAvailable
    Ensure-RepoPath

    Check-Branch | Out-Null

    Write-Host ""
    Write-Host "Remote:"
    git remote -v

    Write-Host ""
    Write-Host "Branch tracking:"
    git branch -vv

    Write-Host ""
    Write-Host "Status:"
    git status

    Write-Host ""
    Write-Host "Last 5 commits:"
    git log --oneline -5
}

function Show-Menu {
    Clear-Host

    Write-Host "IRIS Git Helper" -ForegroundColor Cyan
    Write-Host "Repo: $RepoPath"
    Write-Host "Branch: $(Get-CurrentBranch)"
    Write-Host ""

    Write-Host "1.  Show full git status"
    Write-Host "2.  Show short git status"
    Write-Host "3.  Show recent commits"
    Write-Host "4.  Show diffs"
    Write-Host "5.  Stage selected files"
    Write-Host "6.  Stage all files"
    Write-Host "7.  Unstage all files"
    Write-Host "8.  Commit staged files"
    Write-Host "9.  Commit one file only"
    Write-Host "10. Push current branch to GitHub"
    Write-Host "11. Pull latest from GitHub"
    Write-Host "12. Safe repo check"
    Write-Host "13. Show summary"
    Write-Host "0.  Exit"
    Write-Host ""
}

# =========================
# MAIN
# =========================

Ensure-GitAvailable
Ensure-RepoPath

while ($true) {
    Show-Menu
    $choice = Read-Host "Choose an option"

    try {
        switch ($choice) {
            "1"  { Show-FullStatus; Pause-IRIS }
            "2"  { Show-ShortStatus; Pause-IRIS }
            "3"  { Show-RecentCommits; Pause-IRIS }
            "4"  { Show-Diff; Pause-IRIS }
            "5"  { Stage-SelectedFiles; Pause-IRIS }
            "6"  { Stage-AllFiles; Pause-IRIS }
            "7"  { Unstage-AllFiles; Pause-IRIS }
            "8"  { Commit-StagedFiles; Pause-IRIS }
            "9"  { Commit-OnlyFile; Pause-IRIS }
            "10" { Push-OriginMain; Pause-IRIS }
            "11" { Pull-OriginMain; Pause-IRIS }
            "12" { Run-SafeCheck; Pause-IRIS }
            "13" { Show-RepoSummary; Pause-IRIS }
            "0"  {
                Write-Host ""
                Write-Good "Exiting IRIS Git Helper."
                break
            }
            default {
                Write-Warn "Invalid option."
                Pause-IRIS
            }
        }
    }
    catch {
        Write-Bad $_.Exception.Message
        Pause-IRIS
    }
}