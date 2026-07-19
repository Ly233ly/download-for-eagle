from __future__ import annotations

import functools
import http.server
import os
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from idm_eagle_bridge.database import Database
from idm_eagle_bridge.media import (
    MediaCoordinator,
    MediaPlanError,
    redact_media_url,
    resolve_media_tool,
    safe_output_name,
)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *args: object) -> None:
        return


class MediaCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database = Database(self.root / "bridge.db")
        self.ready = Mock()
        self.coordinator = MediaCoordinator(
            self.database, workers=1, ready_callback=self.ready
        )

    def tearDown(self) -> None:
        self.coordinator.close()
        self.temporary.cleanup()

    @staticmethod
    def payload(**overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "pageUrl": "https://www.bilibili.com/video/BV1test?spm_id_from=secret",
            "pageTitle": "测试视频",
            "outputName": "测试：视频.mp4",
            "outputContainer": "mp4",
            "mergeMode": "direct",
            "route": "browser",
            "importToEagle": True,
            "tabId": 7,
            "streams": [
                {
                    "clientIndex": 0,
                    "url": "https://cdn.example/video.mp4?token=private",
                    "role": "video",
                    "name": "video.mp4",
                    "extension": "mp4",
                    "mimeType": "video/mp4",
                    "size": 123,
                    "duration": 12,
                    "drm": False,
                }
            ],
            "runtimeHeaders": [{}],
        }
        payload.update(overrides)
        return payload

    def _media_tools(self) -> tuple[Path, Path]:
        try:
            return resolve_media_tool("ffmpeg"), resolve_media_tool("ffprobe")
        except MediaPlanError:
            self.skipTest("FFmpeg build asset is not available")

    def _make_video(self, target: Path, color: str = "blue", seconds: int = 1) -> None:
        ffmpeg, _ffprobe = self._media_tools()
        subprocess.run(
            [
                str(ffmpeg),
                "-hide_banner",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=320x180:r=25",
                "-t",
                str(seconds),
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(target),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )

    def test_manifest_quality_selection_uses_the_requested_program(self) -> None:
        probe = {
            "programs": [
                {"program_id": 0, "streams": [
                    {"index": 0, "codec_type": "video", "width": 1280, "height": 720, "bit_rate": "3200000"},
                    {"index": 1, "codec_type": "audio", "bit_rate": "128000"},
                ]},
                {"program_id": 1, "streams": [
                    {"index": 2, "codec_type": "video", "width": 1920, "height": 1080, "bit_rate": "6300000"},
                    {"index": 3, "codec_type": "audio", "bit_rate": "128000"},
                ]},
                {"program_id": 2, "streams": [
                    {"index": 4, "codec_type": "video", "width": 640, "height": 360, "bit_rate": "900000"},
                    {"index": 5, "codec_type": "audio", "bit_rate": "96000"},
                ]},
                {"program_id": 3, "streams": [
                    {"index": 6, "codec_type": "video", "width": 3840, "height": 2160, "bit_rate": "18000000"},
                    {"index": 7, "codec_type": "audio", "bit_rate": "192000"},
                ]},
                {"program_id": 4, "streams": [
                    {"index": 8, "codec_type": "video", "width": 2560, "height": 1440, "bit_rate": "9000000"},
                    {"index": 9, "codec_type": "audio", "bit_rate": "160000"},
                ]},
                {"program_id": 5, "streams": [
                    {"index": 10, "codec_type": "video", "width": 854, "height": 480, "bit_rate": "1300000"},
                    {"index": 11, "codec_type": "audio", "bit_rate": "96000"},
                ]},
                {"program_id": 6, "streams": [
                    {"index": 12, "codec_type": "video", "width": 426, "height": 240, "bit_rate": "480000"},
                    {"index": 13, "codec_type": "audio", "bit_rate": "64000"},
                ]},
                {"program_id": 7, "streams": [
                    {"index": 14, "codec_type": "video", "width": 256, "height": 144, "bit_rate": "180000"},
                    {"index": 15, "codec_type": "audio", "bit_rate": "64000"},
                ]},
            ]
        }
        self.assertEqual(
            MediaCoordinator._select_manifest_stream_indexes(probe, 1080),
            (2, 3),
        )
        self.assertEqual(
            MediaCoordinator._select_manifest_stream_indexes(probe, 720),
            (0, 1),
        )
        self.assertEqual(
            MediaCoordinator._select_manifest_stream_indexes(probe, 1440),
            (8, 9),
        )
        self.assertEqual(
            MediaCoordinator._select_manifest_stream_indexes(probe, 480),
            (10, 11),
        )
        self.assertEqual(
            MediaCoordinator._select_manifest_stream_indexes(probe, None),
            (6, 7),
        )

    @staticmethod
    def _start_server(directory: Path, handler_type: type[http.server.SimpleHTTPRequestHandler] = QuietHandler):
        handler = functools.partial(handler_type, directory=str(directory))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def _wait(self, plan_id: str, timeout: float = 40) -> dict:
        deadline = time.monotonic() + timeout
        result = self.coordinator.get_plan(plan_id)
        while result["status"] not in {
            "ready_to_import",
            "completed_local",
            "retry",
            "canceled",
        } and time.monotonic() < deadline:
            time.sleep(0.1)
            result = self.coordinator.get_plan(plan_id)
        return result

    def test_schema_five_has_desktop_plan_state_and_no_component_handoff(self) -> None:
        with self.database.session() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(download_plans)")
            }
        self.assertEqual(version, 5)
        self.assertNotIn("component_files", names)
        self.assertTrue(
            {
                "import_to_eagle",
                "downloaded_bytes",
                "total_bytes",
                "phase_detail",
                "preview_path",
            }.issubset(columns)
        )

    def test_schema_five_migrates_old_browser_tasks_without_guessing_urls(self) -> None:
        with patch.object(self.coordinator, "schedule"):
            plan = self.coordinator.create_plan(self.payload())
        with self.database.session() as connection:
            connection.execute(
                """
                CREATE TABLE component_files (
                    id TEXT PRIMARY KEY, plan_id TEXT NOT NULL, stream_id TEXT NOT NULL,
                    role TEXT NOT NULL, expected_relative_path TEXT NOT NULL,
                    status TEXT NOT NULL, owned INTEGER NOT NULL,
                    created_at REAL NOT NULL, updated_at REAL NOT NULL
                )
                """
            )
            connection.execute(
                "UPDATE download_plans SET route = 'browser', status = 'downloading_components' WHERE id = ?",
                (plan["id"],),
            )
            connection.execute("PRAGMA user_version = 4")
        reopened = Database(self.database.path)
        with reopened.session() as connection:
            migrated = connection.execute(
                "SELECT route, status, error_code FROM download_plans WHERE id = ?",
                (plan["id"],),
            ).fetchone()
            component_table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'component_files'"
            ).fetchone()
            version = connection.execute("PRAGMA user_version").fetchone()[0]
        self.assertEqual(version, 5)
        self.assertIsNone(component_table)
        self.assertEqual(dict(migrated), {
            "route": "desktop",
            "status": "retry",
            "error_code": "download_context_expired",
        })

    def test_every_plan_is_desktop_and_sensitive_context_is_memory_only(self) -> None:
        with patch.object(self.coordinator, "schedule"):
            plan = self.coordinator.create_plan(
                self.payload(
                    route="browser",
                    runtimeHeaders=[
                        {
                            "referer": "https://www.bilibili.com/",
                            "authorization": "Bearer private",
                            "cookie": "SESSDATA=private",
                            "origin": "https://www.bilibili.com\r\nX-Injected: yes",
                        }
                    ],
                )
            )
        self.assertEqual(plan["route"], "desktop")
        runtime = self.coordinator._remote_inputs[plan["id"]]["streams"][0]
        self.assertEqual(runtime["headers"]["authorization"], "Bearer private")
        self.assertEqual(runtime["headers"]["cookie"], "SESSDATA=private")
        self.assertNotIn("origin", runtime["headers"])
        with self.database.session() as connection:
            stored = connection.execute(
                "SELECT route FROM download_plans WHERE id = ?", (plan["id"],)
            ).fetchone()
            dump = " ".join(
                str(value)
                for row in connection.execute("SELECT * FROM media_streams")
                for value in row
                if value is not None
            )
        self.assertEqual(stored["route"], "desktop")
        self.assertNotIn("private", dump)

    def test_youtube_resolver_plan_keeps_quality_and_auth_context_out_of_database(self) -> None:
        stream = {
            **self.payload()["streams"][0],
            "url": "https://www.youtube.com/watch?v=pIzs1qe-aBc",
            "resolver": "youtube",
            "preferredQuality": "1440p",
            "size": None,
        }
        with patch.object(self.coordinator, "schedule"):
            plan = self.coordinator.create_plan(self.payload(
                pageUrl=stream["url"],
                streams=[stream],
                runtimeHeaders=[{"cookie": "SAPISID=top-secret", "user-agent": "Chrome/Test"}],
            ))
        runtime = self.coordinator._remote_inputs[plan["id"]]["streams"][0]
        self.assertEqual(runtime["resolver"], "youtube")
        self.assertEqual(runtime["preferred_quality"], "1440p")
        self.assertEqual(runtime["headers"]["cookie"], "SAPISID=top-secret")
        with self.database.session() as connection:
            dump = " ".join(
                str(value)
                for table in ("media_streams", "media_groups", "download_plans")
                for row in connection.execute(f"SELECT * FROM {table}")
                for value in row
                if value is not None
            )
        self.assertNotIn("top-secret", dump)

    def test_page_resolver_plan_keeps_permalink_and_auth_context_out_of_database(self) -> None:
        long_session_cookie = "sessionid=" + "s" * 6000 + "; csrftoken=top-secret"
        stream = {
            **self.payload()["streams"][0],
            "url": "https://www.instagram.com/p/Da9rBuVjAGK/",
            "resolver": "page",
            "preferredQuality": "",
            "size": None,
        }
        with patch.object(self.coordinator, "schedule"):
            plan = self.coordinator.create_plan(self.payload(
                pageUrl="https://www.instagram.com/",
                streams=[stream],
                runtimeHeaders=[{"cookie": long_session_cookie, "user-agent": "Chrome/Test"}],
            ))
        runtime = self.coordinator._remote_inputs[plan["id"]]["streams"][0]
        self.assertEqual(runtime["resolver"], "page")
        self.assertEqual(runtime["url"], "https://www.instagram.com/p/Da9rBuVjAGK/")
        self.assertEqual(runtime["headers"]["cookie"], long_session_cookie)
        with self.database.session() as connection:
            dump = " ".join(
                str(value)
                for table in ("media_streams", "media_groups", "download_plans")
                for row in connection.execute(f"SELECT * FROM {table}")
                for value in row
                if value is not None
            )
        self.assertNotIn("top-secret", dump)

    def test_page_resolver_rejects_private_network_urls(self) -> None:
        stream = {
            **self.payload()["streams"][0],
            "url": "http://127.0.0.1/private-video",
            "resolver": "page",
            "size": None,
        }
        with self.assertRaises(MediaPlanError) as raised:
            self.coordinator.create_plan(self.payload(streams=[stream]))
        self.assertEqual(raised.exception.code, "invalid_page_resolver_url")

    def test_youtube_resolver_uses_exact_quality_and_ephemeral_cookie_file(self) -> None:
        class FakeProcess:
            returncode = 0

            def communicate(self):
                return (
                    "https://rr.example.googlevideo.com/videoplayback?itag=271\n"
                    "https://rr.example.googlevideo.com/videoplayback?itag=251\n",
                    "",
                )

            def terminate(self):
                self.returncode = 1

        process = FakeProcess()
        with patch("idm_eagle_bridge.media.resolve_media_tool", side_effect=lambda name: self.root / f"{name}.exe"), patch(
            "idm_eagle_bridge.media.subprocess.Popen", return_value=process
        ) as popen:
            streams = self.coordinator._resolve_youtube_streams(
                "plan-youtube",
                {
                    "url": "https://www.youtube.com/watch?v=pIzs1qe-aBc",
                    "resolver": "youtube",
                    "preferred_quality": "1440p",
                    "duration": 3207,
                    "headers": {
                        "cookie": "SAPISID=top-secret==; SIDCC=other-secret",
                        "user-agent": "Chrome/Test",
                        "referer": "https://www.youtube.com/watch?v=pIzs1qe-aBc",
                    },
                },
                self.root / "resolver-work",
            )
        command = popen.call_args.args[0]
        self.assertIn("bestvideo[height=1440][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=1440]+bestaudio/best[height=1440]", command)
        self.assertNotIn("top-secret", " ".join(str(value) for value in command))
        cookie_path = Path(command[command.index("--cookies") + 1])
        self.assertFalse(cookie_path.exists(), "the resolver cookie file must be removed immediately")
        self.assertEqual([stream["role"] for stream in streams], ["video", "audio"])
        self.assertTrue(all(stream["headers"]["cookie"] == "SAPISID=top-secret==; SIDCC=other-secret" for stream in streams))

    def test_blob_url_is_rejected_instead_of_falling_back_to_browser_download(self) -> None:
        stream = {**self.payload()["streams"][0], "url": "blob:https://example.com/id"}
        with self.assertRaisesRegex(MediaPlanError, "blob"):
            self.coordinator.create_plan(self.payload(streams=[stream]))
        self.assertEqual(self.coordinator.list_plans(), [])

    def test_fixed_byte_range_mp4_is_rejected_before_ffmpeg(self) -> None:
        stream = {
            **self.payload()["streams"][0],
            "url": (
                "https://media.example/v2/range/prot/"
                "cmFuZ2U9OTIwNzAwOS0xMzQ4NDE3Ng/avf/video-id.mp4"
            ),
            "size": 4_277_168,
        }
        with self.assertRaises(MediaPlanError) as raised:
            self.coordinator.create_plan(self.payload(streams=[stream]))
        self.assertEqual(raised.exception.code, "fixed_range_fragment")
        self.assertIn("分片", str(raised.exception))
        self.assertEqual(self.coordinator.list_plans(), [])

    def test_instagram_bytestart_byteend_fragment_is_rejected_before_ffmpeg(self) -> None:
        stream = {
            **self.payload()["streams"][0],
            "url": (
                "https://scontent.example.cdninstagram.com/o1/video.mp4?token=signed"
                "&bytestart=886&byteend=173864"
            ),
            "size": 172_979,
        }
        with self.assertRaises(MediaPlanError) as raised:
            self.coordinator.create_plan(self.payload(streams=[stream]))
        self.assertEqual(raised.exception.code, "fixed_range_fragment")
        self.assertEqual(self.coordinator.list_plans(), [])

    def test_explicit_range_query_is_rejected_even_when_size_reports_whole_file(self) -> None:
        stream = {
            **self.payload()["streams"][0],
            "url": "https://cdn.example/video.mp4?range=0-1023",
            "size": 50_000_000,
        }
        with self.assertRaises(MediaPlanError) as raised:
            self.coordinator.create_plan(self.payload(streams=[stream]))
        self.assertEqual(raised.exception.code, "fixed_range_fragment")

    def test_generic_page_resolver_uses_permalink_and_ephemeral_cookie_file(self) -> None:
        class FakeProcess:
            returncode = 0

            def communicate(self):
                return ("https://cdn.example/video.mp4\nhttps://cdn.example/audio.m4a\n", "")

            def terminate(self):
                self.returncode = 1

        context = {
            "url": "https://www.instagram.com/p/Da9rBuVjAGK/",
            "resolver": "page",
            "preferred_quality": "",
            "duration": 10.4,
            "headers": {
                "cookie": "sessionid=top-secret; csrftoken=other-secret",
                "user-agent": "Chrome/Test",
                "referer": "https://www.instagram.com/",
            },
        }
        process = FakeProcess()
        with patch("idm_eagle_bridge.media.resolve_media_tool", side_effect=lambda name: self.root / f"{name}.exe"), patch(
            "idm_eagle_bridge.media.subprocess.Popen", return_value=process
        ) as popen:
            streams = self.coordinator._resolve_page_streams(
                "plan-page", context, self.root / "page-resolver-work"
            )
        command = popen.call_args.args[0]
        self.assertIn("bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]", command)
        self.assertNotIn("top-secret", " ".join(str(value) for value in command))
        cookie_path = Path(command[command.index("--cookies") + 1])
        self.assertFalse(cookie_path.exists(), "generic resolver cookies must be deleted immediately")
        self.assertEqual([stream["role"] for stream in streams], ["video", "audio"])
        self.assertTrue(all(stream["resolver"] == "" for stream in streams))

    def test_desktop_downloads_direct_media_preserves_subtitle_and_queues_eagle(self) -> None:
        media_root = self.root / "direct"
        media_root.mkdir()
        video = media_root / "video.mp4"
        subtitle = media_root / "subtitle.vtt"
        self._make_video(video)
        subtitle.write_text("WEBVTT\n\n00:00.000 --> 00:00.500\n测试\n", encoding="utf-8")
        server, thread = self._start_server(media_root)
        port = server.server_address[1]
        try:
            streams = [
                {
                    "url": f"http://127.0.0.1:{port}/video.mp4?token=ephemeral",
                    "role": "video",
                    "name": "video.mp4",
                    "extension": "mp4",
                    "mimeType": "video/mp4",
                    "size": video.stat().st_size,
                    "duration": 1,
                    "drm": False,
                },
                {
                    "url": f"http://127.0.0.1:{port}/subtitle.vtt?token=ephemeral",
                    "role": "subtitle",
                    "name": "简体中文.vtt",
                    "extension": "vtt",
                    "mimeType": "text/vtt",
                    "language": "zh-CN",
                    "drm": False,
                },
            ]
            download_root = self.root / "desktop-downloads"
            with patch.dict(os.environ, {"IDM_EAGLE_DOWNLOAD_ROOT": str(download_root)}):
                plan = self.coordinator.create_plan(
                    self.payload(
                        outputName="本机直链.mp4",
                        streams=streams,
                        runtimeHeaders=[{}, {}],
                    )
                )
                result = self._wait(plan["id"])
            self.assertEqual(result["status"], "ready_to_import", result.get("error_message"))
            self.assertEqual(result["route"], "desktop")
            self.assertEqual(result["progress"], 90)
            self.assertTrue(Path(result["final_path"]).is_file())
            self.assertTrue(Path(result["preview_path"]).is_file())
            self.assertTrue(list(Path(result["final_path"]).parent.glob("本机直链.zh-CN.vtt")))
            self.assertIsNotNone(result["job_id"])
            self.assertEqual(
                self.database.get_job(result["job_id"])["source_url"],
                "https://www.bilibili.com/video/BV1test",
            )
            self.assertTrue(self.ready.called)
            self.database.update_job(
                result["job_id"], status="imported", completed_at=time.time()
            )
            imported = self.coordinator.get_plan(plan["id"])
            self.assertEqual(imported["status"], "imported")
            self.assertEqual(imported["progress"], 100)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_download_only_uses_desktop_and_does_not_create_eagle_job(self) -> None:
        media_root = self.root / "download-only"
        media_root.mkdir()
        video = media_root / "video.mp4"
        self._make_video(video, "orange")
        server, thread = self._start_server(media_root)
        port = server.server_address[1]
        try:
            stream = {
                **self.payload()["streams"][0],
                "url": f"http://127.0.0.1:{port}/video.mp4",
                "size": video.stat().st_size,
                "duration": 1,
            }
            with patch.dict(
                os.environ, {"IDM_EAGLE_DOWNLOAD_ROOT": str(self.root / "only-root")}
            ):
                plan = self.coordinator.create_plan(
                    self.payload(
                        streams=[stream],
                        runtimeHeaders=[{}],
                        importToEagle=False,
                        outputName="仅下载.mp4",
                    )
                )
                result = self._wait(plan["id"])
            self.assertEqual(result["status"], "completed_local", result.get("error_message"))
            self.assertEqual(result["progress"], 100)
            self.assertIsNone(result["job_id"])
            self.assertTrue(Path(result["final_path"]).is_file())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_direct_download_rejects_duration_identity_mismatch(self) -> None:
        media_root = self.root / "duration-mismatch"
        media_root.mkdir()
        video = media_root / "video.mp4"
        self._make_video(video, "purple", seconds=1)
        server, thread = self._start_server(media_root)
        port = server.server_address[1]
        try:
            stream = {
                **self.payload()["streams"][0],
                "url": f"http://127.0.0.1:{port}/video.mp4",
                "size": video.stat().st_size,
                "duration": 12,
            }
            with patch.dict(
                os.environ, {"IDM_EAGLE_DOWNLOAD_ROOT": str(self.root / "mismatch-root")}
            ):
                plan = self.coordinator.create_plan(
                    self.payload(
                        streams=[stream],
                        runtimeHeaders=[{}],
                        importToEagle=False,
                        outputName="不应交付的错配视频.mp4",
                    )
                )
                result = self._wait(plan["id"])
            self.assertEqual(result["status"], "retry")
            self.assertEqual(result["error_code"], "output_duration_mismatch")
            self.assertIsNone(result["final_path"])
            self.assertFalse(
                list((self.root / "mismatch-root" / "已完成").glob("不应交付的错配视频*.mp4"))
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_desktop_downloads_protected_separate_video_and_audio(self) -> None:
        ffmpeg, ffprobe = self._media_tools()
        media_root = self.root / "protected"
        media_root.mkdir()
        video_path = media_root / "video.m4s"
        audio_path = media_root / "audio.m4s"
        common = {"capture_output": True, "text": True, "timeout": 60, "check": True}
        subprocess.run(
            [
                str(ffmpeg), "-hide_banner", "-y", "-f", "lavfi", "-i",
                "color=c=purple:s=320x180:r=25", "-t", "1", "-an", "-c:v",
                "libx264", "-pix_fmt", "yuv420p", "-f", "mp4", str(video_path),
            ],
            **common,
        )
        subprocess.run(
            [
                str(ffmpeg), "-hide_banner", "-y", "-f", "lavfi", "-i",
                "sine=frequency=660:sample_rate=48000", "-t", "1", "-vn", "-c:a",
                "aac", "-f", "mp4", str(audio_path),
            ],
            **common,
        )
        required_referer = "https://www.bilibili.com/video/BV1protected"
        required_user_agent = "Mozilla/5.0 Protected-Media-Test"

        class ProtectedHandler(QuietHandler):
            def do_GET(self) -> None:
                if (
                    self.headers.get("Referer") != required_referer
                    or self.headers.get("User-Agent") != required_user_agent
                ):
                    self.send_error(403)
                    return
                super().do_GET()

        server, thread = self._start_server(media_root, ProtectedHandler)
        port = server.server_address[1]
        try:
            streams = [
                {
                    "url": f"http://127.0.0.1:{port}/video.m4s?token=ephemeral",
                    "role": "video", "name": "video.m4s", "extension": "m4s",
                    "mimeType": "video/mp4", "size": video_path.stat().st_size,
                    "duration": 1, "drm": False,
                },
                {
                    "url": f"http://127.0.0.1:{port}/audio.m4s?token=ephemeral",
                    "role": "audio", "name": "audio.m4s", "extension": "m4s",
                    "mimeType": "audio/mp4", "size": audio_path.stat().st_size,
                    "duration": 1, "drm": False,
                },
            ]
            headers = {"referer": required_referer, "user-agent": required_user_agent}
            with patch.dict(
                os.environ, {"IDM_EAGLE_DOWNLOAD_ROOT": str(self.root / "protected-root")}
            ):
                plan = self.coordinator.create_plan(
                    self.payload(
                        pageUrl=required_referer,
                        outputName="受保护分轨.mp4",
                        mergeMode="local_streamcopy",
                        streams=streams,
                        runtimeHeaders=[headers, headers],
                    )
                )
                result = self._wait(plan["id"])
            self.assertEqual(result["status"], "ready_to_import", result.get("error_message"))
            probe = subprocess.run(
                [
                    str(ffprobe), "-v", "error", "-show_entries", "stream=codec_type",
                    "-of", "csv=p=0", str(result["final_path"]),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            self.assertEqual(set(probe.stdout.split()), {"video", "audio"})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_desktop_downloads_aes128_hls_manifest(self) -> None:
        ffmpeg, ffprobe = self._media_tools()
        hls_root = self.root / "hls"
        hls_root.mkdir()
        server, thread = self._start_server(hls_root)
        port = server.server_address[1]
        try:
            key_path = hls_root / "enc.key"
            key_path.write_bytes(b"0123456789abcdef")
            key_info = hls_root / "enc.keyinfo"
            key_info.write_text(
                f"http://127.0.0.1:{port}/enc.key\n{key_path}\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    str(ffmpeg), "-hide_banner", "-y", "-f", "lavfi", "-i",
                    "color=c=green:s=320x180:r=25", "-f", "lavfi", "-i",
                    "sine=frequency=440:sample_rate=48000", "-t", "2", "-c:v",
                    "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-f", "hls",
                    "-hls_time", "0.5", "-hls_list_size", "0", "-hls_key_info_file",
                    str(key_info), str(hls_root / "index.m3u8"),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
            stream = {
                "url": f"http://127.0.0.1:{port}/index.m3u8?token=ephemeral",
                "role": "media",
                "name": "index.m3u8",
                "extension": "m3u8",
                "mimeType": "application/vnd.apple.mpegurl",
                "duration": 2,
                "drm": False,
            }
            with patch.dict(
                os.environ, {"IDM_EAGLE_DOWNLOAD_ROOT": str(self.root / "hls-root")}
            ):
                plan = self.coordinator.create_plan(
                    self.payload(
                        outputName="AES-128 HLS.mkv",
                        outputContainer="mkv",
                        mergeMode="local_streamcopy",
                        streams=[stream],
                        runtimeHeaders=[{"referer": f"http://127.0.0.1:{port}/page"}],
                    )
                )
                result = self._wait(plan["id"])
            self.assertEqual(result["status"], "ready_to_import", result.get("error_message"))
            probe = subprocess.run(
                [
                    str(ffprobe), "-v", "error", "-show_entries", "stream=codec_type",
                    "-of", "csv=p=0", str(result["final_path"]),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            self.assertEqual(set(probe.stdout.split()), {"video", "audio"})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_failed_plan_can_retry_only_while_memory_context_exists(self) -> None:
        with patch.object(self.coordinator, "schedule"):
            plan = self.coordinator.create_plan(self.payload())
            with self.database.session() as connection:
                connection.execute(
                    "UPDATE download_plans SET status = 'retry' WHERE id = ?",
                    (plan["id"],),
                )
            retried = self.coordinator.retry_plan(plan["id"])
        self.assertEqual(retried["status"], "queued")

        with self.database.session() as connection:
            connection.execute(
                "UPDATE download_plans SET status = 'downloading' WHERE id = ?",
                (plan["id"],),
            )
        reopened = MediaCoordinator(self.database, workers=1)
        try:
            recovered = reopened.get_plan(plan["id"])
            self.assertEqual(recovered["status"], "retry")
            self.assertEqual(recovered["error_code"], "download_context_expired")
            with self.assertRaisesRegex(MediaPlanError, "来源网页"):
                reopened.retry_plan(plan["id"])
        finally:
            reopened.close()

    def test_queued_plan_can_be_canceled_without_browser_download(self) -> None:
        with patch.object(self.coordinator, "schedule"):
            plan = self.coordinator.create_plan(self.payload())
        stopped = self.coordinator.stop_plan(plan["id"])
        self.assertEqual(stopped["status"], "canceled")

    def test_completed_plan_preview_is_bounded_to_program_preview_directory(self) -> None:
        station_root = self.root / "preview-root"
        preview = station_root / "下载中转站" / "预览" / "frame.png"
        preview.parent.mkdir(parents=True)
        preview.write_bytes(b"\x89PNG\r\n\x1a\n" + b"preview-frame")
        with (
            patch.dict(os.environ, {"IDM_EAGLE_DOWNLOAD_ROOT": str(station_root)}),
            patch.object(self.coordinator, "schedule"),
        ):
            plan = self.coordinator.create_plan(self.payload())
            with self.database.session() as connection:
                connection.execute(
                    "UPDATE download_plans SET preview_path = ? WHERE id = ?",
                    (str(preview), plan["id"]),
                )
            result = self.coordinator.get_plan_preview(plan["id"])

        self.assertEqual(result["mimeType"], "image/png")
        self.assertTrue(result["dataUrl"].startswith("data:image/png;base64,"))

        outside = self.root / "outside.png"
        outside.write_bytes(b"\x89PNG\r\n\x1a\nnot-owned")
        with self.database.session() as connection:
            connection.execute(
                "UPDATE download_plans SET preview_path = ? WHERE id = ?",
                (str(outside), plan["id"]),
            )
        with (
            patch.dict(os.environ, {"IDM_EAGLE_DOWNLOAD_ROOT": str(station_root)}),
            self.assertRaisesRegex(MediaPlanError, "预览"),
        ):
            self.coordinator.get_plan_preview(plan["id"])

    def test_open_output_uses_only_program_owned_completed_directory(self) -> None:
        station_root = self.root / "open-root"
        completed = station_root / "下载中转站" / "已完成"
        completed.mkdir(parents=True)
        output = completed / "finished.mp4"
        output.write_bytes(b"media")
        with (
            patch.dict(os.environ, {"IDM_EAGLE_DOWNLOAD_ROOT": str(station_root)}),
            patch.object(self.coordinator, "schedule"),
        ):
            plan = self.coordinator.create_plan(self.payload())
            with self.database.session() as connection:
                connection.execute(
                    "UPDATE download_plans SET status = 'completed_local', progress = 100, final_path = ? WHERE id = ?",
                    (str(output), plan["id"]),
                )
            with patch.object(os, "startfile", create=True) as startfile:
                result = self.coordinator.open_plan_output(plan["id"])

        self.assertTrue(result["opened"])
        self.assertEqual(result["fileName"], "finished.mp4")
        startfile.assert_called_once_with(str(completed.resolve()))

        outside = self.root / "outside.mp4"
        outside.write_bytes(b"media")
        with self.database.session() as connection:
            connection.execute(
                "UPDATE download_plans SET final_path = ? WHERE id = ?",
                (str(outside), plan["id"]),
            )
        with (
            patch.dict(os.environ, {"IDM_EAGLE_DOWNLOAD_ROOT": str(station_root)}),
            self.assertRaisesRegex(MediaPlanError, "下载目录"),
        ):
            self.coordinator.open_plan_output(plan["id"])

    def test_completed_local_plan_can_be_queued_for_eagle_without_redownload(self) -> None:
        station_root = self.root / "import-existing-root"
        completed = station_root / "下载中转站" / "已完成"
        completed.mkdir(parents=True)
        output = completed / "already-downloaded.mp4"
        output.write_bytes(b"already-downloaded-media")
        with (
            patch.dict(os.environ, {"IDM_EAGLE_DOWNLOAD_ROOT": str(station_root)}),
            patch.object(self.coordinator, "schedule"),
        ):
            plan = self.coordinator.create_plan(self.payload(importToEagle=False))
            with self.database.session() as connection:
                connection.execute(
                    "UPDATE download_plans SET status = 'completed_local', progress = 100, final_path = ? WHERE id = ?",
                    (str(output), plan["id"]),
                )
            result = self.coordinator.import_completed_plan(plan["id"])

        self.assertEqual(result["status"], "ready_to_import")
        self.assertEqual(result["progress"], 90)
        self.assertEqual(result["import_to_eagle"], 1)
        self.assertIsNotNone(result["job_id"])
        job = self.database.get_job(result["job_id"])
        self.assertEqual(job["file_path"], str(output.resolve()))
        self.assertEqual(job["source_url"], "https://www.bilibili.com/video/BV1test")

        repeated = self.coordinator.import_completed_plan(plan["id"])
        self.assertEqual(repeated["job_id"], result["job_id"], "repeated clicks must not create duplicate Eagle jobs")

    def test_drm_plan_is_blocked_before_rows_are_created(self) -> None:
        streams = list(self.payload()["streams"])
        streams[0] = {**streams[0], "drm": True}
        with self.assertRaisesRegex(MediaPlanError, "DRM"):
            self.coordinator.create_plan(self.payload(streams=streams))
        self.assertEqual(self.coordinator.list_plans(), [])

    def test_output_name_and_url_are_sanitized(self) -> None:
        self.assertEqual(safe_output_name("CON?.mp4", "mp4"), "CON_.mp4")
        self.assertEqual(
            redact_media_url("https://cdn.example/a.mp4?token=secret#part"),
            "https://cdn.example/a.mp4",
        )


if __name__ == "__main__":
    unittest.main()
