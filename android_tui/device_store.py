"""
Device store for persisting and retrieving remembered ADB devices.
Stores recent wireless and USB devices in ~/.android_tui_devices.json.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any


STORE_FILE = Path.home() / ".android_tui_devices.json"


def load_remembered_devices() -> List[Dict[str, Any]]:
    """Loads list of previously connected devices."""
    if not STORE_FILE.exists():
        return []
    try:
        with open(STORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_remembered_device(serial: str, name: str, conn_type: str = "wireless") -> None:
    """Saves or updates a remembered device in the persistent store."""
    devices = load_remembered_devices()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Update existing or append
    found = False
    for d in devices:
        if d.get("serial") == serial or (conn_type == "wireless" and d.get("ip_port") == serial):
            d["name"] = name
            d["last_seen"] = now_str
            d["type"] = conn_type
            d["ip_port"] = serial if conn_type == "wireless" else d.get("ip_port")
            found = True
            break

    if not found:
        devices.insert(
            0,
            {
                "serial": serial,
                "ip_port": serial if conn_type == "wireless" else "",
                "name": name,
                "type": conn_type,
                "last_seen": now_str,
            },
        )

    # Keep at most 10 recent devices
    devices = devices[:10]

    try:
        STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(devices, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def remove_remembered_device(serial: str) -> None:
    """Removes a remembered device from store."""
    devices = [d for d in load_remembered_devices() if d.get("serial") != serial and d.get("ip_port") != serial]
    try:
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(devices, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def clear_remembered_devices() -> None:
    """Clears all remembered devices from store."""
    try:
        if STORE_FILE.exists():
            STORE_FILE.unlink()
    except Exception:
        pass

