#!/usr/bin/env bash
# ====================================================================
# AndroidTUI - Script di Installazione e Configurazione per macOS
# ====================================================================
# Configura:
# 1. Verifica Python 3
# 2. Controllo Homebrew, ADB (android-platform-tools)
# 3. Opzione installazione Scrcpy (brew install scrcpy) o guida al sito https://scrcpy.org/
# 4. Installazione dipendenze Python (Textual, Rich, Pillow, ecc.)
# 5. Collegamento globale comando 'atui' in /usr/local/bin/atui o ~/.local/bin/atui
# 6. Creazione script rapido di avvio macOS (AndroidTUI.command)
# ====================================================================

set -e

SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$( dirname "$SCRIPT_DIR" )"

echo "=========================================================="
echo "    AndroidTUI - Installazione e Configurazione macOS     "
echo "=========================================================="
echo ""

# 1. Verifica Python 3
PYTHON_BIN="$(which python3 || which python || true)"
if [ -z "$PYTHON_BIN" ]; then
    echo "[ERRORE] Python 3 non trovato. Installa Python tramite Homebrew o python.org e riprova." >&2
    exit 1
fi
echo "[OK] Python rilevato: $PYTHON_BIN ($($PYTHON_BIN --version))"

# 2. Controllo Homebrew e ADB
echo ""
echo "[*] Verifica Homebrew e ADB (android-platform-tools)..."
if command -v adb >/dev/null 2>&1; then
    echo "[OK] ADB disponibile: $(which adb)"
elif command -v brew >/dev/null 2>&1; then
    echo "[*] ADB non trovato. Installazione android-platform-tools tramite Homebrew..."
    brew install --cask android-platform-tools || brew install android-platform-tools || true
else
    echo "[INFO] ADB non trovato e Homebrew non installato."
    echo "       Puoi scaricare i Platform-Tools ufficiali da:"
    echo "       https://developer.android.com/tools/releases/platform-tools"
fi

# 3. Opzione Scrcpy (Mirroring Schermo)
echo ""
echo "[*] Opzione installazione Scrcpy (Mirroring Schermo):"
INSTALL_SCRCPY="${INSTALL_SCRCPY:-}"
if [ "$1" == "--with-scrcpy" ]; then
    INSTALL_SCRCPY="yes"
elif [ "$1" == "--without-scrcpy" ] || [ "$1" == "--no-scrcpy" ]; then
    INSTALL_SCRCPY="no"
fi

if command -v scrcpy >/dev/null 2>&1; then
    echo "[OK] Scrcpy rilevato: $(which scrcpy)"
else
    echo "[INFO] Scrcpy non è attualmente installato."
    echo "       Per scaricarlo ed installarlo separatamente, consulta il sito ufficiale:"
    echo "       -> https://scrcpy.org/"
    echo "       Oppure installalo tramite Homebrew: brew install scrcpy"
    if [ "$INSTALL_SCRCPY" == "yes" ] && command -v brew >/dev/null 2>&1; then
        echo "[*] Installazione Scrcpy tramite Homebrew in corso..."
        brew install scrcpy || true
    fi
fi

# 4. Installazione dipendenze Python
echo ""
echo "[*] Installazione pacchetto AndroidTUI e dipendenze..."
chmod +x "$ROOT_DIR/atui"
"$PYTHON_BIN" -m pip install -e "$ROOT_DIR" || {
    echo "[AVVISO] Tento installazione con flag --user..."
    "$PYTHON_BIN" -m pip install --user -e "$ROOT_DIR" || true
}

# 5. Collegamento simbolico comando globale 'atui'
echo ""
echo "[*] Configurazione comando globale 'atui'..."
INSTALL_BIN="/usr/local/bin/atui"
USER_BIN="$HOME/.local/bin/atui"

if [ -w "/usr/local/bin" ]; then
    ln -sf "$ROOT_DIR/atui" "$INSTALL_BIN"
    echo "[OK] Collegamento creato in: $INSTALL_BIN"
elif command -v sudo >/dev/null 2>&1; then
    sudo ln -sf "$ROOT_DIR/atui" "$INSTALL_BIN" 2>/dev/null || true
    if [ -f "$INSTALL_BIN" ]; then
        echo "[OK] Collegamento creato con sudo in: $INSTALL_BIN"
    fi
fi

if [ ! -f "$INSTALL_BIN" ]; then
    mkdir -p "$HOME/.local/bin"
    ln -sf "$ROOT_DIR/atui" "$USER_BIN"
    echo "[OK] Collegamento creato in: $USER_BIN"
    echo "     Assicurati che ~/.local/bin sia nel tuo \$PATH (es. in ~/.zshrc o ~/.bash_profile)"
fi

# 6. Creazione Script Launcher macOS per avvio rapido con doppio click
LAUNCHER_APP="$HOME/Desktop/AndroidTUI.command"
cat <<EOF > "$LAUNCHER_APP"
#!/usr/bin/env bash
cd "$ROOT_DIR"
exec "$ROOT_DIR/atui"
EOF
chmod +x "$LAUNCHER_APP"
echo "[OK] Scorciatoia creata sulla scrivania: $LAUNCHER_APP"

echo ""
echo "=========================================================="
echo "      INSTALLAZIONE macOS COMPLETATA CON SUCCESSO!        "
echo "=========================================================="
echo "Puoi ora avviare AndroidTUI dal Terminale con:"
echo "   atui"
echo "oppure facendo doppio click su 'AndroidTUI.command' sulla scrivania."
echo ""
