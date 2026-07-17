from __future__ import annotations

import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from idm_eagle_bridge.api_server import LocalApiServer
from idm_eagle_bridge.database import Database
from idm_eagle_bridge.security import PairingManager


ORIGIN = "chrome-extension://abcdefghijklmnopabcdefghijklmnop"


class SecurityApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "test.db")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_pairing_rejects_wrong_code_and_accepts_token(self) -> None:
        pairing = PairingManager(self.database)
        with self.assertRaises(ValueError):
            pairing.pair(ORIGIN, "000000" if pairing.pairing_code != "000000" else "999999")

        code = pairing.pairing_code
        token = pairing.pair(ORIGIN, code)
        self.assertTrue(pairing.authenticate(ORIGIN, token))
        self.assertFalse(pairing.authenticate(ORIGIN, "wrong"))

    def test_http_pair_site_and_source_flow(self) -> None:
        server = LocalApiServer(self.database, port=0)
        server.start()
        host, port = server.address
        base = f"http://{host}:{port}"
        try:
            code = PairingManager(self.database).pairing_code
            paired = self._json_request(
                f"{base}/api/pair", {"code": code}, origin=ORIGIN
            )
            token = paired["data"]["token"]

            self._json_request(
                f"{base}/api/site",
                {"domain": "example.com", "enabled": True, "includeSubdomains": True},
                origin=ORIGIN,
                token=token,
            )
            source = self._json_request(
                f"{base}/api/source",
                {
                    "pageUrl": "https://video.example.com/watch?id=1&utm_source=test",
                    "pageTitle": "测试页面",
                    "eventType": "manual",
                },
                origin=ORIGIN,
                token=token,
            )
            self.assertTrue(source["data"]["eventId"])
        finally:
            server.stop()

    def test_installer_bootstrap_pairs_once_and_is_consumed(self) -> None:
        secret = "installer-secret-for-test"
        bootstrap = Path(self.temp_dir.name) / "pairing-bootstrap.json"
        bootstrap.write_text(
            json.dumps(
                {
                    "secretHash": hashlib.sha256(secret.encode("utf-8")).hexdigest(),
                    "expiresAt": time.time() + 60,
                }
            ),
            encoding="utf-8",
        )
        server = LocalApiServer(self.database, port=0)
        server.api.pairing.bootstrap_path = bootstrap
        server.start()
        host, port = server.address
        try:
            paired = self._json_request(
                f"http://{host}:{port}/api/pair/auto",
                {"secret": secret},
                origin=ORIGIN,
            )
            token = paired["data"]["token"]
            self.assertTrue(server.api.pairing.authenticate(ORIGIN, token))
            self.assertFalse(bootstrap.exists())
        finally:
            server.stop()

    def test_web_page_origin_is_rejected(self) -> None:
        server = LocalApiServer(self.database, port=0)
        server.start()
        host, port = server.address
        try:
            with self.assertRaises(HTTPError) as caught:
                self._json_request(
                    f"http://{host}:{port}/api/pair",
                    {"code": PairingManager(self.database).pairing_code},
                    origin="https://example.com",
                )
            self.assertEqual(caught.exception.code, 403)
            caught.exception.close()
        finally:
            server.stop()

    def test_post_body_token_authentication(self) -> None:
        server = LocalApiServer(self.database, host="127.0.0.1", port=0)
        server.start()
        host, port = server.address
        try:
            code = PairingManager(self.database).pairing_code
            paired = self._json_request(
                f"http://{host}:{port}/api/pair",
                {"code": code},
                origin=ORIGIN,
            )
            token = paired["data"]["token"]
            site = self._json_request(
                f"http://{host}:{port}/api/site/status",
                {"domain": "example.com", "authToken": token},
                origin=ORIGIN,
            )
            self.assertEqual(site["data"], {"domain": "example.com", "enabled": False})
        finally:
            server.stop()

    @staticmethod
    def _json_request(
        url: str,
        payload: dict,
        *,
        origin: str,
        token: str | None = None,
    ) -> dict:
        headers = {"Content-Type": "application/json", "Origin": origin}
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
