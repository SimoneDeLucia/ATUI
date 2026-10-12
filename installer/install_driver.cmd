@echo off
setlocal EnableDelayedExpansion

echo ========================================================
echo   AndroidTUI - Installazione Driver Google USB ADB
echo ========================================================
echo.

set "DRIVER_INF=%~dp0drivers\usb_driver\android_winusb.inf"
if not exist "%DRIVER_INF%" (
    set "DRIVER_INF=%~dp0drivers\android_winusb.inf"
)

if not exist "%DRIVER_INF%" (
    echo [ERRORE] File driver non trovato: %DRIVER_INF%
    echo Assicurati che l'archivio driver sia stato estratto correttamente.
    pause
    exit /b 1
)

echo Percorso driver: %DRIVER_INF%
echo Registrazione del driver Google ADB nel driver store di Windows...
echo.

pnputil.exe /add-driver "%DRIVER_INF%" /install
set "PNP_ERR=%ERRORLEVEL%"

if %PNP_ERR% EQU 0 (
    echo.
    echo [SUCCESSO] Driver Google USB ADB installato e associato correttamente!
) else (
    echo.
    echo [INFO] Operazione pnputil terminata (codice: %PNP_ERR%).
    echo Se richiesto, esegui questo script come Amministratore.
)

echo.
pause
