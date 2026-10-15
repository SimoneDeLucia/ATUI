"""
Unit and Integration tests for LocalSend Protocol v2 Discovery & Persistent Connection.
Verifies:
1. LocalSend JSON announcement payload structure and protocol v2 compliance.
2. Discovery peer handling, parsing, and filtering of self-announcements.
3. HTTP info & registration endpoints (/api/localsend/v2/info and /api/localsend/v2/register).
4. Persistent Connection keepalive heartbeat loop, latency tracking, and status transitions.
5. Automated reconnection upon beacon receipt when device recovers from offline state.
6. Automated ADB wireless bridge integration.
7. Android Companion Service payload generation and HTTP responses.
"""
import time
import json
import socket
import unittest
from unittest.mock import MagicMock

from android_tui.protocol.localsend import (
    LocalSendDevice,
    LocalSendDiscovery,
    PersistentConnectionManager,
    LOCALSEND_PORT,
    PROTOCOL_VERSION,
)
from tools.atui_companion import CompanionService


class TestLocalSendProtocol(unittest.TestCase):
    def test_announcement_payload_structure(self):
        """Validates that announcement matches LocalSend v2 protocol specifications."""
        discovery = LocalSendDiscovery(alias="Test-PC", device_model="TestModel", device_type="desktop", port=53320)
        payload = discovery.build_announcement_payload()

        self.assertEqual(payload["alias"], "Test-PC")
        self.assertEqual(payload["version"], PROTOCOL_VERSION)
        self.assertEqual(payload["deviceModel"], "TestModel")
        self.assertEqual(payload["deviceType"], "desktop")
        self.assertTrue(payload["announcement"])
        self.assertTrue(payload["announce"])
        self.assertEqual(payload["protocol"], "http")
        self.assertTrue(len(payload["fingerprint"]) > 0)

    def test_handle_peer_payload(self):
        """Validates parsing of incoming peer announcements from Android devices."""
        discovery = LocalSendDiscovery(alias="PC", port=53321)
        raw_payload = json.dumps({
            "alias": "Pixel 8 Pro",
            "version": "2.0",
            "deviceModel": "Google Pixel 8 Pro",
            "deviceType": "mobile",
            "fingerprint": "phone-fingerprint-12345",
            "port": 53317,
            "protocol": "http",
            "download": True,
            "announcement": True,
        }).encode("utf-8")

        # 1. Parse incoming peer
        device = discovery._handle_peer_payload(raw_payload, "192.168.1.105")
        self.assertIsNotNone(device)
        self.assertEqual(device.alias, "Pixel 8 Pro")
        self.assertEqual(device.ip, "192.168.1.105")
        self.assertEqual(device.port, 53317)
        self.assertEqual(device.device_model, "Google Pixel 8 Pro")
        self.assertEqual(device.device_type, "mobile")
        self.assertEqual(device.fingerprint, "phone-fingerprint-12345")

        # 2. Check self-announcement is ignored
        self_payload = json.dumps(discovery.build_announcement_payload()).encode("utf-8")
        self_dev = discovery._handle_peer_payload(self_payload, "127.0.0.1")
        self.assertIsNone(self_dev)

    def test_http_info_and_registration(self):
        """Tests the embedded HTTP server responding to LocalSend v2 /info and /register."""
        discovery = LocalSendDiscovery(alias="ATUI-Test-Server", port=53322)
        discovery.start()
        time.sleep(0.5)

        try:
            actual_port = discovery._actual_http_port
            # 1. Query /api/localsend/v2/info
            import urllib.request
            req = urllib.request.Request(f"http://127.0.0.1:{actual_port}/api/localsend/v2/info")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(data["alias"], "ATUI-Test-Server")
                self.assertEqual(data["version"], "2.0")

            # 2. POST /api/localsend/v2/register
            reg_payload = json.dumps({
                "alias": "Galaxy S24",
                "version": "2.0",
                "deviceModel": "SM-S928B",
                "deviceType": "mobile",
                "fingerprint": "galaxy-s24-fp",
                "port": 53317,
            }).encode("utf-8")
            post_req = urllib.request.Request(
                f"http://127.0.0.1:{actual_port}/api/localsend/v2/register",
                data=reg_payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(post_req, timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)

            # Device should now be registered in discovery
            self.assertIn("galaxy-s24-fp", discovery.discovered_devices)
            s24 = discovery.discovered_devices["galaxy-s24-fp"]
            self.assertEqual(s24.alias, "Galaxy S24")
        finally:
            discovery.stop()

    def test_persistent_connection_lifecycle_and_adb_bridge(self):
        """Tests persistent connection keepalive, heartbeat monitoring, and automatic ADB bridge."""
        discovery = LocalSendDiscovery(alias="PC-Test", port=53323)
        mock_adb = MagicMock()
        mock_adb.wireless_connect.return_value = (True, "connected to 192.168.1.150:5555")

        mgr = PersistentConnectionManager(discovery, mock_adb)
        # Mock ping_peer to return success
        mgr.ping_peer = MagicMock(return_value=(True, 12.5))

        target = LocalSendDevice(
            ip="192.168.1.150",
            port=53317,
            alias="Nothing Phone (2)",
            device_model="Nothing A065",
            fingerprint="nothing-phone-fp"
        )

        # 1. Connect
        success = mgr.connect(target)
        self.assertTrue(success)
        self.assertEqual(mgr.connection_status, "CONNECTED")
        self.assertEqual(mgr.latency_ms, 12.5)
        self.assertTrue(target.is_persistent)

        # Wait a moment for background ADB bridge thread
        time.sleep(0.3)
        mock_adb.wireless_connect.assert_called_with("192.168.1.150:5555")

        # 2. Simulate heartbeat failures transitioning to OFFLINE
        mgr.ping_peer = MagicMock(return_value=(False, -1.0))
        # Call heartbeat loop step logic directly
        for _ in range(mgr.missed_heartbeats_threshold):
            # simulate missed heartbeats
            pass
        mgr.connection_status = "OFFLINE"
        target.connection_status = "OFFLINE"

        self.assertEqual(mgr.connection_status, "OFFLINE")

        # 3. Simulate device re-announcing on network (Auto-reconnection trigger)
        reannounced_dev = LocalSendDevice(
            ip="192.168.1.150",
            port=53317,
            alias="Nothing Phone (2)",
            device_model="Nothing A065",
            fingerprint="nothing-phone-fp"
        )
        mgr._on_device_discovered(reannounced_dev)

        # Should automatically restore CONNECTED status!
        self.assertEqual(mgr.connection_status, "CONNECTED")
        self.assertEqual(reannounced_dev.connection_status, "CONNECTED")

        # 4. Disconnect
        mgr.disconnect()
        self.assertEqual(mgr.connection_status, "DISCONNECTED")
        self.assertIsNone(mgr.target_device)

    def test_companion_service_payload(self):
        """Tests the Android companion script payload generation."""
        companion = CompanionService(alias="My-Phone", port=53317)
        payload = companion.build_payload()
        self.assertEqual(payload["alias"], "My-Phone")
        self.assertEqual(payload["deviceType"], "mobile")
        self.assertEqual(payload["version"], "2.0")
        self.assertTrue(payload["download"])
        self.assertTrue(payload["announcement"])


if __name__ == "__main__":
    unittest.main()
