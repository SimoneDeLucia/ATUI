"""
Data models for AndroidTUI.
Represents devices, file entries, categories, and connection states.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConnectionType(str, Enum):
    USB = "usb"
    WIRELESS = "wireless"
    DEMO = "demo"
    UNKNOWN = "unknown"


class DeviceState(str, Enum):
    DEVICE = "device"
    UNAUTHORIZED = "unauthorized"
    OFFLINE = "offline"
    RECOVERY = "recovery"
    DISCONNECTED = "disconnected"


class FileCategory(str, Enum):
    FOLDER = "folder"
    ARCHIVE = "archive"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    CODE = "code"
    APK = "apk"
    SYSTEM = "system"
    DEFAULT = "default"


@dataclass
class AdbDevice:
    serial: str
    state: DeviceState = DeviceState.DEVICE
    connection_type: ConnectionType = ConnectionType.USB
    model: str = "Android Device"
    brand: str = ""
    android_version: str = ""
    sdk_version: str = ""
    battery_level: Optional[int] = None
    battery_status: str = "Unknown"
    storage_free: str = ""
    storage_total: str = ""
    sdcard_path: str = "/sdcard"
    ext_sd_path: Optional[str] = None
    ext_sd_free: Optional[str] = None
    ext_sd_total: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None

    @property
    def display_name(self) -> str:
        name = f"{self.brand} {self.model}".strip()
        if not name:
            name = self.serial
        return name

    @property
    def is_ready(self) -> bool:
        return self.state == DeviceState.DEVICE


@dataclass
class FileEntry:
    name: str
    path: str
    is_dir: bool = False
    size: int = 0
    permissions: str = ""
    date_str: str = ""
    is_symlink: bool = False
    link_target: str = ""
    category: FileCategory = FileCategory.DEFAULT

    @property
    def formatted_size(self) -> str:
        if self.is_dir:
            return "<DIR>"
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.2f} GB"

    @property
    def extension(self) -> str:
        if self.is_dir or "." not in self.name:
            return ""
        return self.name.rsplit(".", 1)[-1].lower()


@dataclass
class TransferProgress:
    filename: str
    bytes_transferred: int = 0
    total_bytes: int = 0
    percentage: float = 0.0
    speed: str = ""
    is_done: bool = False
    error: Optional[str] = None
