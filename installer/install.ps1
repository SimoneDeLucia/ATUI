<#
.SYNOPSIS
    Script di installazione rapida (one-liner) per ATUI (Android Terminal User Interface) su Windows.

.DESCRIPTION
    Scarica l'ultimo installer ufficiale Windows (.msi) da GitHub Releases ed esegue l'installazione.
    In alternativa, se la release remota non e ancora disponibile o si desidera l'installazione
    tramite pip/python, offre il fallback automatico.

.EXAMPLE
    irm https://raw.githubusercontent.com/SimoneDeLucia/ATUI/main/installer/install.ps1 | iex
#>

[CmdletBinding()]
param(
    [string]$Version = "latest",
    [switch]$Interactive = $false,
    [switch]$UsePipFallback = $false,
    [string]$CustomMsiUrl = ""
)

$ErrorActionPreference = "Stop"

function Show-Banner {
    Write-Host ""
    Write-Host "   ==========================================================" -ForegroundColor Cyan
    Write-Host "      _   _____ _   _ ___ " -ForegroundColor Cyan
    Write-Host "     /_\ |_   _| | | |_ _|  Android Terminal User Interface" -ForegroundColor Cyan
    Write-Host "    / _ \  | | | |_| || |   Versione: v1.0.2" -ForegroundColor Cyan
    Write-Host "   /_/ \_\ |_|  \___/|___|  https://github.com/SimoneDeLucia/ATUI" -ForegroundColor Cyan
    Write-Host "   ==========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Admin {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

try {
    Show-Banner

    # 1. Verifica Sistema Operativo
    if ($PSVersionTable.PSEdition -ne "Desktop" -and $IsLinux) {
        Write-Host "[!] Rilevato ambiente Linux o non-Windows." -ForegroundColor Yellow
        Write-Host "[*] Su Linux, puoi installare ATUI con:" -ForegroundColor White
        Write-Host "    curl -fsSL https://raw.githubusercontent.com/SimoneDeLucia/ATUI/main/installer/install_linux.sh | bash" -ForegroundColor Cyan
        exit 0
    }

    if ($PSVersionTable.PSEdition -ne "Desktop" -and $IsMacOS) {
        Write-Host "[!] Rilevato ambiente macOS." -ForegroundColor Yellow
        Write-Host "[*] Su macOS, puoi installare ATUI con:" -ForegroundColor White
        Write-Host "    curl -fsSL https://raw.githubusercontent.com/SimoneDeLucia/ATUI/main/installer/install_macos.sh | bash" -ForegroundColor Cyan
        exit 0
    }

    $repoUrl = "https://github.com/SimoneDeLucia/ATUI"
    $msiFileName = "AndroidTUI-Setup.msi"
    $tempDir = [System.IO.Path]::GetTempPath()
    $localMsiPath = Join-Path $tempDir $msiFileName

    if ($CustomMsiUrl) {
        $downloadUrl = $CustomMsiUrl
    } elseif ($Version -eq "latest") {
        $downloadUrl = "$repoUrl/releases/latest/download/$msiFileName"
    } else {
        $downloadUrl = "$repoUrl/releases/download/$Version/$msiFileName"
    }

    $installedViaMsi = $false

    if (-not $UsePipFallback) {
        Write-Host "[*] Download dell'installer Windows (.msi) in corso..." -ForegroundColor Yellow
        Write-Host "    Sorgente: $downloadUrl" -ForegroundColor Gray

        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
            Invoke-WebRequest -Uri $downloadUrl -OutFile $localMsiPath -UseBasicParsing -ErrorAction Stop
            
            $msiItem = Get-Item $localMsiPath
            if ($msiItem.Length -lt 10240) {
                # Meno di 10KB indica probabilmente una pagina HTML di errore 404 di GitHub
                throw "File scaricato non valido (dimensione anomala: $($msiItem.Length) byte)"
            }

            Write-Host "[OK] Download completato: $localMsiPath ($([math]::Round($msiItem.Length / 1KB, 1)) KB)" -ForegroundColor Green

            Write-Host "[*] Avvio installazione di ATUI tramite Windows Installer (msiexec)..." -ForegroundColor Yellow

            $msiArgs = if ($Interactive) {
                "/i `"$localMsiPath`""
            } else {
                "/i `"$localMsiPath`" /passive /norestart"
            }

            $proc = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru
            if ($proc.ExitCode -eq 0) {
                Write-Host "[OK] Windows Installer completato con successo (Exit Code: 0)." -ForegroundColor Green
                $installedViaMsi = $true
            } else {
                Write-Host "[!] L'installer ha restituito il codice di uscita: $($proc.ExitCode)" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "[!] Impossibile scaricare o eseguire l'MSI da GitHub Releases ($($_.Exception.Message))." -ForegroundColor Yellow
            Write-Host "    Nota: Se la release non e ancora stata pubblicata su GitHub, puoi usare la modalita fallback Python." -ForegroundColor Gray
        }
    }

    # Se MSI non e riuscito o e stato richiesto UsePipFallback
    if (-not $installedViaMsi) {
        Write-Host ""
        Write-Host "[*] Tentativo di installazione via Python pip (Cross-platform Fallback)..." -ForegroundColor Yellow
        
        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCmd) {
            $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
        }

        if ($pythonCmd) {
            Write-Host "[*] Trovato interprete Python: $($pythonCmd.Source)" -ForegroundColor Green
            Write-Host "[*] Installazione pacchetto ATUI da GitHub..." -ForegroundColor Yellow
            & $pythonCmd.Source -m pip install --upgrade "git+https://github.com/SimoneDeLucia/ATUI.git"
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] Installazione completata con successo tramite pip!" -ForegroundColor Green
            } else {
                Write-Host "[!] Errore durante l'installazione pip." -ForegroundColor Red
            }
        } else {
            Write-Host "[X] Interprete Python non trovato. Installa Python da https://python.org o scarica l'installer .msi manualmente." -ForegroundColor Red
            Write-Host "    Release GitHub: $repoUrl/releases" -ForegroundColor Cyan
        }
    }

    # 4. Verifica Strumenti Opzionali
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "   Riepilogo Componenti di Sistema" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan

    # Verifica ADB
    $adbCmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($adbCmd) {
        Write-Host " [OK] Android Debug Bridge (ADB): Trovato ($($adbCmd.Source))" -ForegroundColor Green
    } else {
        Write-Host " [i] Android Debug Bridge (ADB): Non nel PATH di sistema." -ForegroundColor Yellow
        Write-Host "     (L'installer MSI include i binari Google ADB in Program Files/AndroidTUI/platform-tools)" -ForegroundColor Gray
    }

    # Verifica Scrcpy
    $scrcpyCmd = Get-Command scrcpy -ErrorAction SilentlyContinue
    if ($scrcpyCmd) {
        Write-Host " [OK] Scrcpy (Screen Mirroring): Rilevato ($($scrcpyCmd.Source))" -ForegroundColor Green
    } else {
        Write-Host " [i] Scrcpy (Screen Mirroring): Non rilevato." -ForegroundColor Yellow
        Write-Host "     Per abilitare la condivisione dello schermo con Scrcpy, installalo tramite:" -ForegroundColor Gray
        Write-Host "     winget install Genymobile.scrcpy" -ForegroundColor Cyan
        Write-Host "     oppure visita https://scrcpy.org/" -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "   INSTALLAZIONE COMPLETATA!" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "   Per avviare l'applicazione, apri un nuovo terminale e digita:" -ForegroundColor White
    Write-Host "      atui" -ForegroundColor Yellow
    Write-Host "   oppure:" -ForegroundColor White
    Write-Host "      androidtui" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Documentazione: https://github.com/SimoneDeLucia/ATUI" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "[!] Errore imprevisto durante l'esecuzione:" -ForegroundColor Red
    Write-Host "    $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}
