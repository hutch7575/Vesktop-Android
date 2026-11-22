[CmdletBinding()]
param(
    [string]$AdbPath = "adb",
    [string]$Serial = "",
    [string]$Destination = (Join-Path (Get-Location) ("Discord-APK-Export-" + (Get-Date -Format "yyyyMMdd-HHmmss")))
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Reads installed package files only. Does not uninstall, patch, root, change
# permissions or read Discord's private data. ADB must already be installed.
$adbCommand = Get-Command -Name $AdbPath -CommandType Application -ErrorAction Stop
$adbExecutable = $adbCommand.Source
$deviceArguments = @()
if ($Serial) { $deviceArguments = @("-s", $Serial) }

function Get-DiscordPaths {
    $lines = @(& $adbExecutable @deviceArguments shell pm path com.discord)
    if ($LASTEXITCODE -ne 0) { throw "ADB could not list Discord's APK paths." }
    $paths = @()
    foreach ($line in $lines) {
        $value = ([string]$line).Trim()
        if (-not $value) { continue }
        if ($value -notmatch '^package:(/data/app/[A-Za-z0-9_./+=-]+\.apk)$') {
            throw "Unexpected package path output. No additional files will be copied."
        }
        $path = $Matches[1]
        if ($path.Split('/') -contains '..') { throw "Invalid package path." }
        $paths += $path
    }
    if ($paths.Count -eq 0) { throw "Discord (com.discord) was not found on the selected device." }
    $unique = @($paths | Sort-Object -Unique)
    if ($unique.Count -ne $paths.Count) { throw "ADB returned duplicate paths." }
    return $unique
}

$deviceState = @(& $adbExecutable @deviceArguments get-state)
if ($LASTEXITCODE -ne 0 -or ($deviceState -join '').Trim() -ne 'device') {
    throw "Connect one Android device and authorise USB debugging. With multiple devices, pass -Serial."
}

$pathsBefore = @(Get-DiscordPaths)
$names = @($pathsBefore | ForEach-Object { [System.IO.Path]::GetFileName($_) })
if (@($names | Sort-Object -Unique).Count -ne $names.Count) { throw "APK filenames are not unique." }
$resolvedDestination = [System.IO.Path]::GetFullPath($Destination)
$zipPath = $resolvedDestination + ".zip"
if ((Test-Path -LiteralPath $resolvedDestination) -or (Test-Path -LiteralPath $zipPath)) {
    throw "The destination already exists. Choose a new -Destination."
}
New-Item -ItemType Directory -Path $resolvedDestination | Out-Null

foreach ($remote in $pathsBefore) {
    $name = [System.IO.Path]::GetFileName($remote)
    $local = Join-Path $resolvedDestination $name
    & $adbExecutable @deviceArguments pull $remote $local
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $local)) {
        throw "An APK copy failed. The export folder is partial; no ZIP was created."
    }
}

$pathsAfter = @(Get-DiscordPaths)
if (@(Compare-Object -ReferenceObject $pathsBefore -DifferenceObject $pathsAfter).Count -ne 0) {
    throw "Discord changed during export. The folder is partial; rerun with a new destination."
}

$hashes = @($names | Sort-Object | ForEach-Object {
    $hash = Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $resolvedDestination $_)
    $hash.Hash.ToLowerInvariant() + "  " + $_
})
$hashes | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $resolvedDestination "SHA256SUMS.txt")
Compress-Archive -LiteralPath @($names | ForEach-Object { Join-Path $resolvedDestination $_ }) -DestinationPath $zipPath
# Only APKs are packaged. The checksum list remains in the local export folder.
Write-Host ("Exported " + $names.Count + " installed APK file(s).")
Write-Host ("ZIP: " + $zipPath)
Write-Host "This copies installed application packages, not your messages or account data."
Write-Host "Installation completeness and APK signatures still require validation."
