"""
LocalSend Protocol v2 Discovery & Persistent Connection Engine for ATUI.
Implements:
1. UDP Multicast (224.0.0.167:53317) and Broadcast discovery compliant with LocalSend protocol v2/v1.
2. Lightweight embedded HTTP server (/api/localsend/v2/register, /api/localsend/v2/info).
3. Persistent connection heartbeat monitor with automatic reconnection and latency tracking.
4. Seamless ADB Wireless bridge connecting discovered Android devices to ATUI.
"""
import os
import sys
import time
import json
import uuid
import socket
import struct
import platform
import threading
from dataclasses import dataclass, field, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List, Optional, Callable, Any, Tuple
import urllib.request
import urllib.error

LOCALSEND_MULTICAST_GROUP = "224.0.0.167"
LOCALSEND_PORT = 53317
PROTOCOL_VERSION = "2.0"


@dataclass
class LocalSendDevice:
    """Represents a device discovered or connected via LocalSend protocol."""
    ip: str
    port: int = LOCALSEND_PORT
    alias: str = "Unknown Device"
    device_model: str = "Android Device"
    device_type: str = "mobile"  # 'mobile', 'desktop', 'web', 'headless', 'server'
    fingerprint: str = ""
    protocol: str = "http"
    version: str = PROTOCOL_VERSION
    last_seen: float = field(default_factory=time.time)
    latency_ms: float = -1.0
    is_persistent: bool = False
    connection_status: str = "DISCONNECTED"  # DISCONNECTED, CONNECTING, CONNECTED, OFFLINE
    adb_status: str = "DISCONNECTED"  # DISCONNECTED, CONNECTED, FAILED

    @property
    def id(self) -> str:
        return self.fingerprint or f"{self.ip}:{self.port}"

    @property
    def display_name(self) -> str:
        icon = "📱" if self.device_type == "mobile" else "💻"
        return f"{icon} {self.alias} ({self.device_model})"

    def to_dict(self) -> dict:
        return asdict(self)


class LocalSendDiscovery:
    """
    Handles network discovery using the LocalSend Protocol:
    - UDP Multicast on 224.0.0.167:53317
    - UDP Broadcast on 255.255.255.255:53317
    - HTTP registration server on port 53317
    """

    def __init__(
        self,
        alias: Optional[str] = None,
        device_model: Optional[str] = None,
        device_type: str = "desktop",
        port: int = LOCALSEND_PORT,
    ):
        self.port = port
        self.device_type = device_type
        self.alias = alias or f"ATUI-{platform.node() or 'PC'}"
        self.device_model = device_model or f"{platform.system()} ({platform.machine()})"
        self.fingerprint = f"atui-{uuid.uuid4().hex[:12]}"

        self.discovered_devices: Dict[str, LocalSendDevice] = {}
        self._callbacks: List[Callable[[LocalSendDevice], None]] = []

        self._running = False
        self._threads: List[threading.Thread] = []
        self._lock = threading.RLock()
        self._http_server: Optional[HTTPServer] = None
        self._actual_http_port = port

    def register_callback(self, callback: Callable[[LocalSendDevice], None]) -> None:
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[LocalSendDevice], None]) -> None:
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def _notify_callbacks(self, device: LocalSendDevice) -> None:
        callbacks = list(self._callbacks)
        for cb in callbacks:
            try:
                cb(device)
            except Exception:
                pass

    def build_announcement_payload(self) -> dict:
        """Constructs the LocalSend JSON announcement datagram."""
        return {
            "alias": self.alias,
            "version": PROTOCOL_VERSION,
            "deviceModel": self.device_model,
            "deviceType": self.device_type,
            "fingerprint": self.fingerprint,
            "port": self._actual_http_port,
            "protocol": "http",
            "download": False,
            "announcement": True,
            "announce": True,
        }

    def start(self) -> None:
        """Starts the discovery services: Multicast UDP, Broadcast UDP, and HTTP API server."""
        if self._running:
            return
        self._running = True

        # 1. Start HTTP Server for peer registration & info
        http_thread = threading.Thread(target=self._run_http_server, daemon=True, name="LocalSend-HTTP")
        http_thread.start()
        self._threads.append(http_thread)

        # 2. Start Multicast UDP Listener
        mcast_thread = threading.Thread(target=self._run_multicast_listener, daemon=True, name="LocalSend-Mcast")
        mcast_thread.start()
        self._threads.append(mcast_thread)

        # 3. Start Broadcast UDP Listener
        bcast_thread = threading.Thread(target=self._run_broadcast_listener, daemon=True, name="LocalSend-Bcast")
        bcast_thread.start()
        self._threads.append(bcast_thread)

        # 4. Send initial announcement beacon
        threading.Thread(target=self._initial_announcements, daemon=True).start()

    def _initial_announcements(self) -> None:
        # Give sockets 200ms to bind, then announce
        time.sleep(0.2)
        self.send_announcement()
        time.sleep(1.0)
        self.send_announcement()

    def stop(self) -> None:
        """Stops all network discovery listeners and servers."""
        self._running = False
        if self._http_server:
            try:
                self._http_server.shutdown()
            except Exception:
                pass

    def send_announcement(self) -> None:
        """Broadcasts announcement packet over UDP multicast and broadcast."""
        payload = json.dumps(self.build_announcement_payload()).encode("utf-8")

        # 1. UDP Multicast
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", 2))
            sock.sendto(payload, (LOCALSEND_MULTICAST_GROUP, self.port))
            sock.close()
        except Exception:
            pass

        # 2. UDP Broadcast
        try:
            b_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            b_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            b_sock.sendto(payload, ("255.255.255.255", self.port))
            b_sock.close()
        except Exception:
            pass

    def _handle_peer_payload(self, raw_data: bytes, sender_ip: str) -> Optional[LocalSendDevice]:
        """Parses and handles discovery payload received from a network peer."""
        try:
            data = json.loads(raw_data.decode("utf-8"))
        except Exception:
            return None

        peer_fingerprint = data.get("fingerprint", "")
        # Ignore our own packets
        if peer_fingerprint == self.fingerprint:
            return None

        peer_alias = data.get("alias") or f"Device-{sender_ip}"
        peer_model = data.get("deviceModel") or "Android Device"
        peer_type = data.get("deviceType") or "mobile"
        peer_port = int(data.get("port") or LOCALSEND_PORT)
        peer_protocol = data.get("protocol") or "http"
        peer_version = data.get("version") or PROTOCOL_VERSION

        device_key = peer_fingerprint or sender_ip
        with self._lock:
            existing = self.discovered_devices.get(device_key)
            if existing:
                existing.ip = sender_ip
                existing.port = peer_port
                existing.alias = peer_alias
                existing.device_model = peer_model
                existing.device_type = peer_type
                existing.last_seen = time.time()
                device = existing
            else:
                device = LocalSendDevice(
                    ip=sender_ip,
                    port=peer_port,
                    alias=peer_alias,
                    device_model=peer_model,
                    device_type=peer_type,
                    fingerprint=peer_fingerprint,
                    protocol=peer_protocol,
                    version=peer_version,
                    last_seen=time.time(),
                )
                self.discovered_devices[device_key] = device

        self._notify_callbacks(device)
        return device

    def _run_multicast_listener(self) -> None:
        """Listens for UDP multicast announcements on 224.0.0.167:53317."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except Exception:
                    pass

            # Bind to multicast port
            if sys.platform == "win32":
                sock.bind(("", self.port))
            else:
                sock.bind((LOCALSEND_MULTICAST_GROUP, self.port))

            mreq = struct.pack("4sl", socket.inet_aton(LOCALSEND_MULTICAST_GROUP), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.settimeout(1.0)
        except Exception:
            return

        while self._running:
            try:
                data, addr = sock.recvfrom(4096)
                if data:
                    self._handle_peer_payload(data, addr[0])
            except socket.timeout:
                continue
            except Exception:
                if not self._running:
                    break
                time.sleep(0.5)

        try:
            sock.close()
        except Exception:
            pass

    def _run_broadcast_listener(self) -> None:
        """Listens for UDP broadcast packets on port 53317."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("", self.port))
            sock.settimeout(1.0)
        except Exception:
            return

        while self._running:
            try:
                data, addr = sock.recvfrom(4096)
                if data:
                    self._handle_peer_payload(data, addr[0])
            except socket.timeout:
                continue
            except Exception:
                if not self._running:
                    break
                time.sleep(0.5)

        try:
            sock.close()
        except Exception:
            pass

    def _run_http_server(self) -> None:
        """Runs the embedded HTTP server handling /api/localsend/v2/register and /api/localsend/v2/info."""
        parent = self

        class LocalSendHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress console logging

            def do_GET(self):
                if self.path.startswith("/api/localsend/v2/info") or self.path.startswith("/api/localsend/v1/info"):
                    payload = json.dumps(parent.build_announcement_payload()).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                elif self.path.startswith("/api/atui/v1/ping"):
                    res = json.dumps({"status": "pong", "time": time.time(), "alias": parent.alias}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(res)
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                if self.path.startswith("/api/localsend/v2/register") or self.path.startswith("/api/localsend/v1/register"):
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length) if content_length > 0 else b""
                    client_ip = self.client_address[0]
                    parent._handle_peer_payload(body, client_ip)

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()

        # Try binding default port or find an available one
        ports_to_try = [self.port, self.port + 1, self.port + 2, 0]
        for p in ports_to_try:
            try:
                server = HTTPServer(("0.0.0.0", p), LocalSendHandler)
                self._http_server = server
                self._actual_http_port = server.server_port
                break
            except Exception:
                continue

        if not self._http_server:
            return

        try:
            self._http_server.serve_forever()
        except Exception:
            pass


class PersistentConnectionManager:
    """
    Manages persistent connection sessions between ATUI on PC and an Android phone:
    - Maintains heartbeat keepalives (periodic pinging).
    - Measures real-time latency and packet health.
    - Triggers automated reconnection when an offline device is re-discovered.
    - Bridges ADB Wireless connection automatically (adb connect <ip>:5555).
    """

    def __init__(self, discovery: LocalSendDiscovery, adb_manager: Optional[Any] = None):
        self.discovery = discovery
        self.adb = adb_manager
        self.target_device: Optional[LocalSendDevice] = None
        self.target_ip: Optional[str] = None
        self.heartbeat_interval: float = 3.5
        self.missed_heartbeats_threshold: int = 3
        self.auto_bridge_adb: bool = True

        self.connection_status: str = "IDLE"  # IDLE, CONNECTING, CONNECTED, RECONNECTING, OFFLINE
        self.last_heartbeat: float = 0.0
        self.latency_ms: float = -1.0
        self.pings_sent: int = 0
        self.pings_received: int = 0

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._status_callbacks: List[Callable[[str, LocalSendDevice], None]] = []

        # Hook into discovery events to trigger auto-reconnection
        self.discovery.register_callback(self._on_device_discovered)

    def register_status_callback(self, callback: Callable[[str, LocalSendDevice], None]) -> None:
        with self._lock:
            if callback not in self._status_callbacks:
                self._status_callbacks.append(callback)

    def unregister_status_callback(self, callback: Callable[[str, LocalSendDevice], None]) -> None:
        with self._lock:
            if callback in self._status_callbacks:
                self._status_callbacks.remove(callback)

    def _notify_status(self, status: str, device: Optional[LocalSendDevice] = None) -> None:
        target = device or self.target_device
        for cb in list(self._status_callbacks):
            try:
                cb(status, target)
            except Exception:
                pass

    def connect(self, device_or_ip: Any) -> bool:
        """Establishes persistent connection to the target Android device."""
        with self._lock:
            if isinstance(device_or_ip, LocalSendDevice):
                self.target_device = device_or_ip
                self.target_ip = device_or_ip.ip
            elif isinstance(device_or_ip, str):
                self.target_ip = device_or_ip
                # Check if device already in discovered list
                for dev in self.discovery.discovered_devices.values():
                    if dev.ip == device_or_ip:
                        self.target_device = dev
                        break
                if not self.target_device:
                    self.target_device = LocalSendDevice(ip=device_or_ip)

            self.target_device.is_persistent = True
            self.connection_status = "CONNECTING"
            self._notify_status("CONNECTING")

        # Perform initial handshake & ping
        success, latency = self.ping_peer(self.target_device.ip, self.target_device.port)
        if success:
            with self._lock:
                self.connection_status = "CONNECTED"
                self.target_device.connection_status = "CONNECTED"
                self.target_device.latency_ms = latency
                self.latency_ms = latency
                self.last_heartbeat = time.time()
                self._notify_status("CONNECTED")

            # Auto bridge ADB wireless if enabled
            if self.auto_bridge_adb and self.adb:
                threading.Thread(target=self._bridge_adb, daemon=True).start()
        else:
            with self._lock:
                self.connection_status = "RECONNECTING"
                self._notify_status("RECONNECTING")

        # Start persistent heartbeat loop if not active
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True, name="LocalSend-Heartbeat")
            self._thread.start()

        return success

    def disconnect(self) -> None:
        """Disconnects the persistent session."""
        with self._lock:
            self._running = False
            self.connection_status = "DISCONNECTED"
            if self.target_device:
                self.target_device.is_persistent = False
                self.target_device.connection_status = "DISCONNECTED"
            dev = self.target_device
            self.target_device = None
            self.target_ip = None
        self._notify_status("DISCONNECTED", dev)

    def ping_peer(self, ip: str, port: int = LOCALSEND_PORT, timeout: float = 2.0) -> Tuple[bool, float]:
        """Pings the target LocalSend peer over HTTP /api/localsend/v2/info or /api/atui/v1/ping to measure latency."""
        url = f"http://{ip}:{port}/api/localsend/v2/info"
        self.pings_sent += 1
        t_start = time.perf_counter()
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    latency = round((time.perf_counter() - t_start) * 1000.0, 1)
                    self.pings_received += 1
                    return True, latency
        except Exception:
            # Fallback to direct TCP connect probe on port
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                s.connect((ip, port))
                s.close()
                latency = round((time.perf_counter() - t_start) * 1000.0, 1)
                self.pings_received += 1
                return True, latency
            except Exception:
                return False, -1.0

        return False, -1.0

    def _bridge_adb(self) -> bool:
        """Establishes ADB wireless connection to the target device on default TCP port 5555."""
        if not self.adb or not self.target_ip:
            return False
        addr = f"{self.target_ip}:5555"
        try:
            success, msg = self.adb.wireless_connect(addr)
            with self._lock:
                if self.target_device:
                    self.target_device.adb_status = "CONNECTED" if success else "FAILED"
            return success
        except Exception:
            return False

    def _heartbeat_loop(self) -> None:
        """Continuous background thread that monitors connection health and triggers auto-reconnect."""
        consecutive_failures = 0

        while self._running:
            time.sleep(self.heartbeat_interval)
            if not self._running or not self.target_device:
                break

            target_ip = self.target_device.ip
            target_port = self.target_device.port

            success, latency = self.ping_peer(target_ip, target_port)
            with self._lock:
                if success:
                    consecutive_failures = 0
                    self.last_heartbeat = time.time()
                    self.latency_ms = latency
                    self.target_device.latency_ms = latency
                    if self.connection_status != "CONNECTED":
                        self.connection_status = "CONNECTED"
                        self.target_device.connection_status = "CONNECTED"
                        self._notify_status("CONNECTED")
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= self.missed_heartbeats_threshold:
                        if self.connection_status != "OFFLINE":
                            self.connection_status = "OFFLINE"
                            self.target_device.connection_status = "OFFLINE"
                            self._notify_status("OFFLINE")
                    else:
                        if self.connection_status == "CONNECTED":
                            self.connection_status = "RECONNECTING"
                            self._notify_status("RECONNECTING")

    def _on_device_discovered(self, device: LocalSendDevice) -> None:
        """Called by LocalSendDiscovery when an announcement beacon is received."""
        with self._lock:
            # Check if this matches our persistent target IP or fingerprint
            is_match = False
            if self.target_device and self.target_device.fingerprint and device.fingerprint:
                is_match = (self.target_device.fingerprint == device.fingerprint)
            elif self.target_ip:
                is_match = (self.target_ip == device.ip)

            if is_match:
                # Update device reference
                self.target_device = device
                self.target_ip = device.ip
                device.is_persistent = True

                # If connection was lost or offline, instantly restore it!
                if self.connection_status in ("OFFLINE", "RECONNECTING"):
                    self.connection_status = "CONNECTED"
                    device.connection_status = "CONNECTED"
                    self.last_heartbeat = time.time()
                    self._notify_status("CONNECTED")

                    # Reconnect ADB if wireless bridge enabled
                    if self.auto_bridge_adb and self.adb:
                        threading.Thread(target=self._bridge_adb, daemon=True).start()
