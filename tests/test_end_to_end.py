from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen

from idm_eagle_bridge.api_server import LocalApiServer
from idm_eagle_bridge.database import Database
from idm_eagle_bridge.hook import main as hook_main
from idm_eagle_bridge.processor import JobProcessor
from idm_eagle_bridge.security import PairingManager


ORIGIN = "chrome-extension://abcdefghijklmnopabcdefghijklmnop"


class FakeEagle:
    def __init__(self) -> None:
        self.imports: list[tuple[str, str | None]] = []

    def is_available(self) -> bool:
        return True

    def add_from_path(self, file_path: str, website: str | None = None) -> str:
        self.imports.append((file_path, website))
        return "e2e-item"


class EndToEndTests(unittest.TestCase):
    def test_chrome_source_plus_idm_hook_reaches_eagle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "sample-video.mp4"
            video.write_bytes(b"end-to-end-video")
            database = Database(root / "bridge.db")
            server = LocalApiServer(database, port=0)
            server.start()
            host, port = server.address
            base = f"http://{host}:{port}"
            try:
                token = self._post(
                    f"{base}/api/pair",
                    {"code": PairingManager(database).pairing_code},
                )["data"]["token"]
                self._post(
                    f"{base}/api/site",
                    {"domain": "example.com", "enabled": True},
                    token,
                )
                self._post(
                    f"{base}/api/source",
                    {
                        "pageUrl": "https://example.com/watch?id=100&utm_source=test",
                        "pageTitle": "sample video",
                        "mediaUrl": "https://cdn.example.com/sample-video.mp4",
                        "eventType": "video_request",
                    },
                    token,
                )

                with patch.dict(
                    os.environ,
                    {
                        "IDM_EAGLE_DATA_DIR": directory,
                        "IDM_EAGLE_DISABLE_AUTO_START": "1",
                    },
                ):
                    self.assertEqual(hook_main([str(video)]), 0)

                eagle = FakeEagle()
                JobProcessor(
                    database,
                    eagle=eagle,
                    minimum_file_age=0,
                    source_grace_period=0,
                ).process_once()
                jobs = database.list_jobs()
                self.assertEqual(jobs[0]["status"], "imported")
                self.assertEqual(
                    eagle.imports,
                    [(str(video), "https://example.com/watch?id=100")],
                )
            finally:
                server.stop()

    def test_idm_hook_without_source_still_reaches_eagle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "no-source.mp4"
            video.write_bytes(b"no-source-video")
            with patch.dict(
                os.environ,
                {
                    "IDM_EAGLE_DATA_DIR": directory,
                    "IDM_EAGLE_DISABLE_AUTO_START": "1",
                },
            ):
                self.assertEqual(hook_main([str(video)]), 0)
                database = Database(root / "bridge.db")
                eagle = FakeEagle()
                JobProcessor(
                    database,
                    eagle=eagle,
                    minimum_file_age=0,
                    source_grace_period=0,
                ).process_once()

            jobs = database.list_jobs()
            self.assertEqual(jobs[0]["status"], "imported")
            self.assertIsNone(jobs[0]["source_url"])
            self.assertEqual(eagle.imports, [(str(video), None)])

    @staticmethod
    def _post(url: str, payload: dict, token: str | None = None) -> dict:
        headers = {"Content-Type": "application/json", "Origin": ORIGIN}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
