from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from idm_eagle_bridge.database import Database
from idm_eagle_bridge.eagle import EagleUnavailable
from idm_eagle_bridge.processor import JobProcessor


class FakeEagle:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.imports: list[tuple[str, str | None]] = []

    def is_available(self) -> bool:
        return self.available

    def add_from_path(self, file_path: str, website: str | None = None) -> str:
        if not self.available:
            raise EagleUnavailable("Eagle 当前不可用")
        self.imports.append((file_path, website))
        return f"item-{len(self.imports)}"


class ProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.database = Database(root / "test.db")
        self.database.set_site_rule("example.com", True)
        self.video = root / "中文 视频 (1).mp4"
        self.video.write_bytes(b"fake-video-content")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _add_job(self, path: Path, offset: float = 0) -> str:
        now = time.time() + offset
        self.database.add_source_event(
            f"https://example.com/watch?id={now}",
            "来源网页",
            created_at=now,
        )
        return self.database.add_job(str(path), created_at=now + 1)

    def test_video_is_imported_with_source_page(self) -> None:
        job_id = self._add_job(self.video)
        eagle = FakeEagle()
        processor = JobProcessor(
            self.database, eagle=eagle, minimum_file_age=0, source_grace_period=0
        )

        processor.process_job(job_id)

        job = self.database.get_job(job_id)
        self.assertEqual(job["status"], "imported")
        self.assertEqual(len(eagle.imports), 1)
        self.assertTrue(eagle.imports[0][1].startswith("https://example.com/watch?id="))

    def test_video_without_source_is_imported_directly(self) -> None:
        job_id = self.database.add_job(str(self.video))
        eagle = FakeEagle()
        processor = JobProcessor(
            self.database, eagle=eagle, minimum_file_age=0, source_grace_period=0
        )

        processor.process_job(job_id)

        job = self.database.get_job(job_id)
        self.assertEqual(job["status"], "imported")
        self.assertIsNone(job["source_url"])
        self.assertEqual(eagle.imports, [(str(self.video), None)])

    def test_same_content_is_skipped_even_with_different_name(self) -> None:
        eagle = FakeEagle()
        processor = JobProcessor(
            self.database, eagle=eagle, minimum_file_age=0, source_grace_period=0
        )

        first_job = self._add_job(self.video)
        processor.process_job(first_job)

        copy = Path(self.temp_dir.name) / "another-name.mkv"
        copy.write_bytes(self.video.read_bytes())
        second_job = self._add_job(copy, offset=10)
        processor.process_job(second_job)

        self.assertEqual(self.database.get_job(second_job)["status"], "skipped_duplicate")
        self.assertEqual(len(eagle.imports), 1)

    def test_eagle_offline_keeps_waiting_job(self) -> None:
        job_id = self._add_job(self.video)
        processor = JobProcessor(
            self.database,
            eagle=FakeEagle(available=False),
            minimum_file_age=0,
            source_grace_period=0,
        )

        processor.process_job(job_id)

        job = self.database.get_job(job_id)
        self.assertEqual(job["status"], "waiting_eagle")
        self.assertEqual(job["attempt_count"], 1)
        self.assertIsNotNone(job["next_retry_at"])
        self.assertIn("自动重试", job["error_message"])

    def test_non_video_is_ignored(self) -> None:
        text_file = Path(self.temp_dir.name) / "notes.txt"
        text_file.write_text("not a video", encoding="utf-8")
        job_id = self._add_job(text_file)
        processor = JobProcessor(
            self.database,
            eagle=FakeEagle(),
            minimum_file_age=0,
            source_grace_period=0,
        )

        processor.process_job(job_id)

        self.assertEqual(self.database.get_job(job_id)["status"], "ignored_non_video")

    def test_user_ignore_event_does_not_import(self) -> None:
        now = time.time()
        self.database.add_source_event(
            "https://example.com/watch?id=ignore",
            "忽略这次",
            event_type="ignore",
            created_at=now,
        )
        job_id = self.database.add_job(str(self.video), created_at=now + 1)
        eagle = FakeEagle()
        processor = JobProcessor(
            self.database, eagle=eagle, minimum_file_age=0, source_grace_period=0
        )

        processor.process_job(job_id)

        self.assertEqual(self.database.get_job(job_id)["status"], "ignored_by_user")
        self.assertEqual(eagle.imports, [])

    def test_short_grace_allows_late_browser_source_to_attach(self) -> None:
        job_id = self.database.add_job(str(self.video))
        job = self.database.get_job(job_id)
        eagle = FakeEagle()
        processor = JobProcessor(
            self.database,
            eagle=eagle,
            minimum_file_age=0,
            source_grace_period=30,
        )

        processor.process_job(job_id)

        waiting = self.database.get_job(job_id)
        self.assertEqual(waiting["status"], "queued")
        self.assertEqual(waiting["error_code"], "source_grace")
        self.assertEqual(eagle.imports, [])

        self.database.add_source_event(
            "https://example.com/late-source",
            "稍晚到达的浏览器来源",
            created_at=float(job["created_at"]) - 0.1,
        )
        processor.process_job(job_id)

        imported = self.database.get_job(job_id)
        self.assertEqual(imported["status"], "imported")
        self.assertEqual(eagle.imports[0][1], "https://example.com/late-source")

    def test_newly_finished_file_retries_automatically_with_short_delay(self) -> None:
        job_id = self.database.add_job(str(self.video))
        processor = JobProcessor(
            self.database,
            eagle=FakeEagle(),
            minimum_file_age=10,
            source_grace_period=0,
        )

        before = time.time()
        processor.process_job(job_id)

        job = self.database.get_job(job_id)
        self.assertEqual(job["status"], "retry")
        self.assertEqual(job["error_code"], "file_not_stable")
        self.assertIn("自动重试", job["error_message"])
        self.assertGreater(job["next_retry_at"], before)
        self.assertLessEqual(job["next_retry_at"] - before, 3.5)

    def test_unstable_file_stops_after_twenty_attempts(self) -> None:
        job_id = self.database.add_job(str(self.video))
        self.database.update_job(job_id, attempt_count=19)
        processor = JobProcessor(
            self.database,
            eagle=FakeEagle(),
            minimum_file_age=10,
            source_grace_period=0,
        )

        processor.process_job(job_id)

        job = self.database.get_job(job_id)
        self.assertEqual(job["status"], "failed_permanent")
        self.assertEqual(job["attempt_count"], 20)
        self.assertIsNone(job["next_retry_at"])
        self.assertIn("停止自动重试", job["error_message"])

    def test_waiting_for_eagle_stops_after_one_hundred_twenty_checks(self) -> None:
        job_id = self._add_job(self.video)
        self.database.update_job(job_id, attempt_count=119)
        processor = JobProcessor(
            self.database,
            eagle=FakeEagle(available=False),
            minimum_file_age=0,
            source_grace_period=0,
        )

        processor.process_job(job_id)

        job = self.database.get_job(job_id)
        self.assertEqual(job["status"], "failed_permanent")
        self.assertEqual(job["attempt_count"], 120)
        self.assertIsNone(job["next_retry_at"])
        self.assertIn("1 小时", job["error_message"])

    def test_completed_same_job_cannot_turn_into_duplicate_on_retry_race(self) -> None:
        job_id = self._add_job(self.video)
        eagle = FakeEagle()
        processor = JobProcessor(
            self.database,
            eagle=eagle,
            minimum_file_age=0,
            source_grace_period=0,
        )
        processor.process_job(job_id)

        self.assertEqual(self.database.get_job(job_id)["status"], "imported")
        self.assertFalse(self.database.retry_job(job_id))

        # 模拟旧界面在导入完成边界上把同一任务再次标记为重试。
        self.database.update_job(
            job_id,
            status="retry",
            next_retry_at=None,
            error_code="file_not_stable",
            error_message="模拟竞态",
            completed_at=None,
        )
        processor.process_job(job_id)

        restored = self.database.get_job(job_id)
        self.assertEqual(restored["status"], "imported")
        self.assertIsNone(restored["error_code"])
        self.assertEqual(len(eagle.imports), 1)


if __name__ == "__main__":
    unittest.main()
