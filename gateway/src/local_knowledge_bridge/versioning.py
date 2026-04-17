from __future__ import annotations

import platform

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


def get_version_status(force_refresh: bool = False) -> dict:
    current_version = load_app_version()
    source = "local"
    if force_refresh:
        source = "local-refresh"
    return {
        "current_version": current_version,
        "latest_version": current_version,
        "update_available": False,
        "source": source,
        "python_version": platform.python_version(),
    }
