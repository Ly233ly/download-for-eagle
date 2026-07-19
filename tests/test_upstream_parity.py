from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "third_party" / "cat-catch" / "source"
EXTENSION = ROOT / "chrome-extension"


class UpstreamParityTests(unittest.TestCase):
    def test_fixed_upstream_source_and_gpl_notices_remain_available(self) -> None:
        self.assertTrue((UPSTREAM / "LICENSE").is_file())
        self.assertTrue((ROOT / "LICENSE").is_file())
        self.assertIn("GNU GENERAL PUBLIC LICENSE", (ROOT / "LICENSE").read_text(encoding="utf-8"))
        provenance = (ROOT / "docs" / "UPSTREAM_PROVENANCE.md").read_text(encoding="utf-8")
        notices = (ROOT / "installer" / "THIRD_PARTY_NOTICES.txt").read_text(encoding="utf-8")
        self.assertIn("7a77612b3e2a01cedacae6e43eb88a89eee3034f", provenance)
        self.assertIn("cat-catch 2.7.1", notices)

    def test_upstream_toolbox_is_not_shipped_as_active_extension_ui(self) -> None:
        background = (EXTENSION / "js" / "background.js").read_text(encoding="utf-8")
        popup = (EXTENSION / "popup.html").read_text(encoding="utf-8")
        ui = (EXTENSION / "js" / "eagle-bridge-ui.js").read_text(encoding="utf-8")
        for marker in (
            "chrome.webRequest.onSendHeaders",
            "chrome.webRequest.onResponseStarted",
            "chrome.tabs.onUpdated",
            "MediaData",
        ):
            self.assertIn(marker, background)
        self.assertEqual(popup.count('id="eagleBridgeRoot"'), 1)
        for marker in ("script:search", 'eagleBridge: "createPlan"'):
            self.assertIn(marker, ui)
        for path in (
            "downloader.html", "install.html", "json.html", "m3u8.html", "mpd.html",
            "options.html", "preview.html", "img", "lib", "tools",
        ):
            self.assertFalse((EXTENSION / path).exists(), path)


if __name__ == "__main__":
    unittest.main()
