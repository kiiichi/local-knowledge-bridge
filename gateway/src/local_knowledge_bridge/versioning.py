from __future__ import annotations

import json
import platform
import re
import time
from urllib import error, request

from .constants import DEFAULT_RELEASE_API_URL, DEFAULT_RELEASE_URL, DEFAULT_UPDATE_TIMEOUT_SECONDS
from .paths import version_path, version_prefix_path


def load_app_version() -> str:
    version = "0.0.0"
    if version_path().exists():
        version = version_path().read_text(encoding="utf-8").strip() or version
    if version_prefix_path().exists():
        prefix = version_prefix_path().read_text(encoding="utf-8").strip()
        if prefix and prefix != "0" and not version.startswith(f"{prefix}."):
            version = f"{prefix}.{version}"
    return version


def _clean_version_text(value: str | None) -> str:
    text = str(value or "").strip()
    if len(text) > 1 and text[0].lower() == "v" and text[1].isdigit():
        return text[1:]
    return text


def _split_version(value: str) -> tuple[list[int], int, int]:
    text = _clean_version_text(value).lower()
    text = text.split("+", 1)[0]
    pre_match = re.search(r"(?:(?<=\d)|(?<=[.\-_]))(dev|alpha|beta|rc|a|b)(\d*)", text)
    if pre_match:
        primary = text[: pre_match.start()].rstrip(".-_")
        suffix = text[pre_match.start() :]
    else:
        primary, _, suffix = text.partition("-")
    numbers = [int(part) for part in re.findall(r"\d+", primary)]
    if not numbers:
        numbers = [0]

    prerelease_rank = 0
    prerelease_number = 0
    if suffix:
        prerelease_rank = -5
        prerelease_ranks = {
            "dev": -4,
            "alpha": -3,
            "a": -3,
            "beta": -2,
            "b": -2,
            "rc": -1,
        }
        for label, rank in prerelease_ranks.items():
            if re.search(rf"(^|[.\-_]){re.escape(label)}($|[.\-_\d])", suffix):
                prerelease_rank = rank
                break
        match = re.search(r"\d+", suffix)
        if match:
            prerelease_number = int(match.group(0))
    return numbers, prerelease_rank, prerelease_number


def _compare_versions(left: str, right: str) -> int:
    left_numbers, left_rank, left_pre = _split_version(left)
    right_numbers, right_rank, right_pre = _split_version(right)
    width = max(len(left_numbers), len(right_numbers))
    for left_item, right_item in zip(
        left_numbers + [0] * (width - len(left_numbers)),
        right_numbers + [0] * (width - len(right_numbers)),
    ):
        if left_item != right_item:
            return 1 if left_item > right_item else -1
    if left_rank != right_rank:
        return 1 if left_rank > right_rank else -1
    if left_pre != right_pre:
        return 1 if left_pre > right_pre else -1
    return 0


def _update_config(config: dict | None) -> dict:
    if not isinstance(config, dict):
        config = {}
    raw = config.get("updates", {})
    updates = raw if isinstance(raw, dict) else {}
    try:
        timeout_seconds = float(updates.get("timeout_seconds") or DEFAULT_UPDATE_TIMEOUT_SECONDS)
    except (TypeError, ValueError):
        timeout_seconds = DEFAULT_UPDATE_TIMEOUT_SECONDS
    return {
        "enabled": bool(updates.get("enabled", True)),
        "release_api_url": str(updates.get("release_api_url") or DEFAULT_RELEASE_API_URL),
        "release_url": str(updates.get("release_url") or DEFAULT_RELEASE_URL),
        "timeout_seconds": max(0.1, timeout_seconds),
        "include_prereleases": bool(updates.get("include_prereleases", False)),
    }


def _select_release(payload: object, *, include_prereleases: bool) -> dict:
    releases = payload if isinstance(payload, list) else [payload]
    for item in releases:
        if not isinstance(item, dict):
            continue
        if item.get("draft"):
            continue
        if item.get("prerelease") and not include_prereleases:
            continue
        if item.get("tag_name") or item.get("name"):
            return item
    raise RuntimeError("No suitable release was returned by the update endpoint.")


def _fetch_remote_release(api_url: str, *, timeout_seconds: float, include_prereleases: bool) -> dict:
    http_request = request.Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json, application/json",
            "User-Agent": "local-knowledge-bridge",
        },
    )
    with request.urlopen(http_request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return _select_release(payload, include_prereleases=include_prereleases)


def _error_message(exc: BaseException) -> str:
    if isinstance(exc, error.HTTPError):
        return f"HTTP {exc.code}: {exc.reason}"
    if isinstance(exc, error.URLError):
        return str(exc.reason)
    return str(exc).strip() or exc.__class__.__name__


def _checked_at() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def get_version_status(force_refresh: bool = False, config: dict | None = None) -> dict:
    current_version = load_app_version()
    source = "local"
    base_status = {
        "current_version": current_version,
        "latest_version": current_version,
        "update_available": False,
        "source": source,
        "python_version": platform.python_version(),
    }
    if not force_refresh:
        return base_status

    updates = _update_config(config)
    if not updates["enabled"]:
        return {**base_status, "source": "local-disabled"}

    try:
        release = _fetch_remote_release(
            updates["release_api_url"],
            timeout_seconds=updates["timeout_seconds"],
            include_prereleases=updates["include_prereleases"],
        )
    except error.HTTPError as exc:
        if exc.code == 404:
            return {
                **base_status,
                "source": "remote-empty",
                "checked_at": _checked_at(),
                "release_url": updates["release_url"],
                "detail": "No public release was found at the update endpoint.",
            }
        return {
            **base_status,
            "source": "remote-error",
            "checked_at": _checked_at(),
            "release_url": updates["release_url"],
            "error": _error_message(exc),
        }
    except Exception as exc:
        return {
            **base_status,
            "source": "remote-error",
            "checked_at": _checked_at(),
            "release_url": updates["release_url"],
            "error": _error_message(exc),
        }

    release_tag = str(release.get("tag_name") or release.get("name") or "").strip()
    latest_version = _clean_version_text(release_tag)
    release_url = str(release.get("html_url") or updates["release_url"])
    return {
        "current_version": current_version,
        "latest_version": latest_version,
        "update_available": _compare_versions(latest_version, current_version) > 0,
        "source": "remote",
        "python_version": platform.python_version(),
        "checked_at": _checked_at(),
        "release_tag": release_tag,
        "release_name": release.get("name") or release_tag,
        "release_url": release_url,
        "published_at": release.get("published_at"),
        "prerelease": bool(release.get("prerelease")),
    }
