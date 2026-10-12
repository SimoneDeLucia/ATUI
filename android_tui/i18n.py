"""
Internationalization (i18n) module for AndroidTUI.
Supports Italian (it) and English (en) with persistent language settings.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

SETTINGS_FILE = Path.home() / ".android_tui_settings.json"

_CURRENT_LANG = "it"

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # -----------------------------------------------------------------
    # General & App Branding
    # -----------------------------------------------------------------
    "app_title": {
        "it": "AndroidTUI",
        "en": "AndroidTUI",
    },
    "app_subtitle": {
        "it": "Interfaccia Terminale per Android ADB",
        "en": "ADB Terminal User Interface",
    },
    "ready": {
        "it": "Pronto.",
        "en": "Ready.",
    },
    "refreshed": {
        "it": "Ricaricato.",
        "en": "Refreshed.",
    },
    "items_loaded": {
        "it": "{count} elementi caricati",
        "en": "{count} items loaded",
    },
    "disconnected_toast": {
        "it": "Disconnesso da {name}. Ritorno al menu principale.",
        "en": "Disconnected from {name}. Returned to main menu.",
    },
    "conn_lost": {
        "it": "Connessione col dispositivo persa!",
        "en": "Device connection lost!",
    },
    "connected_to": {
        "it": "Connesso a {name}",
        "en": "Connected to {name}",
    },
    "device_unauthorized": {
        "it": "Dispositivo non autorizzato: accetta RSA sullo schermo del telefono",
        "en": "Unauthorized device: accept RSA prompt on phone screen",
    },
    "device_offline": {
        "it": "Dispositivo offline: ricollega cavo o riavvia ADB",
        "en": "Device offline: reconnect cable or restart ADB",
    },
    "no_devices_detected": {
        "it": "Nessun dispositivo rilevato. Usa il menu di connessione USB o WiFi.",
        "en": "No devices detected. Use USB or WiFi connection menu.",
    },

    # -----------------------------------------------------------------
    # Header Bar
    # -----------------------------------------------------------------
    "header_disconnected": {
        "it": " ⚠️ Disconnesso ",
        "en": " ⚠️ Disconnected ",
    },
    "header_no_device_ready": {
        "it": "Nessun dispositivo pronto · Clicca qui per collegare",
        "en": "No device ready · Click here to connect",
    },
    "header_signal_lost": {
        "it": "🔴 Segnale perso",
        "en": "🔴 Signal lost",
    },
    "header_latency_excellent": {
        "it": "Ottima",
        "en": "Excellent",
    },
    "header_latency_good": {
        "it": "Buona",
        "en": "Good",
    },
    "header_latency_slow": {
        "it": "Lenta",
        "en": "Slow",
    },
    "header_battery": {
        "it": "Batteria",
        "en": "Battery",
    },
    "header_internal": {
        "it": "📱 Interna",
        "en": "📱 Internal",
    },
    "header_sd": {
        "it": "💾 MicroSD",
        "en": "💾 MicroSD",
    },
    "header_no_sd": {
        "it": "Non presente",
        "en": "Not detected",
    },
    "header_free": {
        "it": "Libero",
        "en": "Free",
    },
    "header_jump_btn": {
        "it": "🚀 Memorie",
        "en": "🚀 Storages",
    },
    "header_lang_btn": {
        "it": "🌐 IT",
        "en": "🌐 EN",
    },

    # -----------------------------------------------------------------
    # Browser & Panes
    # -----------------------------------------------------------------
    "parent_pane_title": {
        "it": " 📁 Genitore: {path} ",
        "en": " 📁 Parent: {path} ",
    },
    "parent_go_up_item": {
        "it": "Cartella superiore",
        "en": "Parent directory",
    },
    "current_pane_title": {
        "it": " 📂 Contenuto: {path} ({count}) ",
        "en": " 📂 Contents: {path} ({count}) ",
    },
    "preview_pane_title": {
        "it": " 📄 Anteprima & Dettagli ",
        "en": " 📄 Preview & Details ",
    },
    "col_sel": {
        "it": "[✓]",
        "en": "[✓]",
    },
    "col_name": {
        "it": "Nome",
        "en": "Name",
    },
    "col_size": {
        "it": "Dimensione",
        "en": "Size",
    },
    "col_type": {
        "it": "Tipo",
        "en": "Type",
    },
    "col_modified": {
        "it": "Modificato",
        "en": "Modified",
    },
    "col_perms": {
        "it": "Permessi",
        "en": "Permissions",
    },
    "sorted_by": {
        "it": "Ordinato per: {col} ({order})",
        "en": "Sorted by: {col} ({order})",
    },
    "order_asc": {
        "it": "Crescente",
        "en": "Ascending",
    },
    "order_desc": {
        "it": "Decrescente",
        "en": "Descending",
    },
    "scrcpy_btn": {
        "it": "🖥️ Scrcpy",
        "en": "🖥️ Scrcpy",
    },
    "scrcpy_launched": {
        "it": "🖥️ Scrcpy avviato per {name}",
        "en": "🖥️ Scrcpy launched for {name}",
    },
    "scrcpy_not_found": {
        "it": "Scrcpy non trovato nel sistema",
        "en": "Scrcpy not found on system",
    },
    "scrcpy_demo_toast": {
        "it": "🖥️ Demo: Scrcpy simulato (collega un dispositivo reale per lo streaming)",
        "en": "🖥️ Demo: Scrcpy simulated (connect a real device for screen mirror)",
    },
    "scrcpy_modal_title": {
        "it": "Condivisione Schermo con Scrcpy",
        "en": "Screen Mirroring with Scrcpy",
    },
    "scrcpy_modal_desc": {
        "it": "Scrcpy consente di visualizzare e controllare lo schermo del dispositivo Android in tempo reale a 60 FPS con bassissima latenza.",
        "en": "Scrcpy allows you to display and control your Android device screen in real-time at 60 FPS with ultra-low latency.",
    },
    "scrcpy_install_guide": {
        "it": "Per installarlo:\n• Windows: winget install Genymobile.scrcpy\n• Linux: sudo apt install scrcpy (oppure pacman -S scrcpy)\n• macOS: brew install scrcpy\n\nOppure scarica l'archivio da: https://github.com/Genymobile/scrcpy/releases",
        "en": "To install it:\n• Windows: winget install Genymobile.scrcpy\n• Linux: sudo apt install scrcpy (or pacman -S scrcpy)\n• macOS: brew install scrcpy\n\nOr download binary from: https://github.com/Genymobile/scrcpy/releases",
    },
    "empty_folder": {
        "it": "Cartella vuota o nessun elemento selezionato.",
        "en": "Empty folder or no item selected.",
    },

    # -----------------------------------------------------------------
    # Preview Details
    # -----------------------------------------------------------------
    "meta_type": {
        "it": "Tipo",
        "en": "Type",
    },
    "meta_size": {
        "it": "Dimensione",
        "en": "Size",
    },
    "meta_perms": {
        "it": "Permessi",
        "en": "Permissions",
    },
    "meta_date": {
        "it": "Data",
        "en": "Date",
    },
    "meta_folder_desc": {
        "it": "Cartella di sistema/utente",
        "en": "System/user folder",
    },
    "meta_enter_folder_hint": {
        "it": "Premi [Enter] o doppio click per esplorare questa cartella.",
        "en": "Press [Enter] or double-click to explore this folder.",
    },
    "meta_content_details": {
        "it": "Dettagli Contenuto",
        "en": "Content Details",
    },
    "meta_img_preview": {
        "it": "🖼️  Immagine visualizzata in anteprima sopra",
        "en": "🖼️  Image preview displayed above",
    },
    "meta_vid_preview": {
        "it": "🎬  File Video (Anteprima fotogramma visualizzata sopra)",
        "en": "🎬  Video File (Frame preview displayed above)",
    },
    "meta_audio_desc": {
        "it": "🎵  File Audio / Musica",
        "en": "🎵  Audio / Music File",
    },
    "meta_apk_desc": {
        "it": "🤖  Pacchetto Applicazione Android (APK)",
        "en": "🤖  Android Application Package (APK)",
    },
    "meta_archive_desc": {
        "it": "📦  Archivio Compresso",
        "en": "📦  Compressed Archive",
    },
    "meta_format": {
        "it": "Formato",
        "en": "Format",
    },
    "meta_resolution": {
        "it": "Risoluzione",
        "en": "Resolution",
    },
    "meta_press_d_dl": {
        "it": "Premi [d] per scaricare il file originale sul PC.",
        "en": "Press [d] to download original file to PC.",
    },
    "meta_quick_actions": {
        "it": "Azioni rapide & Mouse:",
        "en": "Quick Actions & Mouse:",
    },
    "meta_act_dl": {
        "it": " • [bold #73daca][d][/] Scarica sul PC",
        "en": " • [bold #73daca][d][/] Download to PC",
    },
    "meta_act_select": {
        "it": " • [bold #73daca][␣ Spazio][/] Seleziona per download/elimina batch",
        "en": " • [bold #73daca][␣ Space][/] Select for batch download/delete",
    },
    "meta_act_rename": {
        "it": " • [bold #e0af68][n][/] Rinomina file",
        "en": " • [bold #e0af68][n][/] Rename file",
    },
    "meta_act_delete": {
        "it": " • [bold #f7768e][x][/] Elimina dal telefono",
        "en": " • [bold #f7768e][x][/] Delete from phone",
    },

    # -----------------------------------------------------------------
    # Footer Action Buttons
    # -----------------------------------------------------------------
    "fbtn_enter": {
        "it": "⏎ Apri",
        "en": "⏎ Open",
    },
    "fbtn_select": {
        "it": "✓ Sel",
        "en": "✓ Sel",
    },
    "fbtn_download": {
        "it": "📥 Scarica",
        "en": "📥 Download",
    },
    "fbtn_upload": {
        "it": "📤 Carica",
        "en": "📤 Upload",
    },
    "fbtn_mkdir": {
        "it": "📁 Cartella",
        "en": "📁 New Folder",
    },
    "fbtn_rename": {
        "it": "✏️ Rinomina",
        "en": "✏️ Rename",
    },
    "fbtn_delete": {
        "it": "🗑️ Elimina",
        "en": "🗑️ Delete",
    },
    "fbtn_devices": {
        "it": "📱 Dispositivi",
        "en": "📱 Devices",
    },
    "fbtn_disconnect": {
        "it": "🔌 Disconnetti",
        "en": "🔌 Disconnect",
    },
    "fbtn_refresh": {
        "it": "🔄 Ricarica",
        "en": "🔄 Refresh",
    },
    "fbtn_help": {
        "it": "❓ Aiuto",
        "en": "❓ Help",
    },
    "fbtn_quit": {
        "it": "✕ Esci",
        "en": "✕ Quit",
    },
    "fbtn_batch_dl": {
        "it": "📥 Scarica Tutti ({count})",
        "en": "📥 Download All ({count})",
    },
    "fbtn_batch_del": {
        "it": "🗑️ Elimina Tutti ({count})",
        "en": "🗑️ Delete All ({count})",
    },
    "fbtn_batch_clear": {
        "it": "✕ Annulla",
        "en": "✕ Cancel",
    },
    "batch_badge": {
        "it": " 🧺 {count} selezionati ({size}) ",
        "en": " 🧺 {count} selected ({size}) ",
    },
    "selection_cleared": {
        "it": "Selezione annullata.",
        "en": "Selection cleared.",
    },

    # -----------------------------------------------------------------
    # Disconnected Dashboard
    # -----------------------------------------------------------------
    "dash_hero_title": {
        "it": "📱 AndroidTUI — File Manager ADB",
        "en": "📱 AndroidTUI — ADB File Manager",
    },
    "dash_hero_subtitle": {
        "it": "Nessun dispositivo Android collegato",
        "en": "No Android device currently connected",
    },
    "dash_card_usb_title": {
        "it": "🔌 Connessione Via Cavo USB",
        "en": "🔌 USB Cable Connection",
    },
    "dash_card_usb_desc": {
        "it": "1. Attiva 'Debug USB' nelle Opzioni Sviluppatore.\n2. Collega il cavo al PC e autorizza la chiave RSA.",
        "en": "1. Enable 'USB Debugging' in Developer Options.\n2. Connect USB cable to PC and accept RSA prompt.",
    },
    "dash_btn_usb_detect": {
        "it": "🔍 Rileva Dispositivi USB",
        "en": "🔍 Detect USB Devices",
    },
    "dash_btn_usb_reconnect": {
        "it": "🔄 Invia Richiesta Riconnessione",
        "en": "🔄 Send Reconnect Request",
    },
    "dash_card_wifi_title": {
        "it": "📶 Connessione Wireless (WiFi)",
        "en": "📶 Wireless Connection (WiFi)",
    },
    "dash_card_wifi_desc": {
        "it": "Dispositivi recenti o aggiunta manuale IP:Porta e pairing code.",
        "en": "Recent devices or manual connection via IP:Port and pairing code.",
    },
    "dash_btn_wifi_connect": {
        "it": "📶 Connetti con IP e Porta",
        "en": "📶 Connect with IP and Port",
    },
    "dash_btn_wifi_pair": {
        "it": "🔑 Accoppia Nuovo Dispositivo (Pair)",
        "en": "🔑 Pair New Device",
    },
    "dash_card_tools_title": {
        "it": "🛠️ Diagnostica & Strumenti ADB",
        "en": "🛠️ ADB Diagnostics & Tools",
    },
    "dash_card_tools_desc": {
        "it": "Riavvia il demone ADB in caso di blocchi, o avvia una simulazione demo.",
        "en": "Restart ADB daemon if frozen, or launch full demo simulation.",
    },
    "dash_btn_restart_adb": {
        "it": "⚡ Riavvia Server ADB",
        "en": "⚡ Restart ADB Server",
    },
    "dash_btn_tcpip": {
        "it": "📡 Attiva Modalità TCP/IP 5555",
        "en": "📡 Enable TCP/IP Mode 5555",
    },
    "dash_btn_demo": {
        "it": "🎮 Avvia Modalità Demo / Simulazione",
        "en": "🎮 Launch Demo / Simulation Mode",
    },
    "dash_recent_title": {
        "it": "Dispositivi Connessi Recentemente",
        "en": "Recently Connected Devices",
    },
    "dash_btn_clear_history": {
        "it": "🗑️ Cancella Cronologia",
        "en": "🗑️ Clear History",
    },

    # -----------------------------------------------------------------
    # Modals
    # -----------------------------------------------------------------
    "modal_btn_cancel": {
        "it": "Annulla",
        "en": "Cancel",
    },
    "modal_btn_submit": {
        "it": "Conferma",
        "en": "Confirm",
    },
    "modal_btn_close": {
        "it": "Chiudi",
        "en": "Close",
    },
    "modal_btn_delete": {
        "it": "Elimina Definitivamente",
        "en": "Delete Permanently",
    },
    "modal_jump_title": {
        "it": "🚀 Navigazione Rapida Memorie & Cartelle",
        "en": "🚀 Quick Storage & Folder Navigation",
    },
    "modal_jump_desc": {
        "it": "Seleziona una posizione nota da esplorare:",
        "en": "Select a known storage location to explore:",
    },
    # Common Modal Action Buttons
    "btn_select": {
        "it": "Seleziona",
        "en": "Select",
    },
    "btn_cancel": {
        "it": "Annulla",
        "en": "Cancel",
    },
    "btn_close": {
        "it": "Chiudi",
        "en": "Close",
    },
    "btn_connect": {
        "it": "Connetti",
        "en": "Connect",
    },
    "btn_pair": {
        "it": "Accoppia",
        "en": "Pair",
    },
    "btn_scan_usb": {
        "it": "🔌 Scansiona USB",
        "en": "🔌 Scan USB",
    },
    "btn_wifi_connect": {
        "it": "📶 Connetti WiFi",
        "en": "📶 WiFi Connect",
    },
    "btn_wifi_pair": {
        "it": "🔗 Accoppia WiFi",
        "en": "🔗 WiFi Pair",
    },
    "btn_download_now": {
        "it": "Scarica Ora",
        "en": "Download Now",
    },
    "btn_upload_now": {
        "it": "Carica Ora",
        "en": "Upload Now",
    },
    "btn_create": {
        "it": "Crea",
        "en": "Create",
    },
    "btn_rename": {
        "it": "Rinomina",
        "en": "Rename",
    },
    "btn_delete_confirm": {
        "it": "Elimina Definitivamente",
        "en": "Delete Permanently",
    },
    "btn_delete_all": {
        "it": "Elimina Tutti ({count})",
        "en": "Delete All ({count})",
    },
    "btn_download_all": {
        "it": "Scarica Tutti ({count})",
        "en": "Download All ({count})",
    },
    # Device Select Modal
    "dev_select_title": {
        "it": "📱 Seleziona o Aggiungi Dispositivo Android",
        "en": "📱 Select or Add Android Device",
    },
    "dev_select_subtitle": {
        "it": "Elenco dispositivi rilevati o aggiungi una nuova connessione:",
        "en": "List of detected devices or add a new connection:",
    },
    "dev_no_devices": {
        "it": "Nessun dispositivo attualmente connesso. Collega un cavo USB o usa il WiFi.",
        "en": "No devices currently connected. Connect USB cable or use WiFi.",
    },
    "dev_add_section": {
        "it": "➕ Aggiungi Dispositivo:",
        "en": "➕ Add Device:",
    },
    # Breadcrumbs & Path Navigation Modal
    "breadcrumb_title": {
        "it": "📂 Navigazione Percorso & Sottocartelle",
        "en": "📂 Path & Subfolder Navigation",
    },
    "breadcrumb_subtitle": {
        "it": "Seleziona una cartella nel percorso attuale per saltarvi direttamente:",
        "en": "Select a folder in current path to jump directly:",
    },
    "breadcrumb_input_placeholder": {
        "it": "Inserisci o modifica percorso (es. /sdcard/Download)",
        "en": "Enter or edit path (e.g. /sdcard/Download)",
    },
    "breadcrumb_btn_go": {
        "it": "Vai",
        "en": "Go",
    },
    "breadcrumb_root": {
        "it": "Root di Sistema (/)",
        "en": "System Root (/)",
    },
}


def load_language_preference() -> str:
    """Loads saved language preference from ~/.android_tui_settings.json."""
    if not SETTINGS_FILE.exists():
        return "it"
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("language", "it")
    except Exception:
        return "it"


def save_language_preference(lang: str) -> None:
    """Saves language preference to disk."""
    data = {}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data["language"] = lang
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


_CURRENT_LANG = load_language_preference()


def get_current_language() -> str:
    return _CURRENT_LANG


def set_current_language(lang: str) -> None:
    global _CURRENT_LANG
    if lang in ("it", "en"):
        _CURRENT_LANG = lang
        save_language_preference(lang)


def toggle_language() -> str:
    global _CURRENT_LANG
    _CURRENT_LANG = "en" if _CURRENT_LANG == "it" else "it"
    save_language_preference(_CURRENT_LANG)
    return _CURRENT_LANG


def t(key: str, **kwargs) -> str:
    """Retrieves localized string for key, formatting with kwargs if provided."""
    item = TRANSLATIONS.get(key)
    if not item:
        return key
    text = item.get(_CURRENT_LANG, item.get("it", key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
