<#
.SYNOPSIS
    Compilatore e pacchettizzatore dell'installer Windows (.msi) per AndroidTUI.

.DESCRIPTION
    1. Scarica i driver Google ADB USB ufficiali dal server Google:
       https://dl.google.com/android/repository/usb_driver_r13-windows.zip
    2. Scarica i Google Platform-Tools (adb.exe) se non presenti:
       https://dl.google.com/android/repository/platform-tools-latest-windows.zip
    3. Prepara l'albero di staging con launcher, modulo python, driver e binari adb
    4. Genera il pacchetto Microsoft Windows Installer: installer/dist/AndroidTUI-Setup.msi
    5. Configura il percorso di installazione, PATH di sistema e installazione automatica dei driver
#>

param(
    [string]$PythonExe = "",
    [switch]$SkipDownload = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$DownloadsDir = Join-Path $ScriptDir "downloads"
$StagingDir = Join-Path $ScriptDir "staging"
$DistDir = Join-Path $ScriptDir "dist"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AndroidTUI - Costruzione Installer Windows (.msi)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Trova interprete Python
if (-not $PythonExe) {
    $pythonCandidates = @(
        "C:\Users\SiMonee\AppData\Local\Programs\Python\Python311\python.exe",
        "C:\Users\SiMonee\AppData\Local\Programs\Python\Python313\python.exe",
        (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
    )
    foreach ($cand in $pythonCandidates) {
        if ($cand -and (Test-Path $cand)) {
            $PythonExe = $cand
            break
        }
    }
}

if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    Write-Error "Interprete Python non trovato. Specifica -PythonExe <percorso>"
}
Write-Host "[*] Utilizzo Python: $PythonExe" -ForegroundColor Green

# 2. Crea directory di lavoro
New-Item -ItemType Directory -Force -Path $DownloadsDir | Out-Null
New-Item -ItemType Directory -Force -Path $StagingDir | Out-Null
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

# 3. Download Google USB Driver
$usbDriverZip = Join-Path $DownloadsDir "usb_driver_r13-windows.zip"
$usbDriverUrl = "https://dl.google.com/android/repository/usb_driver_r13-windows.zip"

if (-not (Test-Path $usbDriverZip) -and -not $SkipDownload) {
    Write-Host "[*] Download Google USB Driver da Google ($usbDriverUrl)..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $usbDriverUrl -OutFile $usbDriverZip -UseBasicParsing
    Write-Host "[✓] Google USB Driver scaricato con successo." -ForegroundColor Green
} elseif (Test-Path $usbDriverZip) {
    Write-Host "[✓] Archivio Google USB Driver già presente in cache." -ForegroundColor Green
}

# 4. Estrazione driver
$driversStaging = Join-Path $StagingDir "drivers"
New-Item -ItemType Directory -Force -Path $driversStaging | Out-Null

if (Test-Path $usbDriverZip) {
    Write-Host "[*] Estrazione driver USB in staging..." -ForegroundColor Yellow
    Expand-Archive -Path $usbDriverZip -DestinationPath $driversStaging -Force
    Copy-Item (Join-Path $ScriptDir "install_driver.cmd") -Destination $driversStaging -Force
    Write-Host "[✓] Driver estratti in: $driversStaging" -ForegroundColor Green
}

# 5. Download Google Platform Tools (ADB)
$platformToolsZip = Join-Path $DownloadsDir "platform-tools-latest-windows.zip"
$platformToolsUrl = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"

if (-not (Test-Path $platformToolsZip) -and -not $SkipDownload) {
    Write-Host "[*] Download Google Platform-Tools ($platformToolsUrl)..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $platformToolsUrl -OutFile $platformToolsZip -UseBasicParsing
    Write-Host "[✓] Google Platform-Tools scaricati con successo." -ForegroundColor Green
} elseif (Test-Path $platformToolsZip) {
    Write-Host "[✓] Archivio Platform-Tools già presente in cache." -ForegroundColor Green
}

$toolsStaging = Join-Path $StagingDir "platform-tools"
New-Item -ItemType Directory -Force -Path $toolsStaging | Out-Null
if (Test-Path $platformToolsZip) {
    Write-Host "[*] Estrazione Platform-Tools in staging..." -ForegroundColor Yellow
    Expand-Archive -Path $platformToolsZip -DestinationPath $StagingDir -Force
}

# 6. Copia file applicazione
Write-Host "[*] Copia file applicazione AndroidTUI in staging..." -ForegroundColor Yellow
$appStaging = Join-Path $StagingDir "app"
New-Item -ItemType Directory -Force -Path $appStaging | Out-Null

Copy-Item (Join-Path $RootDir "atui.cmd") -Destination $appStaging -Force
Copy-Item (Join-Path $RootDir "androidtui.cmd") -Destination $appStaging -Force
Copy-Item (Join-Path $RootDir "pyproject.toml") -Destination $appStaging -Force
Copy-Item (Join-Path $RootDir "README.md") -Destination $appStaging -Force
Copy-Item (Join-Path $RootDir "android_tui") -Destination $appStaging -Recurse -Force

Write-Host "[✓] File applicativi pronti per l'impacchettamento." -ForegroundColor Green

# 7. Compilazione Installer MSI
Write-Host "[*] Compilazione pacchetto Windows Installer (.msi)..." -ForegroundColor Yellow
$buildScript = Join-Path $ScriptDir "build_msi.py"
& $PythonExe $buildScript

$msiOutput = Join-Path $DistDir "AndroidTUI-Setup.msi"
if (Test-Path $msiOutput) {
    $msiSize = (Get-Item $msiOutput).Length
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "   INSTALLER MSI GENERATO CON SUCCESSO!" -ForegroundColor Green
    Write-Host "   Percorso: $msiOutput" -ForegroundColor White
    Write-Host "   Dimensione: $([math]::Round($msiSize / 1KB, 2)) KB" -ForegroundColor White
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Per installare silenziosamente o testare l'installer:" -ForegroundColor Cyan
    Write-Host "  msiexec /i `"$msiOutput`" /l*v install.log" -ForegroundColor Gray
} else {
    Write-Error "Impossibile generare $msiOutput"
}
