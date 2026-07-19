param(
    [string]$Destination
)

$ErrorActionPreference = "Stop"

$ytDlpVersion = "2026.06.09"
$ytDlpUrl = "https://github.com/yt-dlp/yt-dlp/releases/download/$ytDlpVersion/yt-dlp.exe"
$ytDlpSha256 = "3a48cb955d55c8821b60ccbdbbc6f61bc958f2f3d3b7ad5eaf3d83a543293a27"
$ytDlpSourceUrl = "https://github.com/yt-dlp/yt-dlp/releases/download/$ytDlpVersion/yt-dlp.tar.gz"
$ytDlpSourceSha256 = "7603f876b78d08b5fdd5bcd1d368590fde22c3c18e4ea00766d51120d21cc679"
$ytDlpNoticesUrl = "https://raw.githubusercontent.com/yt-dlp/yt-dlp/$ytDlpVersion/THIRD_PARTY_LICENSES.txt"
$ytDlpNoticesSha256 = "b085c65586a953cdb4b13c6390d63ec984d66912e4b6a19e66ba3582f2ed104b"
$denoVersion = "2.8.1"
$denoUrl = "https://github.com/denoland/deno/releases/download/v$denoVersion/deno-x86_64-pc-windows-msvc.zip"
$denoSha256 = "5fb5bac71f609fb91ec8960fb290885aadc27eeb22f07a8eca0c3db6be38b11a"
$projectRoot = Split-Path -Parent $PSScriptRoot
$cacheRoot = Join-Path $projectRoot ".build-tools\youtube-resolver-$ytDlpVersion-deno-$denoVersion"
$ytDlpPath = Join-Path $cacheRoot "yt-dlp.exe"
$ytDlpSourcePath = Join-Path $cacheRoot "yt-dlp.tar.gz"
$ytDlpNoticesPath = Join-Path $cacheRoot "YT-DLP-THIRD-PARTY-LICENSES.txt"
$denoArchive = Join-Path $cacheRoot "deno-x86_64-pc-windows-msvc.zip"
$denoExpanded = Join-Path $cacheRoot "deno-expanded"
$destinationRoot = if ($Destination) {
    [System.IO.Path]::GetFullPath($Destination)
} else {
    Join-Path $projectRoot "media-tools"
}

New-Item -ItemType Directory -Path $cacheRoot, $destinationRoot -Force | Out-Null
if (-not (Test-Path -LiteralPath $ytDlpPath -PathType Leaf)) {
    Invoke-WebRequest -Uri $ytDlpUrl -OutFile $ytDlpPath -UseBasicParsing
}
if (-not (Test-Path -LiteralPath $denoArchive -PathType Leaf)) {
    Invoke-WebRequest -Uri $denoUrl -OutFile $denoArchive -UseBasicParsing
}
if (-not (Test-Path -LiteralPath $ytDlpSourcePath -PathType Leaf)) {
    Invoke-WebRequest -Uri $ytDlpSourceUrl -OutFile $ytDlpSourcePath -UseBasicParsing
}
if (-not (Test-Path -LiteralPath $ytDlpNoticesPath -PathType Leaf)) {
    Invoke-WebRequest -Uri $ytDlpNoticesUrl -OutFile $ytDlpNoticesPath -UseBasicParsing
}

$actualYtDlpHash = (Get-FileHash -LiteralPath $ytDlpPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualYtDlpHash -ne $ytDlpSha256) {
    throw "yt-dlp SHA-256 mismatch. Expected $ytDlpSha256, got $actualYtDlpHash."
}
$actualDenoHash = (Get-FileHash -LiteralPath $denoArchive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualDenoHash -ne $denoSha256) {
    throw "Deno SHA-256 mismatch. Expected $denoSha256, got $actualDenoHash."
}
$actualYtDlpSourceHash = (Get-FileHash -LiteralPath $ytDlpSourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualYtDlpSourceHash -ne $ytDlpSourceSha256) {
    throw "yt-dlp source SHA-256 mismatch. Expected $ytDlpSourceSha256, got $actualYtDlpSourceHash."
}
$actualYtDlpNoticesHash = (Get-FileHash -LiteralPath $ytDlpNoticesPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualYtDlpNoticesHash -ne $ytDlpNoticesSha256) {
    throw "yt-dlp notices SHA-256 mismatch. Expected $ytDlpNoticesSha256, got $actualYtDlpNoticesHash."
}

if (-not (Test-Path -LiteralPath (Join-Path $denoExpanded "deno.exe") -PathType Leaf)) {
    if (Test-Path -LiteralPath $denoExpanded) {
        Remove-Item -LiteralPath $denoExpanded -Recurse -Force
    }
    Expand-Archive -LiteralPath $denoArchive -DestinationPath $denoExpanded
}
$denoPath = Join-Path $denoExpanded "deno.exe"
if (-not (Test-Path -LiteralPath $denoPath -PathType Leaf)) {
    throw "Deno archive is incomplete."
}

Copy-Item -LiteralPath $ytDlpPath -Destination (Join-Path $destinationRoot "yt-dlp.exe") -Force
Copy-Item -LiteralPath $denoPath -Destination (Join-Path $destinationRoot "deno.exe") -Force
$ytDlpThirdPartyRoot = Join-Path $projectRoot "third_party\yt-dlp"
New-Item -ItemType Directory -Path $ytDlpThirdPartyRoot -Force | Out-Null
Copy-Item -LiteralPath $ytDlpSourcePath -Destination (Join-Path $ytDlpThirdPartyRoot "yt-dlp-$ytDlpVersion-source.tar.gz") -Force
Copy-Item -LiteralPath $ytDlpNoticesPath -Destination (Join-Path $projectRoot "licenses\YT-DLP-THIRD-PARTY-LICENSES.txt") -Force

$metadata = [ordered]@{
    ytDlpVersion = $ytDlpVersion
    ytDlpBinarySource = $ytDlpUrl
    ytDlpSha256 = $ytDlpSha256
    ytDlpSource = $ytDlpSourceUrl
    ytDlpSourceSha256 = $ytDlpSourceSha256
    denoVersion = $denoVersion
    denoSource = $denoUrl
    denoArchiveSha256 = $denoSha256
    denoSha256 = (Get-FileHash -LiteralPath (Join-Path $destinationRoot "deno.exe") -Algorithm SHA256).Hash.ToLowerInvariant()
    purpose = "Resolve selected YouTube quality to transient direct media URLs on the desktop"
}
$metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $destinationRoot "YOUTUBE-RESOLVER-VERSION.json") -Encoding UTF8

Write-Output "YouTube resolver assets installed to $destinationRoot"
Write-Output "yt-dlp $ytDlpVersion; Deno $denoVersion"
