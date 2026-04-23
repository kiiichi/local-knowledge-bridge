from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from local_knowledge_bridge import versioning


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class VersioningTests(unittest.TestCase):
    def test_version_compare_handles_prefixes_and_dev_suffixes(self) -> None:
        self.assertGreater(versioning._compare_versions("v1.4.2026.10104", "1.4.2026.9903"), 0)
        self.assertGreater(versioning._compare_versions("0.1.0", "0.1.0-dev"), 0)
        self.assertGreater(versioning._compare_versions("0.1.0", "0.1.0.dev0"), 0)
        self.assertEqual(versioning._compare_versions("v0.1.0", "0.1.0"), 0)

    def test_get_version_status_stays_local_without_refresh(self) -> None:
        with (
            patch.object(versioning, "load_app_version", return_value="0.1.0"),
            patch.object(versioning.request, "urlopen") as urlopen,
        ):
            status = versioning.get_version_status()

        urlopen.assert_not_called()
        self.assertEqual(status["source"], "local")
        self.assertFalse(status["update_available"])

    def test_get_version_status_fetches_remote_release_on_refresh(self) -> None:
        release = {
            "tag_name": "v0.2.0",
            "name": "v0.2.0",
            "html_url": "https://example.test/releases/v0.2.0",
            "published_at": "2026-04-22T00:00:00Z",
            "prerelease": False,
        }
        config = {"updates": {"release_api_url": "https://example.test/latest", "timeout_seconds": 1}}

        with (
            patch.object(versioning, "load_app_version", return_value="0.1.0-dev"),
            patch.object(versioning.request, "urlopen", return_value=FakeResponse(release)) as urlopen,
        ):
            status = versioning.get_version_status(force_refresh=True, config=config)

        urlopen.assert_called_once()
        self.assertEqual(status["source"], "remote")
        self.assertEqual(status["latest_version"], "0.2.0")
        self.assertEqual(status["release_tag"], "v0.2.0")
        self.assertTrue(status["update_available"])
        self.assertEqual(status["release_url"], release["html_url"])

    def test_get_version_status_reports_remote_errors_without_failing_doctor(self) -> None:
        config = {"updates": {"release_api_url": "https://example.test/latest", "timeout_seconds": 1}}

        with (
            patch.object(versioning, "load_app_version", return_value="0.1.0"),
            patch.object(versioning.request, "urlopen", side_effect=OSError("network down")),
        ):
            status = versioning.get_version_status(force_refresh=True, config=config)

        self.assertEqual(status["source"], "remote-error")
        self.assertEqual(status["latest_version"], "0.1.0")
        self.assertFalse(status["update_available"])
        self.assertIn("network down", status["error"])

    def test_get_version_status_treats_missing_latest_release_as_empty_remote(self) -> None:
        config = {"updates": {"release_api_url": "https://example.test/latest", "timeout_seconds": 1}}
        not_found = versioning.error.HTTPError("https://example.test/latest", 404, "Not Found", None, None)

        with (
            patch.object(versioning, "load_app_version", return_value="0.1.0"),
            patch.object(versioning.request, "urlopen", side_effect=not_found),
        ):
            status = versioning.get_version_status(force_refresh=True, config=config)

        self.assertEqual(status["source"], "remote-empty")
        self.assertEqual(status["latest_version"], "0.1.0")
        self.assertFalse(status["update_available"])
        self.assertIn("No public release", status["detail"])

    def test_get_version_status_can_select_from_release_lists(self) -> None:
        releases = [
            {"tag_name": "v0.3.0-rc1", "prerelease": True, "draft": False},
            {"tag_name": "v0.2.0", "prerelease": False, "draft": False},
        ]
        config = {"updates": {"release_api_url": "https://example.test/releases"}}

        with (
            patch.object(versioning, "load_app_version", return_value="0.1.0"),
            patch.object(versioning.request, "urlopen", return_value=FakeResponse(releases)),
        ):
            status = versioning.get_version_status(force_refresh=True, config=config)

        self.assertEqual(status["latest_version"], "0.2.0")
        self.assertFalse(status["prerelease"])


if __name__ == "__main__":
    unittest.main()
