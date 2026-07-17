from __future__ import annotations

import unittest

from idm_eagle_bridge.eagle import EagleClient, EagleEndpointUnavailable


class RecordingEagle(EagleClient):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[tuple[str, str, dict | None]] = []

    def _request(self, method: str, path: str, data: dict | None = None) -> dict:
        self.requests.append((method, path, data))
        if path == "/api/v2/item/add":
            return {"status": "success", "data": {"id": "item-1"}}
        return {"status": "success"}


class LegacyFallbackEagle(RecordingEagle):
    def _request(self, method: str, path: str, data: dict | None = None) -> dict:
        self.requests.append((method, path, data))
        if path.startswith("/api/v2/item/"):
            raise EagleEndpointUnavailable("not supported")
        return {"status": "success"}


class EagleClientTests(unittest.TestCase):
    def test_import_without_source_omits_website_field(self) -> None:
        eagle = RecordingEagle()
        item_id = eagle.add_from_path("C:/Downloads/video.mp4")
        self.assertEqual(item_id, "item-1")
        self.assertNotIn("website", eagle.requests[0][2])

    def test_import_with_source_keeps_website_field(self) -> None:
        eagle = RecordingEagle()
        eagle.add_from_path("C:/Downloads/video.mp4", "https://example.com/watch")
        self.assertEqual(eagle.requests[0][2]["website"], "https://example.com/watch")

    def test_update_source_uses_existing_eagle_item(self) -> None:
        eagle = RecordingEagle()
        eagle.update_source("item-1", "https://example.com/watch")
        self.assertEqual(
            eagle.requests,
            [
                (
                    "POST",
                    "/api/v2/item/update",
                    {"id": "item-1", "url": "https://example.com/watch"},
                )
            ],
        )

    def test_import_falls_back_to_legacy_endpoint(self) -> None:
        eagle = LegacyFallbackEagle()
        eagle.add_from_path("C:/Downloads/video.mp4")
        self.assertEqual(
            [request[1] for request in eagle.requests],
            ["/api/v2/item/add", "/api/item/addFromPath"],
        )

    def test_update_falls_back_to_legacy_endpoint(self) -> None:
        eagle = LegacyFallbackEagle()
        eagle.update_source("item-1", "https://example.com/watch")
        self.assertEqual(
            [request[1] for request in eagle.requests],
            ["/api/v2/item/update", "/api/item/update"],
        )


if __name__ == "__main__":
    unittest.main()
