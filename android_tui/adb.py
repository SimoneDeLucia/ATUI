"""
ADB Engine and File System Manager for AndroidTUI.
Wraps ADB CLI commands safely, parses device states and directory listings,
and supports USB and Wireless ADB pairing/connection.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from .models import (
    AdbDevice,
    ConnectionType,
    DeviceState,
    FileEntry,
    FileCategory,
)
from .theme import categorize_entry


DEFAULT_ADB_CANDIDATES = [
    r"C:\platform-tools\adb.exe",
    r"C:\ProgramData\chocolatey\bin\adb.exe",
    r"C:\Android\platform-tools\adb.exe",
    os.path.expanduser(r"~\AppData\Local\Android\Sdk\platform-tools\adb.exe"),
    "/usr/bin/adb",
    "/usr/local/bin/adb",
    "/snap/bin/adb",
    os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
    os.path.expanduser("~/.android-sdk/platform-tools/adb"),
]

DEFAULT_SCRCPY_CANDIDATES = [
    r"C:\platform-tools\scrcpy.exe",
    r"C:\scrcpy\scrcpy.exe",
    r"C:\Program Files\scrcpy\scrcpy.exe",
    os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy.exe"),
    "/usr/bin/scrcpy",
    "/usr/local/bin/scrcpy",
    "/snap/bin/scrcpy",
    "/opt/scrcpy/scrcpy",
]


def resolve_scrcpy_path() -> Optional[str]:
    """Resolves the scrcpy executable path across Windows and Linux systems."""
    which_scrcpy = shutil.which("scrcpy")
    if which_scrcpy:
        return which_scrcpy
    for candidate in DEFAULT_SCRCPY_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return None



class AdbManager:
    def __init__(self, custom_adb_path: Optional[str] = None):
        self.adb_path = self._resolve_adb_path(custom_adb_path)
        self.active_device: Optional[AdbDevice] = None
        self.demo_mode: bool = False
        self._demo_fs = self._init_demo_fs()

    def _resolve_adb_path(self, custom_path: Optional[str] = None) -> str:
        if custom_path and os.path.isfile(custom_path):
            return custom_path
        
        which_adb = shutil.which("adb")
        if which_adb:
            return which_adb
            
        for candidate in DEFAULT_ADB_CANDIDATES:
            if os.path.isfile(candidate):
                return candidate
                
        return "adb"

    def run_cmd(
        self,
        args: List[str],
        timeout: int = 15,
        target_serial: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        cmd = [self.adb_path]
        serial = target_serial or (self.active_device.serial if self.active_device and not self.demo_mode else None)
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(args)

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout scaduto durante l'esecuzione del comando ADB."
        except Exception as e:
            return -2, "", str(e)

    # -------------------------------------------------------------
    # Device Management
    # -------------------------------------------------------------
    def get_devices(self) -> List[AdbDevice]:
        if self.demo_mode:
            return [
                AdbDevice(
                    serial="demo-pixel-8",
                    state=DeviceState.DEVICE,
                    connection_type=ConnectionType.DEMO,
                    model="Pixel 8 Pro (Demo Mode)",
                    brand="Google",
                    android_version="14",
                    sdk_version="34",
                    battery_level=88,
                    battery_status="In carica",
                    storage_free="64.5 GB",
                    storage_total="128 GB",
                    sdcard_path="/sdcard",
                    ext_sd_path="/storage/1F2A-3B4C",
                    ext_sd_free="112 GB",
                    ext_sd_total="128 GB",
                )
            ]

        code, stdout, stderr = self.run_cmd(["devices", "-l"], timeout=8)
        devices: List[AdbDevice] = []
        if code != 0:
            return devices

        for line in stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            serial = parts[0]
            raw_state = parts[1].lower()

            state = DeviceState.DEVICE
            if raw_state == "unauthorized":
                state = DeviceState.UNAUTHORIZED
            elif raw_state == "offline":
                state = DeviceState.OFFLINE
            elif raw_state == "recovery":
                state = DeviceState.RECOVERY
            elif raw_state != "device":
                state = DeviceState.DISCONNECTED

            # Determine connection type
            conn_type = ConnectionType.WIRELESS if ":" in serial else ConnectionType.USB

            # Extract model/product if present
            model = "Android Device"
            brand = ""
            for p in parts[2:]:
                if p.startswith("model:"):
                    model = p.split(":", 1)[1].replace("_", " ")
                elif p.startswith("product:"):
                    brand = p.split(":", 1)[1]

            ip = serial.split(":")[0] if conn_type == ConnectionType.WIRELESS else None
            port = int(serial.split(":")[1]) if conn_type == ConnectionType.WIRELESS and ":" in serial else None

            dev = AdbDevice(
                serial=serial,
                state=state,
                connection_type=conn_type,
                model=model,
                brand=brand,
                ip_address=ip,
                port=port,
            )

            # If device is authorized and active, enrich details
            if state == DeviceState.DEVICE:
                self._enrich_device_info(dev)

            devices.append(dev)

        return devices

    def _enrich_device_info(self, dev: AdbDevice) -> None:
        # Get brand & model
        code, out, _ = self.run_cmd(["shell", "getprop", "ro.product.brand"], target_serial=dev.serial)
        if code == 0 and out.strip():
            dev.brand = out.strip().capitalize()

        code, out, _ = self.run_cmd(["shell", "getprop", "ro.product.model"], target_serial=dev.serial)
        if code == 0 and out.strip():
            dev.model = out.strip()

        # Android version
        code, out, _ = self.run_cmd(["shell", "getprop", "ro.build.version.release"], target_serial=dev.serial)
        if code == 0 and out.strip():
            dev.android_version = out.strip()

        code, out, _ = self.run_cmd(["shell", "getprop", "ro.build.version.sdk"], target_serial=dev.serial)
        if code == 0 and out.strip():
            dev.sdk_version = out.strip()

        # Battery
        code, out, _ = self.run_cmd(["shell", "dumpsys", "battery"], target_serial=dev.serial)
        if code == 0:
            for raw_line in out.splitlines():
                line = raw_line.strip()
                if line.startswith("level:"):
                    try:
                        dev.battery_level = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith("status:"):
                    status_code = line.split(":", 1)[1].strip()
                    if status_code == "2":
                        dev.battery_status = "In carica"
                    elif status_code == "3":
                        dev.battery_status = "In scarica"
                    elif status_code == "5":
                        dev.battery_status = "Carica completa"


        # Storage: Internal /sdcard
        code, out, _ = self.run_cmd(["shell", "df", "-h", "/sdcard"], target_serial=dev.serial)
        if code == 0:
            lines = [l for l in out.splitlines() if l.strip()]
            if len(lines) >= 2:
                cols = lines[-1].split()
                if len(cols) >= 4:
                    dev.storage_total = cols[1]
                    dev.storage_free = cols[3]

        # Storage: External MicroSD / USB OTG in /storage/
        code_sd, out_sd, _ = self.run_cmd(["shell", "ls", "-d", "/storage/*"], target_serial=dev.serial)
        if code_sd == 0:
            for item in out_sd.splitlines():
                path = item.strip()
                name = path.rstrip("/").split("/")[-1]
                if name and name not in ("emulated", "self", "knox-emulated") and not name.startswith("."):
                    dev.ext_sd_path = path
                    code_df, out_df, _ = self.run_cmd(["shell", "df", "-h", path], target_serial=dev.serial)
                    if code_df == 0:
                        df_lines = [l for l in out_df.splitlines() if l.strip()]
                        if len(df_lines) >= 2:
                            df_cols = df_lines[-1].split()
                            if len(df_cols) >= 4:
                                dev.ext_sd_total = df_cols[1]
                                dev.ext_sd_free = df_cols[3]
                    break

    def set_active_device(self, device: Optional[AdbDevice]) -> None:
        self.active_device = device
        if device and device.connection_type == ConnectionType.DEMO:
            self.demo_mode = True
        elif device:
            self.demo_mode = False

    def restart_server(self) -> Tuple[bool, str]:
        code, out, err = self.run_cmd(["kill-server"], timeout=10)
        code2, out2, err2 = self.run_cmd(["start-server"], timeout=10)
        if code2 == 0:
            return True, "Server ADB riavviato con successo."
        return False, f"Errore riavvio server: {err2 or out2}"

    def reconnect_devices(self) -> Tuple[bool, str]:
        code, out, err = self.run_cmd(["reconnect", "offline"], timeout=5)
        self.run_cmd(["reconnect"], timeout=5)
        return True, "Richiesta riconnessione inviata ai dispositivi."

    # -------------------------------------------------------------
    # Wireless Connections
    # -------------------------------------------------------------
    def wireless_pair(self, ip_port: str, pairing_code: str) -> Tuple[bool, str]:
        if not ip_port or not pairing_code:
            return False, "IP:Porta e Codice di accoppiamento sono obbligatori."
        code, out, err = self.run_cmd(["pair", ip_port.strip(), pairing_code.strip()], timeout=15)
        if code == 0 and "successfully" in out.lower():
            return True, f"Accoppiato con successo a {ip_port}!"
        return False, out.strip() or err.strip() or "Accoppiamento fallito."

    def wireless_connect(self, ip_port: str) -> Tuple[bool, str]:
        if not ip_port:
            return False, "Specificare IP:Porta (es. 192.168.1.50:5555)."
        if ":" not in ip_port:
            ip_port = f"{ip_port}:5555"
        code, out, err = self.run_cmd(["connect", ip_port.strip()], timeout=15)
        if code == 0 and ("connected" in out.lower() or "already connected" in out.lower()):
            return True, f"Connesso con successo a {ip_port}!"
        return False, out.strip() or err.strip() or f"Impossibile connettersi a {ip_port}."

    def wireless_disconnect(self, ip_port: str) -> Tuple[bool, str]:
        code, out, err = self.run_cmd(["disconnect", ip_port.strip()], timeout=5)
        return code == 0, out.strip() or err.strip()

    def enable_tcpip_mode(self, port: int = 5555) -> Tuple[bool, str]:
        code, out, err = self.run_cmd(["tcpip", str(port)], timeout=10)
        if code == 0:
            return True, f"Modalità TCP/IP avviata sulla porta {port}. Ora puoi connetterti wireless!"
        return False, err.strip() or out.strip()

    # -------------------------------------------------------------
    # File Operations
    # -------------------------------------------------------------
    def list_directory(self, path: str) -> Tuple[List[FileEntry], Optional[str]]:
        if self.demo_mode:
            return self._demo_list_dir(path)

        clean_path = path.rstrip("/")
        if not clean_path:
            clean_path = "/"

        # Append '/' when listing directories/symlinks so ls enters them
        target_path = f"{clean_path}/" if clean_path != "/" else "/"

        code, stdout, stderr = self.run_cmd(["shell", f"ls -la -p '{target_path}'"], timeout=15)
        if code != 0:
            return [], stderr.strip() or "Impossibile leggere la cartella (permessi insufficienti o percorso inesistente)."

        entries: List[FileEntry] = []
        clean_parent = clean_path

        for line in stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("total "):
                continue

            # Handle SELinux restricted lines: 'd????????? ? ? ? ? ? name'
            if line.startswith(("d?", "l?", "-?", "?")):
                parts = line.split()
                if len(parts) >= 2:
                    name_raw = parts[-1]
                    if "->" in parts:
                        idx = parts.index("->")
                        name_raw = parts[idx - 1]
                    name = name_raw.rstrip("/")
                    if name in (".", "..", "?"):
                        continue
                    is_dir = line.startswith("d") or name_raw.endswith("/")
                    item_path = f"{clean_parent}/{name}".replace("//", "/")
                    entries.append(
                        FileEntry(
                            name=name,
                            path=item_path,
                            is_dir=is_dir,
                            size=0,
                            permissions="SELinux protetto",
                            category=FileCategory.FOLDER if is_dir else FileCategory.DEFAULT,
                        )
                    )
                continue

            # Robust date & time regex pattern matching standard Android ls
            m = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}|\b[A-Za-z]{3}\s+\d+\s+[\d:]{4,5}|\?\s+\?)\s+(.+)$", line)
            if not m:
                continue

            date_str = m.group(1)
            name_raw = m.group(2).strip()
            prefix = line[:m.start()].split()
            if not prefix:
                continue

            perms = prefix[0]
            size = 0
            if len(prefix) >= 5:
                try:
                    size = int(prefix[4])
                except ValueError:
                    size = 0

            is_symlink = perms.startswith("l") or " -> " in name_raw
            link_target = ""
            if " -> " in name_raw:
                name, link_target = name_raw.split(" -> ", 1)
                name = name.strip().rstrip("/")
                link_target = link_target.strip()
            else:
                name = name_raw.rstrip("/")

            if name in (".", ".."):
                continue

            is_dir = perms.startswith("d") or name_raw.endswith("/")
            # If symlink points to a directory, treat as directory
            if is_symlink:
                if (
                    name in ("sdcard", "bin", "etc", "bugreports", "d", "self", "primary")
                    or link_target.endswith("/")
                    or "/storage" in link_target
                    or "/system" in link_target
                ):
                    is_dir = True

            item_path = f"{clean_parent}/{name}".replace("//", "/")
            cat = FileCategory.FOLDER if is_dir else categorize_entry(name, is_dir)

            entries.append(
                FileEntry(
                    name=name,
                    path=item_path,
                    is_dir=is_dir,
                    size=size,
                    permissions=perms,
                    date_str=date_str if date_str != "? ?" else "—",
                    is_symlink=is_symlink,
                    link_target=link_target,
                    category=cat,
                )
            )

        # Sort: directories first, then alphabetical case-insensitive
        entries.sort(key=lambda x: (not x.is_dir, x.name.lower()))
        return entries, None

    def read_text_preview(self, path: str, max_bytes: int = 15000) -> Tuple[str, bool]:
        if self.demo_mode:
            return self._demo_read_preview(path)

        code, out, err = self.run_cmd(["shell", f"head -c {max_bytes} '{path}'"], timeout=10)
        if code == 0:
            is_truncated = len(out) >= max_bytes
            return out, is_truncated
        return "File non visualizzabile come testo.", False

    def pull_file(self, remote_path: str, local_dest: str, target_serial: Optional[str] = None) -> Tuple[bool, str]:
        """Pulls file or folder from Phone to PC using 'adb pull'"""
        if self.demo_mode:
            target_file = local_dest
            if os.path.isdir(local_dest) or local_dest.endswith(("/", "\\")):
                fname = os.path.basename(remote_path)
                target_file = os.path.join(local_dest, fname)
            os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)
            demo_content, _ = self.read_text_preview(remote_path)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(demo_content)
            return True, f"File trasferito con successo (Demo) in {target_file}"

        if local_dest.endswith(("/", "\\")) or (os.path.exists(local_dest) and os.path.isdir(local_dest)):
            os.makedirs(local_dest, exist_ok=True)
        else:
            parent = os.path.dirname(local_dest)
            if parent:
                os.makedirs(parent, exist_ok=True)
        code, out, err = self.run_cmd(["pull", remote_path, local_dest], timeout=120, target_serial=target_serial)
        if code == 0:
            return True, out.strip() or f"File trasferito con successo in {local_dest}"
        return False, err.strip() or out.strip() or "Errore durante il download dal telefono."

    def push_file(self, local_src: str, remote_dest_dir: str, target_serial: Optional[str] = None) -> Tuple[bool, str]:
        """Pushes file or folder from PC to Phone using 'adb push'"""
        local_src = local_src.strip().strip('"\'')
        if not os.path.exists(local_src):
            return False, f"File locale non trovato: {local_src}"

        if self.demo_mode:
            fname = os.path.basename(local_src)
            is_dir = os.path.isdir(local_src)
            cat = FileCategory.FOLDER if is_dir else FileCategory.DEFAULT
            size = os.path.getsize(local_src) if not is_dir else 0
            entry = FileEntry(
                name=fname,
                path=f"{remote_dest_dir.rstrip('/')}/{fname}",
                is_dir=is_dir,
                size=size,
                category=cat,
            )
            self._demo_fs.setdefault(remote_dest_dir, []).append(entry)
            return True, f"Caricato con successo in {remote_dest_dir} (Demo)"

        code, out, err = self.run_cmd(["push", local_src, remote_dest_dir], timeout=120, target_serial=target_serial)
        if code == 0:
            return True, out.strip() or f"Caricato con successo in {remote_dest_dir}"
        return False, err.strip() or out.strip() or "Errore durante il caricamento sul telefono."

    def create_directory(self, parent_path: str, folder_name: str) -> Tuple[bool, str]:
        target = f"{parent_path.rstrip('/')}/{folder_name.strip()}"
        if self.demo_mode:
            self._demo_fs.setdefault(parent_path, []).append(
                FileEntry(name=folder_name, path=target, is_dir=True, category=FileCategory.FOLDER)
            )
            self._demo_fs[target] = []
            return True, f"Cartella '{folder_name}' creata."

        code, out, err = self.run_cmd(["shell", f"mkdir -p '{target}'"], timeout=10)
        if code == 0:
            return True, f"Cartella '{folder_name}' creata con successo."
        return False, err.strip() or "Errore durante la creazione della cartella."

    def rename_entry(self, old_path: str, new_name: str) -> Tuple[bool, str]:
        parent = os.path.dirname(old_path)
        new_path = f"{parent}/{new_name.strip()}"
        if self.demo_mode:
            return True, f"Rinominato in '{new_name}' (Demo)."

        code, out, err = self.run_cmd(["shell", f"mv '{old_path}' '{new_path}'"], timeout=10)
        if code == 0:
            return True, f"Elemento rinominato in '{new_name}'."
        return False, err.strip() or "Errore durante la ridenominazione."

    def delete_entry(self, target_path: str) -> Tuple[bool, str]:
        # Guard against accidental root deletion
        if target_path in ("/", "/sdcard", "/storage", "/storage/emulated/0", "/system", "/data"):
            return False, "Operazione non consentita sulle directory di sistema di base!"

        if self.demo_mode:
            return True, f"Elemento rimosso (Demo): {target_path}"

        code, out, err = self.run_cmd(["shell", f"rm -rf '{target_path}'"], timeout=20)
        if code == 0:
            return True, f"Elemento eliminato: {os.path.basename(target_path)}"
        return False, err.strip() or "Errore durante l'eliminazione."

    # -------------------------------------------------------------
    # Demo Virtual File System
    # -------------------------------------------------------------
    def _init_demo_fs(self) -> Dict[str, List[FileEntry]]:
        fs: Dict[str, List[FileEntry]] = {}
        
        # /sdcard root
        fs["/sdcard"] = [
            FileEntry("Download", "/sdcard/Download", is_dir=True, category=FileCategory.FOLDER, permissions="drwxrwx--x"),
            FileEntry("DCIM", "/sdcard/DCIM", is_dir=True, category=FileCategory.FOLDER, permissions="drwxrwx--x"),
            FileEntry("Pictures", "/sdcard/Pictures", is_dir=True, category=FileCategory.FOLDER, permissions="drwxrwx--x"),
            FileEntry("Documents", "/sdcard/Documents", is_dir=True, category=FileCategory.FOLDER, permissions="drwxrwx--x"),
            FileEntry("Music", "/sdcard/Music", is_dir=True, category=FileCategory.FOLDER, permissions="drwxrwx--x"),
            FileEntry("Movies", "/sdcard/Movies", is_dir=True, category=FileCategory.FOLDER, permissions="drwxrwx--x"),
            FileEntry("backup_contacts.vcf", "/sdcard/backup_contacts.vcf", is_dir=False, size=15420, category=FileCategory.DOCUMENT, permissions="-rw-rw----"),
            FileEntry("device_info.json", "/sdcard/device_info.json", is_dir=False, size=3280, category=FileCategory.CODE, permissions="-rw-rw----"),
        ]

        # /sdcard/Download
        fs["/sdcard/Download"] = [
            FileEntry("Termux_v0.118.apk", "/sdcard/Download/Termux_v0.118.apk", is_dir=False, size=104857600, category=FileCategory.APK, permissions="-rw-rw----"),
            FileEntry("report_annual_2026.pdf", "/sdcard/Download/report_annual_2026.pdf", is_dir=False, size=4512000, category=FileCategory.DOCUMENT, permissions="-rw-rw----"),
            FileEntry("kernel_patch.zip", "/sdcard/Download/kernel_patch.zip", is_dir=False, size=84300000, category=FileCategory.ARCHIVE, permissions="-rw-rw----"),
            FileEntry("config_vpn.ovpn", "/sdcard/Download/config_vpn.ovpn", is_dir=False, size=2450, category=FileCategory.CODE, permissions="-rw-rw----"),
            FileEntry("podcast_ep42.mp3", "/sdcard/Download/podcast_ep42.mp3", is_dir=False, size=52428800, category=FileCategory.AUDIO, permissions="-rw-rw----"),
        ]

        # /sdcard/DCIM
        fs["/sdcard/DCIM"] = [
            FileEntry("Camera", "/sdcard/DCIM/Camera", is_dir=True, category=FileCategory.FOLDER, permissions="drwxrwx--x"),
            FileEntry("Screenshots", "/sdcard/DCIM/Screenshots", is_dir=True, category=FileCategory.FOLDER, permissions="drwxrwx--x"),
        ]

        # /sdcard/DCIM/Camera
        fs["/sdcard/DCIM/Camera"] = [
            FileEntry("IMG_20261012_142010.jpg", "/sdcard/DCIM/Camera/IMG_20261012_142010.jpg", is_dir=False, size=5240000, category=FileCategory.IMAGE, permissions="-rw-rw----"),
            FileEntry("IMG_20261012_142022.jpg", "/sdcard/DCIM/Camera/IMG_20261012_142022.jpg", is_dir=False, size=4890000, category=FileCategory.IMAGE, permissions="-rw-rw----"),
            FileEntry("VID_20261012_143000.mp4", "/sdcard/DCIM/Camera/VID_20261012_143000.mp4", is_dir=False, size=189400000, category=FileCategory.VIDEO, permissions="-rw-rw----"),
        ]

        return fs

    def _demo_list_dir(self, path: str) -> Tuple[List[FileEntry], Optional[str]]:
        clean = path.rstrip("/") or "/sdcard"
        if clean in self._demo_fs:
            return list(self._demo_fs[clean]), None
        return [], None

    def _demo_read_preview(self, path: str) -> Tuple[str, bool]:
        if path.endswith(".json"):
            return '{\n  "device": "Pixel 8 Pro",\n  "brand": "Google",\n  "android": "14",\n  "status": "Online (Demo)",\n  "adb_bridge": "Antigravity ADB TUI"\n}', False
        elif path.endswith(".ovpn"):
            return "client\ndev tun\nproto udp\nremote vpn.example.com 1194\nresolv-retry infinite\nnobind\npersist-key\npersist-tun\nca ca.crt\ncert client.crt\nkey client.key\nverb 3", False
        return f"File binario o multimediale: {os.path.basename(path)}\nDimensione stimata sul dispositivo.", False
