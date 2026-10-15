#!/usr/bin/env python3
"""
ATUI Android Companion Service (LocalSend Protocol Engine).
Runs on an Android device (via Termux, Pydroid, or adb shell) to establish a persistent
LocalSend connection with ATUI running on the PC.

Features:
- Announces the Android device over LocalSend UDP Multicast (224.0.0.167:53317) and Broadcast.
- Embedded HTTP responder on port 53317 for peer registration, health check, and keepalive ping.
- Enables ADB over TCP/IP (port 5555) on rooted devices or when initiated via ADB shell.
- Maintains persistent connection session with ATUI.
"""
import os
import sys
import time
import json
import uuid
import socket
import struct
import platform
import argparse
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

LOCALSEND_MULTICAST_GROUP = "224.0.0.167"
LOCALSEND_PORT = 53317


def get_android_device_info() -> dict:
    """Extracts Android device model and manufacturer if running on Android."""
    model = "Android Device"
    brand = "Android"

    # Try reading Android getprop via shell or environment
    try:
        import subprocess
        p_model = subprocess.run(["getprop", "ro.product.model"], capture_output=True, text=True, timeout=1)
        if p_model.returncode == 0 and p_model.stdout.strip():
            model = p_model.stdout.strip()

        p_brand = subprocess.run(["getprop", "ro.product.brand"], capture_output=True, text=True, timeout=1)
        if p_brand.returncode == 0 and p_brand.stdout.strip():
            brand = p_brand.stdout.strip().capitalize()
    except Exception:
        pass

    return {"model": model, "brand": brand}


class CompanionService:
    def __init__(self, alias: str = "", port: int = LOCALSEND_PORT, beacon_interval: float = 4.0):
        self.port = port
        self.beacon_interval = beacon_interval

        info = get_android_device_info()
        self.alias = alias or f"{info['brand']} Phone"
        self.device_model = info["model"]
        self.fingerprint = f"atui-companion-{uuid.uuid4().hex[:12]}"
        self._running = False
        self._lock = threading.Lock()
        self.connected_pc_ip: str = ""
        self.last_pc_ping: float = 0.0

    def build_payload(self) -> dict:
        return {
            "alias": self.alias,
            "version": "2.0",
            "deviceModel": self.device_model,
            "deviceType": "mobile",
            "fingerprint": self.fingerprint,
            "port": self.port,
            "protocol": "http",
            "download": True,
            "announcement": True,
            "announce": True,
        }

    def start(self) -> None:
        self._running = True
        print(f"[*] Avvio ATUI Companion su porta {self.port}...")
        print(f"[*] Dispositivo: {self.alias} ({self.device_model})")
        print(f"[*] Fingerprint: {self.fingerprint}")

        # Try enabling TCP/IP on Android port 5555
        self._try_enable_adb_tcpip()

        # 1. Start HTTP Server
        http_thread = threading.Thread(target=self._run_http, daemon=True)
        http_thread.start()

        # 2. Start Multicast Beacon Loop
        beacon_thread = threading.Thread(target=self._run_beacon_loop, daemon=True)
        beacon_thread.start()

        print("[+] Servizio in esecuzione. Premi Ctrl+C per terminare.")
        try:
            while self._running:
                time.sleep(1.0)
                if self.connected_pc_ip and (time.time() - self.last_pc_ping < 10.0):
                    status = f"🟢 Connesso a PC ({self.connected_pc_ip})"
                else:
                    status = "🟡 In attesa di connessione da ATUI..."
                print(f"\r[*] Stato: {status} ", end="", flush=True)
        except KeyboardInterrupt:
            print("\n[-] Chiusura servizio...")
            self._running = False

    def _try_enable_adb_tcpip(self) -> None:
        try:
            import subprocess
            subprocess.run(["setprop", "service.adb.tcp.port", "5555"], capture_output=True, timeout=1)
            subprocess.run(["stop", "adbd"], capture_output=True, timeout=1)
            subprocess.run(["start", "adbd"], capture_output=True, timeout=1)
        except Exception:
            pass

    def _run_http(self) -> None:
        parent = self

        class CompanionHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def do_GET(self):
                if self.path.startswith("/api/localsend/v2/info") or self.path.startswith("/api/atui/v1/ping"):
                    parent.last_pc_ping = time.time()
                    parent.connected_pc_ip = self.client_address[0]
                    payload = json.dumps(parent.build_payload()).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                if self.path.startswith("/api/localsend/v2/register"):
                    parent.last_pc_ping = time.time()
                    parent.connected_pc_ip = self.client_address[0]
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()

        try:
            server = HTTPServer(("0.0.0.0", self.port), CompanionHandler)
            server.serve_forever()
        except Exception as e:
            print(f"[!] Errore server HTTP: {e}")

    def _run_beacon_loop(self) -> None:
        payload = json.dumps(self.build_payload()).encode("utf-8")
        while self._running:
            # 1. UDP Multicast
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", 2))
                s.sendto(payload, (LOCALSEND_MULTICAST_GROUP, self.port))
                s.close()
            except Exception:
                pass

            # 2. UDP Broadcast
            try:
                bs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                bs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                bs.sendto(payload, ("255.255.255.255", self.port))
                bs.close()
            except Exception:
                pass

            time.sleep(self.beacon_interval)


def main():
    parser = argparse.ArgumentParser(description="ATUI Android Companion (LocalSend Protocol)")
    parser.add_argument("--alias", help="Nome visualizzato del telefono", default="")
    parser.add_argument("--port", type=int, help="Porta LocalSend (predefinita 53317)", default=LOCALSEND_PORT)
    parser.add_argument("--interval", type=float, help="Intervallo beacon (sec)", default=4.0)
    args = parser.parse_args()

    service = CompanionService(alias=args.alias, port=args.port, beacon_interval=args.interval)
    service.start()


if __name__ == "__main__":
    main()
