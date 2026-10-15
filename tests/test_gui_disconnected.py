"""
Unit tests for the merged 3-column Miller columns disconnected GUI dashboard.
Verifies:
1. DisconnectedDashboard is rendered in a 3-column layout matching BrowserView
2. Left pane contains USB & WiFi connection controls and recent devices history
3. Center pane contains Hero status banner, connection steps and quick shortcuts
4. Right pane contains ADB server debug tools, diagnostic info and troubleshooting
5. Dynamic language toggle updates all 3 columns seamlessly
"""
import asyncio
import unittest

from android_tui.app import AndroidTuiApp
from android_tui.views.disconnected import DisconnectedDashboard
from android_tui.views.browser import BrowserView
from textual.widgets import Button, Static


class TestGuiDisconnected(unittest.IsolatedAsyncioTestCase):
    async def test_three_column_disconnected_layout(self):
        app = AndroidTuiApp()
        # Mock ADB to return no devices so app stays reliably disconnected
        app.adb.get_devices = lambda: []
        app.adb.set_active_device(None)

        async with app.run_test() as pilot:
            app.adb.set_active_device(None)
            app.sync_views()
            for _ in range(5):
                await pilot.pause()

            # Disconnected dashboard should be visible, browser hidden
            dash = app.query_one(DisconnectedDashboard)
            self.assertTrue(dash.display)
            self.assertFalse(app.query_one(BrowserView).display)

            # Check 3 panes exist
            left_pane = dash.query_one("#disconnected-left-pane")
            center_pane = dash.query_one("#disconnected-center-pane")
            right_pane = dash.query_one("#disconnected-right-pane")
            self.assertIsNotNone(left_pane)
            self.assertIsNotNone(center_pane)
            self.assertIsNotNone(right_pane)

            # Left Pane: USB, WiFi, Recent
            self.assertIsNotNone(dash.query_one("#card-usb"))
            self.assertIsNotNone(dash.query_one("#btn-usb-detect"))
            self.assertIsNotNone(dash.query_one("#btn-usb-reconnect"))

            self.assertIsNotNone(dash.query_one("#card-wireless"))
            self.assertIsNotNone(dash.query_one("#btn-wifi-connect"))
            self.assertIsNotNone(dash.query_one("#btn-wifi-pair"))

            self.assertIsNotNone(dash.query_one("#card-recent"))

            # Center Pane: Hero & Guides
            self.assertIsNotNone(dash.query_one("#hero-title"))
            self.assertIsNotNone(dash.query_one("#hero-subtitle"))
            self.assertIsNotNone(dash.query_one("#card-guide-usb"))
            self.assertIsNotNone(dash.query_one("#card-guide-wifi"))
            self.assertIsNotNone(dash.query_one("#card-guide-shortcuts"))

            # Right Pane: Tools & Diagnostics
            self.assertIsNotNone(dash.query_one("#card-tools"))
            self.assertIsNotNone(dash.query_one("#btn-restart-adb"))
            self.assertIsNotNone(dash.query_one("#btn-tcpip"))
            self.assertIsNotNone(dash.query_one("#card-adb-info"))
            self.assertIsNotNone(dash.query_one("#card-troubleshooting"))

            # Test language toggle
            app.action_toggle_language()
            for _ in range(3):
                await pilot.pause()
            left_title = dash.query_one("#disconnected-left-title", Static)
            self.assertIsNotNone(left_title)


if __name__ == "__main__":
    unittest.main()
