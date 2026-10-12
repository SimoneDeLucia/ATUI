#!/usr/bin/env bash
# ====================================================================
# AndroidTUI - Script di Installazione e Configurazione per Linux
# ====================================================================
# Configura:
# 1. Regole udev (/etc/udev/rules.d/51-android.rules) per accesso USB senza root
# 2. Strumenti ADB e Scrcpy tramite gestore pacchetti (apt, pacman, dnf)
# 3. Dipendenze Python (Textual, Rich, Pillow, ecc.)
# 4. Collegamento globale comando 'atui' in /usr/local/bin/atui
# 5. Voce desktop in ~/.local/share/applications/android-tui.desktop
# ====================================================================

set -e

SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$( dirname "$SCRIPT_DIR" )"

echo "=========================================================="
echo "    AndroidTUI - Installazione e Configurazione Linux     "
echo "=========================================================="
echo ""

# 1. Verifica Python
PYTHON_BIN="$(which python3 || which python || true)"
if [ -z "$PYTHON_BIN" ]; then
    echo "[ERRORE] Python 3 non trovato. Installa python3 e riprova." >&2
    exit 1
fi
echo "[OK] Python rilevato: $PYTHON_BIN ($($PYTHON_BIN --version))"

# 2. Configurazione Regole UDEV per accesso USB ai telefoni Android
echo ""
echo "[*] Configurazione regole udev per dispositivi Android USB..."
UDEV_SOURCE="$SCRIPT_DIR/51-android.rules"

if [ -f "$UDEV_SOURCE" ]; then
    if [ "$EUID" -eq 0 ]; then
        cp "$UDEV_SOURCE" /etc/udev/rules.d/51-android.rules
        chmod 644 /etc/udev/rules.d/51-android.rules
        udevadm control --reload-rules 2>/dev/null || true
        udevadm trigger 2>/dev/null || true
        echo "[OK] Regole udev installate in /etc/udev/rules.d/51-android.rules"
    elif command -v sudo >/dev/null 2>&1; then
        echo "Richiesta autorizzazione sudo per copiare le regole udev in /etc/udev/rules.d/..."
        sudo cp "$UDEV_SOURCE" /etc/udev/rules.d/51-android.rules
        sudo chmod 644 /etc/udev/rules.d/51-android.rules
        sudo udevadm control --reload-rules 2>/dev/null || true
        sudo udevadm trigger 2>/dev/null || true
        echo "[OK] Regole udev installate con successo."
    else
        echo "[AVVISO] Impossibile copiare /etc/udev/rules.d/51-android.rules senza privilegi root."
        echo "Copia manualmente il file $UDEV_SOURCE in /etc/udev/rules.d/ con permessi root."
    fi
fi

# 3. Controllo ADB e Scrcpy (Opzionale)
echo ""
echo "[*] Verifica strumenti ADB..."
if ! command -v adb >/dev/null 2>&1; then
    echo "[INFO] ADB non trovato nel PATH. Per installarlo su Debian/Ubuntu: sudo apt install adb"
    echo "       Su Fedora: sudo dnf install android-tools"
    echo "       Su Arch:   sudo pacman -S android-tools"
else
    echo "[OK] ADB disponibile: $(which adb)"
fi

echo ""
echo "[*] Opzione installazione Scrcpy (Mirroring Schermo):"
INSTALL_SCRCPY="${INSTALL_SCRCPY:-}"
if [ "$1" == "--with-scrcpy" ]; then
    INSTALL_SCRCPY="yes"
elif [ "$1" == "--without-scrcpy" ] || [ "$1" == "--no-scrcpy" ]; then
    INSTALL_SCRCPY="no"
fi

if ! command -v scrcpy >/dev/null 2>&1; then
    echo "[INFO] Scrcpy non è attualmente installato."
    echo "       Se desideri installarlo separatamente, consulta il sito ufficiale:"
    echo "       -> https://scrcpy.org/"
    echo "       Oppure installalo tramite gestore pacchetti: sudo apt install scrcpy"
    if [ "$INSTALL_SCRCPY" == "yes" ]; then
        echo "[*] Tentativo di installazione automatica Scrcpy..."
        if command -v apt >/dev/null 2>&1; then
            sudo apt update && sudo apt install -y scrcpy || true
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y scrcpy || true
        elif command -v pacman >/dev/null 2>&1; then
            sudo pacman -S --noconfirm scrcpy || true
        fi
    fi
else
    echo "[OK] Scrcpy rilevato: $(which scrcpy)"
fi

# 4. Installazione dipendenze Python
echo ""
echo "[*] Installazione pacchetto AndroidTUI e dipendenze..."
chmod +x "$ROOT_DIR/atui"
"$PYTHON_BIN" -m pip install -e "$ROOT_DIR" || {
    echo "[AVVISO] Installazione pip non riuscita con flag -e. Tento installazione utenti..."
    "$PYTHON_BIN" -m pip install --user -e "$ROOT_DIR" || true
}

# 5. Collegamento simbolico globale comando 'atui'
echo ""
echo "[*] Configurazione comando globale 'atui'..."
INSTALL_BIN="/usr/local/bin/atui"
USER_BIN="$HOME/.local/bin/atui"

if [ -w "/usr/local/bin" ]; then
    ln -sf "$ROOT_DIR/atui" "$INSTALL_BIN"
    echo "[OK] Collegamento creato in: $INSTALL_BIN"
elif command -v sudo >/dev/null 2>&1; then
    sudo ln -sf "$ROOT_DIR/atui" "$INSTALL_BIN"
    echo "[OK] Collegamento creato con sudo in: $INSTALL_BIN"
else
    mkdir -p "$HOME/.local/bin"
    ln -sf "$ROOT_DIR/atui" "$USER_BIN"
    echo "[OK] Collegamento creato in: $USER_BIN (assicurati che ~/.local/bin sia nel tuo \$PATH)"
fi

# 6. Creazione Desktop Entry
echo ""
echo "[*] Creazione icona desktop in ~/.local/share/applications/..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat <<EOF > "$DESKTOP_DIR/android-tui.desktop"
[Desktop Entry]
Name=AndroidTUI
Comment=Terminal UI for Android ADB File Management & Mirroring
Exec=bash -c '$ROOT_DIR/atui'
Icon=phone
Terminal=true
Type=Application
Categories=Utility;System;Development;
Keywords=android;adb;tui;scrcpy;file-manager;
EOF

chmod +x "$DESKTOP_DIR/android-tui.desktop"
echo "[OK] Desktop entry creata: $DESKTOP_DIR/android-tui.desktop"

echo ""
echo "=========================================================="
echo "      INSTALLAZIONE LINUX COMPLETATA CON SUCCESSO!        "
echo "=========================================================="
echo "Puoi ora avviare AndroidTUI da qualsiasi terminale con:"
echo "   atui"
echo ""
