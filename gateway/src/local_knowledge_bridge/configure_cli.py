from __future__ import annotations

import argparse
from pathlib import Path

from .cli_io import configure_output, print_json
from .config import load_config, save_config


ENDNOTE_MAX_LIBRARIES = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update Local Knowledge Bridge source paths.")
    parser.add_argument("--show", action="store_true", help="Print the current configuration.")
    parser.add_argument("--obsidian", help="Set Obsidian vault path.")
    parser.add_argument("--zotero", help="Set Zotero zotero.sqlite path.")
    parser.add_argument("--remove-zotero", action="store_true", help="Remove the configured Zotero path.")
    parser.add_argument("--endnote", help="Add or update an EndNote .enl path.")
    parser.add_argument("--endnote-name", help="Display name for the EndNote library being added or updated.")
    parser.add_argument("--disable-endnote", help="Disable an EndNote library by id or name.")
    parser.add_argument("--folder-library", help="Add or update a folder knowledge source path.")
    parser.add_argument("--folder-name", help="Display name for the folder knowledge source.")
    parser.add_argument("--disable-folder", help="Disable a folder knowledge source by id, name, or path.")
    parser.add_argument("--remove-folder", help="Remove a folder knowledge source by id, name, or path.")
    return parser.parse_args()


def _normalize_endnote_id(name: str, index: int) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or f"endnote-{index}"


def _normalize_folder_id(name: str, index: int) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or f"folder-{index}"


def _update_endnote_libraries(config: dict, path: str, display_name: str | None) -> None:
    libraries = list(config.get("endnote_libraries", []))
    normalized_path = str(Path(path).expanduser())
    display_name = display_name or Path(path).stem
    for item in libraries:
        if item.get("path") == normalized_path:
            item["name"] = display_name
            item["enabled"] = True
            config["endnote_library"] = normalized_path
            config["endnote_libraries"] = libraries
            return
    if len(libraries) >= ENDNOTE_MAX_LIBRARIES:
        raise SystemExit(f"At most {ENDNOTE_MAX_LIBRARIES} EndNote libraries are supported in Local Knowledge Bridge V1.")
    library_id = _normalize_endnote_id(display_name, len(libraries) + 1)
    libraries.append(
        {
            "id": library_id,
            "name": display_name,
            "path": normalized_path,
            "enabled": True,
        }
    )
    config["endnote_library"] = normalized_path
    config["endnote_libraries"] = libraries


def _disable_endnote(config: dict, value: str) -> None:
    libraries = list(config.get("endnote_libraries", []))
    for item in libraries:
        if item.get("id") == value or item.get("name") == value:
            item["enabled"] = False
    config["endnote_libraries"] = libraries
    enabled_paths = [item.get("path", "") for item in libraries if item.get("enabled")]
    config["endnote_library"] = enabled_paths[0] if enabled_paths else ""


def _update_folder_libraries(config: dict, path: str, display_name: str | None) -> None:
    libraries = list(config.get("folder_libraries", []))
    normalized_path = str(Path(path).expanduser())
    display_name = display_name or Path(path).name or f"Folder {len(libraries) + 1}"
    for item in libraries:
        if item.get("path") == normalized_path:
            item["name"] = display_name
            item["enabled"] = True
            config["folder_libraries"] = libraries
            return
    libraries.append(
        {
            "id": _normalize_folder_id(display_name, len(libraries) + 1),
            "name": display_name,
            "path": normalized_path,
            "enabled": True,
        }
    )
    config["folder_libraries"] = libraries


def _matches_library(item: dict, value: str) -> bool:
    return value in {str(item.get("id", "")), str(item.get("name", "")), str(item.get("path", ""))}


def _disable_folder(config: dict, value: str) -> None:
    libraries = list(config.get("folder_libraries", []))
    for item in libraries:
        if _matches_library(item, value):
            item["enabled"] = False
    config["folder_libraries"] = libraries


def _remove_folder(config: dict, value: str) -> None:
    config["folder_libraries"] = [
        item for item in list(config.get("folder_libraries", [])) if not _matches_library(item, value)
    ]


def main() -> int:
    configure_output()
    args = parse_args()
    config = load_config()
    changed = False

    if args.obsidian is not None:
        config["obsidian_vault"] = str(Path(args.obsidian).expanduser())
        changed = True

    if args.zotero is not None:
        config["zotero_sqlite"] = str(Path(args.zotero).expanduser())
        changed = True

    if args.remove_zotero:
        config["zotero_sqlite"] = ""
        changed = True

    if args.endnote is not None:
        _update_endnote_libraries(config, args.endnote, args.endnote_name)
        changed = True

    if args.disable_endnote is not None:
        _disable_endnote(config, args.disable_endnote)
        changed = True

    if args.folder_library is not None:
        _update_folder_libraries(config, args.folder_library, args.folder_name)
        changed = True

    if args.disable_folder is not None:
        _disable_folder(config, args.disable_folder)
        changed = True

    if args.remove_folder is not None:
        _remove_folder(config, args.remove_folder)
        changed = True

    if changed:
        save_config(config)

    if args.show or changed or (
        not any(
            [
                args.obsidian,
                args.zotero,
                args.remove_zotero,
                args.endnote,
                args.disable_endnote,
                args.folder_library,
                args.disable_folder,
                args.remove_folder,
            ]
        )
    ):
        print_json(config)

    return 0
