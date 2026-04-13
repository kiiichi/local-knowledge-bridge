from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import PROFILE_SETTINGS, SERVICE_HOST, SERVICE_PORT
from .paths import config_path, config_template_path, default_index_db_path, gateway_root, runtime_root


def _merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _normalize_path(value: str | None) -> str:
    if not value:
        return ""
    return str(Path(value).expanduser())


def _default_paths() -> dict[str, Any]:
    return {
        "runtime": {"python_home": str(runtime_root())},
        "index": {"db_path": str(default_index_db_path())},
        "service": {"host": SERVICE_HOST, "port": SERVICE_PORT},
    }


def load_template_base() -> dict[str, Any]:
    with config_template_path().open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    data = _merge(data, _default_paths())
    data.setdefault("retrieval", {})
    data["retrieval"].setdefault("profile_default", "fast")
    return data


def _normalize_endnote_libraries(config: dict[str, Any]) -> list[dict[str, Any]]:
    libraries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, item in enumerate(config.get("endnote_libraries", []), start=1):
        path = _normalize_path(item.get("path"))
        if not path or path in seen:
            continue
        seen.add(path)
        libraries.append(
            {
                "id": item.get("id") or f"endnote-{idx}",
                "name": item.get("name") or Path(path).stem,
                "path": path,
                "enabled": bool(item.get("enabled", True)),
            }
        )
    single_path = _normalize_path(config.get("endnote_library"))
    if single_path and single_path not in seen:
        libraries.append(
            {
                "id": f"endnote-{len(libraries) + 1}",
                "name": Path(single_path).stem,
                "path": single_path,
                "enabled": True,
            }
        )
    return libraries


def _normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    normalized = _merge(load_template_base(), config)
    normalized["obsidian_vault"] = _normalize_path(normalized.get("obsidian_vault"))
    normalized["endnote_libraries"] = _normalize_endnote_libraries(normalized)

    enabled_paths = [item["path"] for item in normalized["endnote_libraries"] if item.get("enabled")]
    normalized["endnote_library"] = _normalize_path(normalized.get("endnote_library")) or (enabled_paths[0] if enabled_paths else "")

    normalized.setdefault("exclude_dirs", [])
    normalized.setdefault("runtime", {})
    normalized.setdefault("index", {})
    normalized.setdefault("models", {})
    normalized.setdefault("service", {})
    normalized.setdefault("retrieval", {})

    if not normalized["runtime"].get("python_home"):
        normalized["runtime"]["python_home"] = str(runtime_root())
    if not normalized["index"].get("db_path"):
        normalized["index"]["db_path"] = str(default_index_db_path())
    if not normalized["service"].get("host"):
        normalized["service"]["host"] = SERVICE_HOST
    service_port = normalized["service"].get("port")
    if not service_port or int(service_port) == 51234:
        normalized["service"]["port"] = SERVICE_PORT
    if not normalized["retrieval"].get("profile_default"):
        normalized["retrieval"]["profile_default"] = "fast"
    return normalized


def load_template() -> dict[str, Any]:
    return _normalize_config(load_template_base())


def ensure_config_exists() -> Path:
    path = config_path()
    if not path.exists():
        save_config(load_template())
    return path


def load_config() -> dict[str, Any]:
    ensure_config_exists()
    with config_path().open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return _normalize_config(_merge(load_template_base(), raw))


def save_config(data: dict[str, Any]) -> None:
    normalized = _normalize_config(data)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(normalized, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def gateway_local_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = gateway_root() / path
    return path.resolve()


def selected_profile(config: dict[str, Any], profile: str | None) -> str:
    name = (profile or config.get("retrieval", {}).get("profile_default") or "fast").lower()
    if name not in PROFILE_SETTINGS:
        raise SystemExit(f"Unsupported profile: {name}")
    return name


def profile_settings(config: dict[str, Any], profile: str | None) -> dict[str, Any]:
    name = selected_profile(config, profile)
    settings = dict(PROFILE_SETTINGS[name])
    if name == "balanced":
        retrieval = config.get("retrieval", {})
        settings["top_k_recall"] = int(retrieval.get("top_k_recall", settings["top_k_recall"]))
        settings["top_k_evidence"] = int(retrieval.get("top_k_evidence", settings["top_k_evidence"]))
    return settings


def enabled_endnote_libraries(config: dict[str, Any], selector: str | None = None) -> list[dict[str, Any]]:
    libraries = [item for item in config.get("endnote_libraries", []) if item.get("enabled")]
    if selector is None:
        return libraries
    selector_lower = selector.lower()
    return [
        item
        for item in libraries
        if item.get("id", "").lower() == selector_lower
        or item.get("name", "").lower() == selector_lower
        or item.get("path", "").lower() == selector_lower
    ]
