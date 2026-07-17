from __future__ import annotations

import unittest

from idm_eagle_bridge.url_utils import (
    InvalidPageUrl,
    clean_page_url,
    domain_from_url,
    normalize_domain,
)


class UrlUtilsTests(unittest.TestCase):
    def test_clean_page_url_removes_tracking_and_fragment(self) -> None:
        result = clean_page_url(
            "HTTPS://Example.COM/watch?id=42&utm_source=test&fbclid=abc#comments"
        )
        self.assertEqual(result, "https://example.com/watch?id=42")

    def test_clean_page_url_preserves_functional_query(self) -> None:
        result = clean_page_url("https://例子.测试/video?page=2&quality=hd")
        self.assertEqual(
            result,
            "https://xn--fsqu00a.xn--0zwm56d/video?page=2&quality=hd",
        )

    def test_credentials_are_rejected(self) -> None:
        with self.assertRaises(InvalidPageUrl):
            clean_page_url("https://user:password@example.com/video")

    def test_domain_normalization(self) -> None:
        self.assertEqual(normalize_domain("Sub.Example.com."), "sub.example.com")
        self.assertEqual(domain_from_url("https://sub.example.com/a"), "sub.example.com")


if __name__ == "__main__":
    unittest.main()
