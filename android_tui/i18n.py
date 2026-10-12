"""
Modular Internationalization (i18n) module for AndroidTUI.
Loads translation dictionaries dynamically from separate JSON files in android_tui/locales/
allowing seamless addition of new languages (e.g. it.json, en.json, es.json, etc.).
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

LOCALES_DIR = Path(__file__).resolve().parent / "locales"
SETTINGS_FILE = Path.home() / ".android_tui_settings.json"

_CURRENT_LANG = "it"
_LOCALES: Dict[str, Dict[str, str]] = {}


def _load_locales() -> None:
    """Loads all translation dictionary files from the locales directory."""
    global _LOCALES
    _LOCALES.clear()

    if not LOCALES_DIR.exists():
        LOCALES_DIR.mkdir(parents=True, exist_ok=True)

    for json_file in sorted(LOCALES_DIR.glob("*.json")):
        lang_code = json_file.stem.lower()
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _LOCALES[lang_code] = data
        except Exception as e:
            print(f"[i18n] Errore caricamento locale {json_file.name}: {e}")

    # Fallback minimal dictionary if locales directory is missing or empty
    if not _LOCALES:
        _LOCALES["it"] = {"app_title": "AndroidTUI", "ready": "Pronto."}
        _LOCALES["en"] = {"app_title": "AndroidTUI", "ready": "Ready."}


def get_available_languages() -> List[str]:
    """Returns list of supported language codes found in locales/."""
    if not _LOCALES:
        _load_locales()
    return list(_LOCALES.keys())


def load_saved_language() -> str:
    """Reads saved language from persistent settings file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("language")
                if lang and lang in get_available_languages():
                    return lang
        except Exception:
            pass
    return "it"


def save_language(lang: str) -> None:
    """Saves language choice to persistent settings file."""
    try:
        data = {}
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["language"] = lang
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def set_language(lang: str) -> None:
    """Sets active language and persists choice."""
    global _CURRENT_LANG
    avail = get_available_languages()
    if lang in avail:
        _CURRENT_LANG = lang
    elif "en" in avail:
        _CURRENT_LANG = "en"
    elif avail:
        _CURRENT_LANG = avail[0]
    save_language(_CURRENT_LANG)


def get_current_language() -> str:
    """Returns active language code (e.g. 'it' or 'en')."""
    return _CURRENT_LANG


def get_language_name(lang: Optional[str] = None) -> str:
    """Returns human-readable name of specified or current language from its locale dictionary."""
    if not _LOCALES:
        _load_locales()
    target_lang = lang or _CURRENT_LANG
    lang_dict = _LOCALES.get(target_lang, {})
    if "lang_name" in lang_dict:
        return lang_dict["lang_name"]
    defaults = {
        "it": "Italiano (IT)",
        "en": "English (EN)",
        "es": "Español (ES)",
        "fr": "Français (FR)",
        "de": "Deutsch (DE)",
    }
    return defaults.get(target_lang, target_lang.upper())


def toggle_language() -> str:
    """Cycles through all available languages and returns new active code."""
    avail = get_available_languages()
    if not avail:
        return _CURRENT_LANG
    try:
        curr_idx = avail.index(_CURRENT_LANG)
        next_idx = (curr_idx + 1) % len(avail)
        new_lang = avail[next_idx]
    except ValueError:
        new_lang = avail[0]

    set_language(new_lang)
    return new_lang


def t(key: str, **kwargs) -> str:
    """
    Translates key using active language dictionary with English/key fallback.
    Interpolates any **kwargs into formatted string.
    """
    if not _LOCALES:
        _load_locales()

    curr_dict = _LOCALES.get(_CURRENT_LANG, {})
    template = curr_dict.get(key)

    if template is None:
        # Fallback to English dictionary
        en_dict = _LOCALES.get("en", {})
        template = en_dict.get(key)

    if template is None:
        # Fallback to Italian dictionary
        it_dict = _LOCALES.get("it", {})
        template = it_dict.get(key)

    if template is None:
        return key

    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    return template


# Initialize locales on module import
_load_locales()
_CURRENT_LANG = load_saved_language()
