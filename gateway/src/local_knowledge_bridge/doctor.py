from __future__ import annotations

from pathlib import Path

from .config import enabled_endnote_libraries
from .retrieval import index_status
from .source_guard import endnote_data_dir


def doctor_report(config: dict, service_health: dict | None = None) -> dict:
    obsidian_path = config.get("obsidian_vault", "")
    endnote_libraries = enabled_endnote_libraries(config)
    report = {
        "obsidian": {
            "configured": bool(obsidian_path),
            "path": obsidian_path,
            "exists": bool(obsidian_path) and Path(obsidian_path).exists(),
        },
        "endnote": [
            {
                "id": item["id"],
                "name": item["name"],
                "path": item["path"],
                "library_exists": Path(item["path"]).exists(),
                "data_dir_exists": endnote_data_dir(item["path"]).exists(),
                "enabled": item.get("enabled", True),
            }
            for item in endnote_libraries
        ],
        "index": index_status(config),
        "service": service_health or {"running": False},
    }
    return report
