from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import config_path, config_template_path, gateway_root, runtime_root


def _default_paths() -> dict[str, Any]:
    root = gateway_root()
    return {
        "runtime": {"python_home": str(runtime_root())},
        "index": {"db_path": str(root / ".index" / "lkb_index.sqlite")},
    }


def _merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_template() -> dict[str, Any]:
    with config_template_path().open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return _merge(data, _default_paths())


def ensure_config_exists() -> Path:
    path = config_path()
    if not path.exists():
        save_config(load_template())
    return path


def load_config() -> dict[str, Any]:
    ensure_config_exists()
    with config_path().open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return _merge(load_template(), data)


def save_config(data: dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
