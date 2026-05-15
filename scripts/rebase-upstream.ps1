[CmdletBinding()]
param(
    [switch]$Push,
    [string]$UpstreamUrl = "https://github.com/CINEV/codex-lb-cinamon.git",
    [string]$UpstreamBranch = "main",
    [string]$OriginRemote = "origin"
)

# Default flow:
# git status --porcelain
# git fetch upstream
# git rebase upstream/main
# git push --force-with-lease origin $CurrentBranch

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$GitArgs
    )

    & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Get-GitOutput {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$GitArgs
    )

    $output = & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed with exit code $LASTEXITCODE"
    }

    return $output
}

if ((Get-GitOutput rev-parse --is-inside-work-tree) -ne "true") {
    throw "This script must be run inside a Git work tree."
}

$CurrentBranch = Get-GitOutput rev-parse --abbrev-ref HEAD
if ($CurrentBranch -eq "HEAD") {
    throw "Cannot rebase from a detached HEAD."
}

$StatusLines = @(Get-GitOutput status --porcelain)
$TrackedChanges = @($StatusLines | Where-Object { $_ -and -not $_.StartsWith("?? ") })
if ($TrackedChanges.Count -gt 0) {
    throw "Commit, stash, or discard tracked changes before rebasing."
}

$ExistingUpstream = $null
try {
    $ExistingUpstream = Get-GitOutput remote get-url upstream
} catch {
    Write-Host "Adding upstream remote: $UpstreamUrl"
    Invoke-Git remote add upstream $UpstreamUrl
}

if ($ExistingUpstream -and ($ExistingUpstream -ne $UpstreamUrl)) {
    throw "Existing upstream URL is '$ExistingUpstream', expected '$UpstreamUrl'."
}

Write-Host "Fetching upstream..."
Invoke-Git fetch upstream

$UpstreamRef = "upstream/$UpstreamBranch"
Write-Host "Rebasing $CurrentBranch onto $UpstreamRef..."
Invoke-Git rebase $UpstreamRef

Write-Host ""
Write-Host "Status against ${UpstreamRef}:"
Invoke-Git rev-list --left-right --count "$CurrentBranch...$UpstreamRef"

$OriginRef = "$OriginRemote/$CurrentBranch"
& git rev-parse --verify --quiet $OriginRef | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Status against ${OriginRef}:"
    Invoke-Git rev-list --left-right --count "$CurrentBranch...$OriginRef"
} elseif ($LASTEXITCODE -ne 1) {
    throw "git rev-parse --verify --quiet $OriginRef failed with exit code $LASTEXITCODE"
}

if ($Push) {
    Write-Host ""
    Write-Host "Pushing $CurrentBranch to $OriginRemote with --force-with-lease..."
    Invoke-Git push --force-with-lease $OriginRemote $CurrentBranch
}
