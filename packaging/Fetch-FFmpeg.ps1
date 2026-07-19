param(
    [string]$Destination
)

$ErrorActionPreference = "Stop"

$ffmpegVersion = "8.1.2"
$archiveUrl = "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-8.1.2-essentials_build.zip"
$archiveSha256 = "db580001caa24ac104c8cb856cd113a87b0a443f7bdf47d8c12b1d740584a2ec"
$projectRoot = Split-Path -Parent $PSScriptRoot
$cacheRoot = Join-Path $projectRoot ".build-tools\ffmpeg-$ffmpegVersion"
$archivePath = Join-Path $cacheRoot "ffmpeg-$ffmpegVersion-essentials_build.zip"
$extractRoot = Join-Path $cacheRoot "expanded"
$packageRoot = Join-Path $extractRoot "ffmpeg-$ffmpegVersion-essentials_build"
$destinationRoot = if ($Destination) {
    [System.IO.Path]::GetFullPath($Destination)
} else {
    Join-Path $projectRoot "media-tools"
}

New-Item -ItemType Directory -Path $cacheRoot -Force | Out-Null
New-Item -ItemType Directory -Path $destinationRoot -Force | Out-Null

if (-not (Test-Path -LiteralPath $archivePath)) {
    Invoke-WebRequest -Uri $archiveUrl -OutFile $archivePath -UseBasicParsing
}

$actualArchiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualArchiveHash -ne $archiveSha256) {
    throw "FFmpeg archive SHA-256 mismatch. Expected $archiveSha256, got $actualArchiveHash."
}

if (-not (Test-Path -LiteralPath $packageRoot)) {
    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractRoot
}

$ffmpegSource = Join-Path $packageRoot "bin\ffmpeg.exe"
$ffprobeSource = Join-Path $packageRoot "bin\ffprobe.exe"
$licenseSource = Join-Path $packageRoot "LICENSE"
$readmeSource = Join-Path $packageRoot "README.txt"
foreach ($required in @($ffmpegSource, $ffprobeSource, $licenseSource, $readmeSource)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "FFmpeg package is incomplete: $required"
    }
}

Copy-Item -LiteralPath $ffmpegSource -Destination (Join-Path $destinationRoot "ffmpeg.exe") -Force
Copy-Item -LiteralPath $ffprobeSource -Destination (Join-Path $destinationRoot "ffprobe.exe") -Force
Copy-Item -LiteralPath $licenseSource -Destination (Join-Path $projectRoot "licenses\FFMPEG-GPL-3.0.txt") -Force
Copy-Item -LiteralPath $readmeSource -Destination (Join-Path $projectRoot "licenses\FFMPEG-BUILD-README.txt") -Force

$metadata = [ordered]@{
    version = $ffmpegVersion
    variant = "essentials_build"
    source = $archiveUrl
    archiveSha256 = $archiveSha256
    ffmpegSha256 = (Get-FileHash -LiteralPath (Join-Path $destinationRoot "ffmpeg.exe") -Algorithm SHA256).Hash.ToLowerInvariant()
    ffprobeSha256 = (Get-FileHash -LiteralPath (Join-Path $destinationRoot "ffprobe.exe") -Algorithm SHA256).Hash.ToLowerInvariant()
    license = "GPL-3.0"
}
$metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $destinationRoot "FFMPEG-VERSION.json") -Encoding UTF8

Write-Output "FFmpeg $ffmpegVersion installed to $destinationRoot"
Write-Output "Archive SHA-256: $archiveSha256"
