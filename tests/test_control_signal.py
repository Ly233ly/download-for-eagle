from __future__ import annotations

import unittest

from idm_eagle_bridge.control_signal import (
    QUIT_EVENT_NAME,
    RULES_EVENT_NAME,
    SHOW_EVENT_NAME,
    ControlSignals,
    notify_control_event,
)


class ControlSignalTests(unittest.TestCase):
    def test_external_tray_can_show_and_quit_window(self) -> None:
        signals = ControlSignals()
        try:
            self.assertTrue(notify_control_event(SHOW_EVENT_NAME))
            self.assertTrue(signals.poll_show())
            self.assertFalse(signals.poll_show())

            self.assertTrue(notify_control_event(RULES_EVENT_NAME))
            self.assertTrue(signals.poll_rules())
            self.assertFalse(signals.poll_rules())

            self.assertTrue(notify_control_event(QUIT_EVENT_NAME))
            self.assertTrue(signals.poll_quit())
            self.assertFalse(signals.poll_quit())
        finally:
            signals.close()


if __name__ == "__main__":
    unittest.main()
