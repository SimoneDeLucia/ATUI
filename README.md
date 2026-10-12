# ⚡ AndroidTUI — ADB Terminal User Interface

[🇮🇹 Italiano](README.md) | [🇬🇧 English](README_EN.md)

> **Un gestore file system Android da terminale potente, elegante e reattivo, basato sui comandi ADB e ispirato all'estetica Miller Columns di [pikpaktui](https://github.com/Bengerthelorf/pikpaktui).**

---

## 🌟 Caratteristiche Principali

- 🖱️ **Riquadri di Selezione Checkbox Cliccabili con il Mouse**:
  - Colonna dedicata `[✓]` per selezionare o deselezionare file singoli con un click del mouse senza muovere il cursore né perdere la posizione.
  - Cliccando sull'intestazione `[✓]` seleziona o deseleziona tutti i file della cartella.
- 🖼️ **Anteprime Grafiche con Thumbnail per Tutte le Tipologie di File**:
  - Grafica cyber in stile truecolor half-block per tutte le categorie: **APK** (Mascotte Android verde), **Audio** (Equalizzatore/Waveform), **Documenti** (Foglio con piega), **Archivi** (Scatola con cerniera), **Codice Sorgente** (Console e sintassi), **Binari di Sistema** (Microprocessore CPU).
  - **Anteprima di Default per File Non Riconosciuti**: Card dedicata con stemma della Graffetta `📎` per formati non noti (es. `prod.keys`), con indicazione dell'estensione e dettagli del file.
  - Anteprima fotografica ad alta risoluzione (JPG, PNG, HEIC, WEBP, GIF) ed estrazione frame video MP4 tramite FFmpeg.
- 🔄 **Ordinamento per Nome, Dimensione e Tipologia (Mouse e Tastiera)**:
  - Clicca sull'intestazione della colonna (`Nome`, `Dimensione`, `Tipo`) per ordinare all'istante con frecce indicatrici (`▲` / `▼`).
  - Tramite tastiera: premi `s` per ciclare il criterio di ordinamento (Nome → Dimensione → Tipo), premi `S` (Shift+S) per invertire l'ordine (Crescente ↔ Decrescente).
- 🖥️ **Condivisione Schermo Integrata con Scrcpy**:
  - Integrazione nativa con [scrcpy](https://github.com/genymobile/scrcpy) per visualizzare e controllare lo schermo del dispositivo Android in tempo reale con bassissima latenza.
  - Avvia con un click sul pulsante `[ 🖥️ Scrcpy ]` nell'header oppure con la scorciatoia da tastiera `m`.
  - Finestra informativa guidata se Scrcpy non è presente sul sistema.
- 📦 **Installer Windows .msi e Compatibilità Linux Nativa**:
  - Installer Windows `.msi` configurabile (`installer/dist/AndroidTUI-Setup.msi` o `build_installer.ps1`) che scarica e installa automaticamente i driver Google ADB USB ufficiali e i platform-tools.
  - Compatibilità Linux completa: script di avvio `atui`, regole udev `installer/51-android.rules` per accesso non-root USB e script `installer/install_linux.sh`.
  - Branch Git separato `linux` per isolamento e manutenzione su distribuzioni Linux.
- 🖥️ **Interfaccia a 3 Colonne (Miller Columns)**:
  - **Colonna Genitore**: Panoramica della cartella superiore con voce `⬆️ ..` navigabile con cursore da tastiera o cliccabile con mouse per salire istantaneamente.
  - **Colonna Attiva**: Lista file con checkbox dedicate, dimensioni formattate, categoria, date e permessi.
  - **Colonna Anteprima**: Card grafiche ad alta risoluzione e visualizzatore testo scorrevole per codice e documenti.
- 📱 **Header Dispositivo con Locazioni di Memoria Note**:
  - Mostra lo stato di connessione (USB / Wireless), latenza segnale, batteria, e versione Android.
  - Scorciatoie rapide: **Memoria Interna** (`/sdcard`) e **MicroSD Esterna** (`/storage/XXXX-XXXX`) con tasti `[📱 Interna]` e `[💾 MicroSD]` o tasto `g`.
- 🌐 **Supporto Bilingue Completo (Italiano / Inglese)**:
  - Cambio lingua istantaneo con un click (`[🌐 IT / EN]`) o tasto `F2`.
- 🎨 **Architettura CSS Modulare**:
  - File separati in `android_tui/css/` (`base.css`, `header.css`, `footer.css`, `browser.css`, `dashboard.css`, `modals.css`).

---

## ⌨️ Scorciatoie da Tastiera (Keybindings)

| Tasto | Azione | Descrizione |
| :---: | :--- | :--- |
| `j` / `↓` | **Giù** | Sposta il cursore verso il basso nella lista file |
| `k` / `↑` | **Su** | Sposta il cursore verso l'alto nella lista file |
| `Enter` / `l` | **Apri** | Entra nella cartella selezionata o apre il download per i file |
| `Backspace` / `h` | **Genitore** | Torna alla cartella superiore |
| `Spazio` | **Seleziona** | Seleziona/deseleziona file per operazioni batch (mantiene il cursore) |
| `a` | **Tutti** | Seleziona o deseleziona tutti i file |
| `s` | **Ordina** | Cicla criterio di ordinamento (Nome → Dimensione → Tipo) |
| `S` (Shift+S) | **Inverti Ordine** | Inverte l'ordinamento (Crescente ↔ Decrescente) |
| `m` | **Scrcpy** | Condivide lo schermo del dispositivo con scrcpy |
| `Esc` | **Annulla Selez.** | Cancella la selezione batch attiva |
| `g` | **Memorie (Jump)** | Finestra di navigazione rapida (Interna, MicroSD, Download, DCIM, Root) |
| `F2` | **Lingua** | Cambia lingua tra Italiano e Inglese |
| `d` | **Scarica su PC** | Esegue `adb pull` del file o dei file selezionati |
| `u` | **Carica da PC** | Esegue `adb push` di un file dal tuo PC al telefono |
| `f` | **Nuova Cartella** | Crea una nuova directory sul telefono (`mkdir -p`) |
| `n` | **Rinomina** | Modifica il nome del file o cartella (`mv`) |
| `x` | **Elimina** | Elimina elemento/i con finestra di conferma |
| `c` | **Dispositivi** | Apre il menu di gestione e selezione dispositivi ADB |
| `Ctrl+D` | **Disconnetti** | Disconnette il dispositivo attivo e torna al menu principale |
| `r` | **Ricarica** | Aggiorna la vista e riscatta i file da ADB |
| `?` | **Aiuto** | Mostra la finestra di aiuto e comandi |
| `q` | **Esci** | Chiude AndroidTUI |

---

## 🚀 Requisiti e Installazione

### 1. Prerequisiti
- **Python 3.10+** installato sul sistema.
- **Android Debug Bridge (`adb`)**:
  - Incluso con Android Studio oppure scaricabile separatamente come [SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools).
  - Su Windows, AndroidTUI cerca automaticamente `adb.exe` in `C:\platform-tools\`, nel PATH di sistema e nelle cartelle standard.

### 2. Installazione delle dipendenze
Dalla cartella del progetto:
```bash
pip install -r requirements.txt
```

### 3. Avvio Globale da Qualsiasi Terminale
L'applicazione è configurata nel `$PATH` di sistema e si avvia direttamente con il comando:
```bash
atui
```

Opzioni disponibili da riga di comando:
```bash
# Avvio standard
atui

# Avvio diretto in modalità demo / test
atui --demo

# Specificare un percorso ADB alternativo
atui --adb-path "C:\tuo-percorso\adb.exe"

# Mostra aiuto e opzioni
atui --help
```

---

## 📱 Guida alla Connessione

### Modalità 1: Cavo USB
1. Sul tuo smartphone Android, vai in **Impostazioni > Info sul telefono** e tocca **Numero build** 7 volte per attivare le *Opzioni sviluppatore*.
2. Vai in **Impostazioni > Sistema > Opzioni sviluppatore** e attiva **Debug USB**.
3. Collega il telefono al PC con cavo USB.
4. Quando sul display del telefono compare il messaggio **"Consenti debug USB da questo computer?"**, seleziona la spunta e premi **Consenti**.
5. In AndroidTUI, premi `[Cerca Dispositivi USB]` (o premi `r` per ricaricare).

### Modalità 2: Wireless Debugging (Android 11+)
1. Collega smartphone e PC alla **stessa rete Wi-Fi**.
2. Nelle *Opzioni sviluppatore*, attiva **Debug wireless** ed entra nel menu.
3. Se è la prima volta:
   - Seleziona **Accoppia dispositivo con codice di accoppiamento**.
   - In AndroidTUI clicca su `[Accoppia (Pair)]`, inserisci l'indirizzo IP:Porta e il codice a 6 cifre mostrato sul telefono.
4. Per connetterti:
   - Inserisci l'indirizzo IP e la porta principale visualizzati nella schermata Debug wireless e clicca su `[Connetti IP:Porta]`.

---

## 📁 Struttura del Progetto

```
AndroidTUI/
├── android_tui/
│   ├── __init__.py           # Info pacchetto e versione
│   ├── adb.py                # Wrapper motore ADB (comandi, parser ls/stat, pairing/connect)
│   ├── models.py             # Modelli dati (AdbDevice, FileEntry, stati)
│   ├── theme.py              # Palette colori, icone estensioni e foglio di stile CSS
│   ├── views/
│   │   ├── __init__.py
│   │   ├── header.py         # Barra superiore con badge dispositivo, batteria e breadcrumb
│   │   ├── footer.py         # Barra inferiore scorciatoie e notifiche toast
│   │   ├── disconnected.py   # Dashboard interattiva per connessione USB e Wireless
│   │   ├── browser.py        # Miller Columns 3-pane file manager
│   │   └── modals.py         # Finestre modali (WiFi, download, upload, elimina, aiuto)
│   └── app.py                # Applicazione principale Textual & worker asincroni
├── main.py                   # Script di avvio con argomenti CLI
├── requirements.txt          # Dipendenze Python (textual, rich)
└── README.md                 # Documentazione del progetto
```
