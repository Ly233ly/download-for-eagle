from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from idm_eagle_bridge.hook import main


class HookTests(unittest.TestCase):
    def test_starts_assistant_hidden_when_no_listener_exists(self) -> None:
        video = str(Path("C:/Downloads/new-video.mp4"))
        with (
            patch("idm_eagle_bridge.hook.Database") as database_type,
            patch(
                "idm_eagle_bridge.hook.notify_processing_service",
                return_value=False,
            ),
            patch(
                "idm_eagle_bridge.hook.start_assistant_hidden",
                return_value=True,
            ) as start,
        ):
            self.assertEqual(main([video]), 0)

        database_type.return_value.add_job.assert_called_once_with(video)
        start.assert_called_once_with()

    def test_running_assistant_is_only_woken(self) -> None:
        video = str(Path("C:/Downloads/new-video.mp4"))
        with (
            patch("idm_eagle_bridge.hook.Database"),
            patch(
                "idm_eagle_bridge.hook.notify_processing_service",
                return_value=True,
            ),
            patch("idm_eagle_bridge.hook.start_assistant_hidden") as start,
        ):
            self.assertEqual(main([video]), 0)

        start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
