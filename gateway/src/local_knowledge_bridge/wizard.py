from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable

from .cli_io import configure_output
from .config import load_config, save_config
from .constants import DEFAULT_ROUTE_WEIGHTS
from .deep_models import inspect_deep_status
from .doctor import diagnose_gateway
from .paths import gateway_root, runtime_python
from .retrieval import index_status
from .source_guard import (
    resolve_endnote_components,
    validate_folder_library,
    validate_obsidian_vault,
    validate_zotero_sqlite,
)
from .terminal_ui import TerminalUI, run_logged_command


ENDNOTE_MAX_LIBRARIES = 3
InputFunc = Callable[[str], str]
PrintFunc = Callable[..., None]

WEIGHT_PRESETS = {
    "default": "Default route weights",
    "notes_first": "Prefer Obsidian notes and Zotero notes/annotations",
    "paper_fulltext_first": "Prefer EndNote/Zotero paper metadata and full text",
    "annotation_first": "Prefer Zotero annotations and notes",
    "folder_first": "Prefer configured folder knowledge sources",
}

DEEP_DEVICES = {"cuda_if_available", "cpu", "cuda"}
PROFILES = {"fast", "balanced", "deep"}


def _clamp_weight(value: float) -> float:
    return round(max(0.5, min(2.0, value)), 3)


def route_weight_preset(name: str) -> dict[str, float]:
    preset = name.strip().lower()
    weights = dict(DEFAULT_ROUTE_WEIGHTS)
    if preset == "default":
        return weights
    if preset == "notes_first":
        boosted = {"obsidian_notes", "obsidian_chunks", "zotero_notes", "zotero_annotations"}
        lowered = {"endnote_fulltext", "zotero_fulltext", "endnote_attachments", "zotero_attachments"}
        return {
            key: _clamp_weight(value * (1.2 if key in boosted else 0.9 if key in lowered else 1.0))
            for key, value in weights.items()
        }
    if preset == "paper_fulltext_first":
        boosted = {"endnote_docs", "endnote_fulltext", "zotero_docs", "zotero_fulltext"}
        return {
            key: _clamp_weight(
                value
                * (
                    1.2
                    if key in boosted
                    else 0.9
                    if key.startswith("obsidian_") or key.startswith("folder_")
                    else 1.0
                )
            )
            for key, value in weights.items()
        }
    if preset == "annotation_first":
        boosted = {"zotero_annotations", "zotero_notes"}
        lowered = {"endnote_attachments", "zotero_attachments"}
        return {
            key: _clamp_weight(value * (1.25 if key in boosted else 1.1 if key == "obsidian_chunks" else 0.9 if key in lowered else 1.0))
            for key, value in weights.items()
        }
    if preset == "folder_first":
        return {
            key: _clamp_weight(value * (1.35 if key.startswith("folder_") else 0.9))
            for key, value in weights.items()
        }
    raise SystemExit(f"Unsupported weight preset: {name}")


def apply_weight_preset(config: dict[str, Any], preset: str) -> None:
    config.setdefault("retrieval", {})
    config["retrieval"]["route_weights"] = route_weight_preset(preset)


def set_deep_device(config: dict[str, Any], device: str) -> None:
    device = device.strip().lower()
    if device not in DEEP_DEVICES:
        raise SystemExit(f"Unsupported deep device: {device}")
    config.setdefault("models", {})
    config["models"]["deep_device"] = device


def set_default_profile(config: dict[str, Any], profile: str) -> None:
    profile = profile.strip().lower()
    if profile not in PROFILES:
        raise SystemExit(f"Unsupported profile: {profile}")
    config.setdefault("retrieval", {})
    config["retrieval"]["profile_default"] = profile


def _slug(name: str, prefix: str, index: int) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or f"{prefix}-{index}"


def _system_exit_message(exc: SystemExit) -> str:
    if exc.code is None:
        return exc.__class__.__name__
    return str(exc.code).strip() or exc.__class__.__name__


def _matches_library(item: dict[str, Any], value: str) -> bool:
    return value in {str(item.get("id", "")), str(item.get("name", "")), str(item.get("path", ""))}


def _sync_endnote_primary(config: dict[str, Any]) -> None:
    paths = [str(item.get("path", "")) for item in config.get("endnote_libraries", []) if item.get("enabled")]
    config["endnote_library"] = paths[0] if paths else ""


def add_or_update_endnote_library(config: dict[str, Any], path: str, name: str | None = None) -> None:
    components = resolve_endnote_components(path)
    normalized_path = str(components["library"])
    display_name = name or Path(normalized_path).stem
    libraries = list(config.get("endnote_libraries", []))
    for item in libraries:
        if str(item.get("path", "")) == normalized_path:
            item["name"] = display_name
            item["enabled"] = True
            config["endnote_libraries"] = libraries
            _sync_endnote_primary(config)
            return
    if len(libraries) >= ENDNOTE_MAX_LIBRARIES:
        raise SystemExit(f"At most {ENDNOTE_MAX_LIBRARIES} EndNote libraries are supported.")
    libraries.append(
        {
            "id": _slug(display_name, "endnote", len(libraries) + 1),
            "name": display_name,
            "path": normalized_path,
            "enabled": True,
        }
    )
    config["endnote_libraries"] = libraries
    _sync_endnote_primary(config)


def add_or_update_folder_library(config: dict[str, Any], path: str, name: str | None = None) -> None:
    folder_path = validate_folder_library(path)
    normalized_path = str(folder_path)
    libraries = list(config.get("folder_libraries", []))
    display_name = name or Path(normalized_path).name or f"Folder {len(libraries) + 1}"
    for item in libraries:
        if str(item.get("path", "")) == normalized_path:
            item["name"] = display_name
            item["enabled"] = True
            config["folder_libraries"] = libraries
            return
    libraries.append(
        {
            "id": _slug(display_name, "folder", len(libraries) + 1),
            "name": display_name,
            "path": normalized_path,
            "enabled": True,
        }
    )
    config["folder_libraries"] = libraries


def set_library_enabled(config: dict[str, Any], key: str, selector: str, enabled: bool) -> bool:
    changed = False
    libraries = list(config.get(key, []))
    for item in libraries:
        if _matches_library(item, selector):
            item["enabled"] = enabled
            changed = True
    config[key] = libraries
    if key == "endnote_libraries":
        _sync_endnote_primary(config)
    return changed


def rename_library(config: dict[str, Any], key: str, selector: str, name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    changed = False
    libraries = list(config.get(key, []))
    for item in libraries:
        if _matches_library(item, selector):
            item["name"] = name
            changed = True
    config[key] = libraries
    return changed


def remove_library(config: dict[str, Any], key: str, selector: str) -> bool:
    libraries = list(config.get(key, []))
    kept = [item for item in libraries if not _matches_library(item, selector)]
    changed = len(kept) != len(libraries)
    config[key] = kept
    if key == "endnote_libraries":
        _sync_endnote_primary(config)
    return changed


def _source_line(name: str, item: dict[str, Any]) -> str:
    return (
        f"{name}: configured={bool(item.get('configured'))} "
        f"available={bool(item.get('available'))} compatible={bool(item.get('compatible'))}"
    )


class Wizard:
    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        input_func: InputFunc | None = None,
        print_func: PrintFunc = print,
    ) -> None:
        self.original_config = copy.deepcopy(config if config is not None else load_config())
        self.config = copy.deepcopy(self.original_config)
        self.ui = TerminalUI(input_func=input_func, print_func=print_func)
        self.input = self.ui.input
        self.print = self.ui.print
        self.dirty = False

    def run(self) -> int:
        self.ui.title("Local Knowledge Bridge Wizard")
        self.show_status()
        try:
            while True:
                self.ui.menu(
                    "Main menu",
                    [
                        ("1", "Manage sources"),
                        ("2", "Select route weight preset"),
                        ("3", "Configure deep retrieval"),
                        ("4", "Database status and rebuild"),
                        ("5", "Save configuration"),
                        ("6", "Show status"),
                        ("q", "Quit"),
                    ],
                )
                choice = self._prompt("Select").lower()
                try:
                    if choice == "1":
                        self.manage_sources()
                    elif choice == "2":
                        self.manage_weights()
                    elif choice == "3":
                        self.manage_deep()
                    elif choice == "4":
                        self.manage_database()
                    elif choice == "5":
                        self.save_pending()
                    elif choice == "6":
                        self.show_status()
                    elif choice in {"q", "quit", "exit"}:
                        return 0 if self.confirm_exit() else 1
                    else:
                        self.print("Unknown selection.")
                except SystemExit as exc:
                    self.print(f"Error: {_system_exit_message(exc)}")
        except KeyboardInterrupt:
            self.print("")
            self.print("Interrupted.")
            return 0 if self.confirm_exit() else 1

    def _prompt(self, label: str, default: str | None = None) -> str:
        return self.ui.prompt(label, default)

    def confirm(self, label: str, *, default: bool = False) -> bool:
        return self.ui.confirm(label, default=default)

    def mark_dirty(self) -> None:
        self.dirty = True

    def show_status(self) -> None:
        self.ui.section("Status")
        try:
            report = self.ui.run_task("Checking gateway status", lambda: diagnose_gateway(self.config, force_refresh=False))
            for name in ("obsidian", "endnote", "zotero", "folder"):
                self.ui.item(_source_line(name, report.get("source_status", {}).get(name, {})))
            index_info = report.get("index_status", {})
            counts = index_info.get("counts", {})
            self.ui.status("index_db", index_info.get("db_path"))
            count_text = ", ".join(f"{key}={value}" for key, value in counts.items() if int(value or 0) > 0)
            self.ui.status("index_counts", count_text or "empty")
            stale_keys = ["obsidian_stale", "endnote_stale", "zotero_stale", "folder_stale"]
            stale = [key.replace("_stale", "") for key in stale_keys if index_info.get(key)]
            self.ui.status("stale_sources", ", ".join(stale) if stale else "none")
            deep = report.get("deep_status", {})
            self.ui.status(
                "deep",
                f"ready={bool(deep.get('ready'))} device={deep.get('resolved_device')} "
                f"models_cached={bool(deep.get('models_cached'))}",
            )
        except Exception as exc:
            self.print(f"Status unavailable: {exc}")

    def manage_sources(self) -> None:
        while True:
            self.ui.menu(
                "Sources",
                [
                    ("1", f"Obsidian: {self.config.get('obsidian_vault') or '(not set)'}"),
                    ("2", f"EndNote libraries: {len(self.config.get('endnote_libraries', []))}"),
                    ("3", f"Zotero: {self.config.get('zotero_sqlite') or '(not set)'}"),
                    ("4", f"Folder libraries: {len(self.config.get('folder_libraries', []))}"),
                    ("b", "Back"),
                ],
            )
            choice = self._prompt("Select").lower()
            if choice == "1":
                self.manage_obsidian()
            elif choice == "2":
                self.manage_library_list("endnote_libraries")
            elif choice == "3":
                self.manage_zotero()
            elif choice == "4":
                self.manage_library_list("folder_libraries")
            elif choice in {"b", "back"}:
                return
            else:
                self.print("Unknown selection.")

    def manage_obsidian(self) -> None:
        self.ui.menu(
            f"Current Obsidian vault: {self.config.get('obsidian_vault') or '(not set)'}",
            [("1", "Set path"), ("2", "Clear path"), ("b", "Back")],
        )
        choice = self._prompt("Select").lower()
        if choice == "1":
            path = self._prompt("Obsidian vault path")
            if not path:
                return
            self.config["obsidian_vault"] = str(validate_obsidian_vault(path))
            self.mark_dirty()
        elif choice == "2":
            self.config["obsidian_vault"] = ""
            self.mark_dirty()

    def manage_zotero(self) -> None:
        self.ui.menu(
            f"Current Zotero sqlite: {self.config.get('zotero_sqlite') or '(not set)'}",
            [("1", "Set zotero.sqlite"), ("2", "Clear path"), ("b", "Back")],
        )
        choice = self._prompt("Select").lower()
        if choice == "1":
            path = self._prompt("Zotero zotero.sqlite path")
            if not path:
                return
            self.config["zotero_sqlite"] = str(validate_zotero_sqlite(path))
            self.mark_dirty()
        elif choice == "2":
            self.config["zotero_sqlite"] = ""
            self.mark_dirty()

    def manage_library_list(self, key: str) -> None:
        label = "EndNote" if key == "endnote_libraries" else "Folder"
        while True:
            self.ui.section(f"{label} libraries")
            self._print_libraries(key)
            self.ui.menu(
                f"{label} actions",
                [
                    ("1", "Add or update"),
                    ("2", "Rename"),
                    ("3", "Enable/disable"),
                    ("4", "Remove from configuration"),
                    ("b", "Back"),
                ],
            )
            choice = self._prompt("Select").lower()
            if choice == "1":
                self._add_or_update_library(key)
            elif choice == "2":
                item = self._select_library(key)
                if item:
                    name = self._prompt("New display name", str(item.get("name", ""))).strip()
                    if rename_library(self.config, key, str(item.get("id", "")), name):
                        self.mark_dirty()
            elif choice == "3":
                item = self._select_library(key)
                if item:
                    item["enabled"] = not bool(item.get("enabled", True))
                    if key == "endnote_libraries":
                        _sync_endnote_primary(self.config)
                    self.mark_dirty()
            elif choice == "4":
                item = self._select_library(key)
                if item and self.confirm("Remove this entry from lkb_config.json only?"):
                    if remove_library(self.config, key, str(item.get("id", ""))):
                        self.mark_dirty()
            elif choice in {"b", "back"}:
                return
            else:
                self.print("Unknown selection.")

    def _add_or_update_library(self, key: str) -> None:
        if key == "endnote_libraries":
            path = self._prompt("EndNote .enl path")
            if not path:
                return
            name = self._prompt("Display name", Path(path).stem).strip()
            add_or_update_endnote_library(self.config, path, name)
            self.mark_dirty()
            return
        path = self._prompt("Folder source path")
        if not path:
            return
        name = self._prompt("Display name", Path(path).name or "Folder").strip()
        add_or_update_folder_library(self.config, path, name)
        self.mark_dirty()

    def _print_libraries(self, key: str) -> None:
        libraries = self.config.get(key, [])
        if not libraries:
            self.ui.item("none")
            return
        for index, item in enumerate(libraries, start=1):
            status = "enabled" if item.get("enabled", True) else "disabled"
            self.print(f"  {index}. {item.get('name')} [{item.get('id')}] {status} - {item.get('path')}")

    def _select_library(self, key: str) -> dict[str, Any] | None:
        libraries = self.config.get(key, [])
        if not libraries:
            self.print("No entries configured.")
            return None
        self._print_libraries(key)
        value = self._prompt("Entry number/id/name/path")
        for index, item in enumerate(libraries, start=1):
            if value == str(index) or _matches_library(item, value):
                return item
        self.print("No matching entry.")
        return None

    def manage_weights(self) -> None:
        self.ui.section("Route weight presets")
        names = list(WEIGHT_PRESETS)
        for index, name in enumerate(names, start=1):
            self.print(f"  {index}. {name} - {WEIGHT_PRESETS[name]}")
        self.print("  b. Back")
        choice = self._prompt("Select").lower()
        if choice in {"b", "back"}:
            return
        if choice.isdigit() and 1 <= int(choice) <= len(names):
            preset = names[int(choice) - 1]
        else:
            preset = choice
        if preset not in WEIGHT_PRESETS:
            self.print("Unknown preset.")
            return
        apply_weight_preset(self.config, preset)
        self.mark_dirty()
        self.print(f"Selected preset: {preset}")

    def manage_deep(self) -> None:
        while True:
            self.ui.section("Deep retrieval")
            self.show_deep_status()
            self.ui.menu(
                "Deep actions",
                [
                    ("1", "Set deep device"),
                    ("2", "Set default profile"),
                    ("3", "Install deep dependencies and prefetch models"),
                    ("b", "Back"),
                ],
            )
            choice = self._prompt("Select").lower()
            if choice == "1":
                self._set_deep_device_menu()
            elif choice == "2":
                self._set_default_profile_menu()
            elif choice == "3":
                self.run_deep_setup()
            elif choice in {"b", "back"}:
                return
            else:
                self.print("Unknown selection.")

    def show_deep_status(self) -> None:
        try:
            status = inspect_deep_status(self.config)
            self.print(
                f"Deep ready={bool(status.get('ready'))} deps={bool(status.get('deps_installed'))} "
                f"cached={bool(status.get('models_cached'))} device={status.get('resolved_device')}"
            )
            self.print(f"Embedding: {status.get('embedding_model')}")
            self.print(f"Reranker : {status.get('reranker_model')}")
            if status.get("detail"):
                self.print(f"Detail   : {status.get('detail')}")
        except Exception as exc:
            self.print(f"Deep status unavailable: {exc}")

    def _set_deep_device_menu(self) -> None:
        devices = ["cuda_if_available", "cpu", "cuda"]
        for index, device in enumerate(devices, start=1):
            self.print(f"  {index}. {device}")
        choice = self._prompt("Select").lower()
        if choice.isdigit() and 1 <= int(choice) <= len(devices):
            choice = devices[int(choice) - 1]
        set_deep_device(self.config, choice)
        self.mark_dirty()
        if choice == "cuda":
            self.print("CUDA wheel management is not automatic. Use lkb_doctor and the README GPU check if CUDA is unavailable.")

    def _set_default_profile_menu(self) -> None:
        profiles = ["fast", "balanced", "deep"]
        for index, profile in enumerate(profiles, start=1):
            self.print(f"  {index}. {profile}")
        choice = self._prompt("Select").lower()
        if choice.isdigit() and 1 <= int(choice) <= len(profiles):
            choice = profiles[int(choice) - 1]
        set_default_profile(self.config, choice)
        self.mark_dirty()

    def manage_database(self) -> None:
        while True:
            self.ui.section("Database")
            self.show_index_status()
            self.ui.menu(
                "Database actions",
                [
                    ("1", "Show raw status JSON"),
                    ("2", "Refresh index"),
                    ("3", "Full rebuild"),
                    ("b", "Back"),
                ],
            )
            choice = self._prompt("Select").lower()
            if choice == "1":
                self.print(json.dumps(index_status(self.config), ensure_ascii=True, indent=2))
            elif choice == "2":
                self.run_index(force=False)
            elif choice == "3":
                self.run_index(force=True)
            elif choice in {"b", "back"}:
                return
            else:
                self.print("Unknown selection.")

    def show_index_status(self) -> None:
        try:
            status = self.ui.run_task("Checking index status", lambda: index_status(self.config))
            self.ui.status("Index DB", status.get("db_path"))
            self.ui.status("Exists", bool(status.get("exists")))
            counts = status.get("counts", {})
            nonzero = ", ".join(f"{key}={value}" for key, value in counts.items() if int(value or 0) > 0)
            self.ui.status("Counts", nonzero or "empty")
        except Exception as exc:
            self.print(f"Index status unavailable: {exc}")

    def save_pending(self) -> bool:
        if not self.dirty:
            self.print("No configuration changes to save.")
            return True
        self.print("")
        self.print("Pending configuration summary")
        for line in self.config_summary():
            self.print(f"- {line}")
        if not self.confirm("Save these changes to lkb_config.json?"):
            return False
        save_config(self.config)
        self.original_config = copy.deepcopy(self.config)
        self.dirty = False
        self.print("Configuration saved.")
        return True

    def _save_before_action(self, action: str) -> bool:
        if not self.dirty:
            return True
        self.print(f"{action} requires saving pending configuration first.")
        return self.save_pending()

    def run_deep_setup(self) -> bool:
        if not self._save_before_action("Deep setup"):
            return False
        if not self.confirm("Install deep dependencies and prefetch models now?"):
            return False
        command = [
            sys.executable,
            str(gateway_root() / "lkb_bootstrap_runtime.py"),
            "--include-deep",
            "--prefetch-models",
        ]
        result = run_logged_command(command, label="Deep dependency install and model prefetch", cwd=gateway_root(), ui=self.ui)
        return result.ok

    def run_index(self, *, force: bool) -> bool:
        action = "Full index rebuild" if force else "Index refresh"
        if not self._save_before_action(action):
            return False
        if not self.confirm(f"{action} can take a while. Continue?"):
            return False
        python = runtime_python()
        if not python.exists():
            self.print("Embedded runtime is not available. Run lkb_bootstrap_runtime first.")
            return False
        command = [str(python), str(gateway_root() / "lkb_index.py")]
        if force:
            command.append("--force")
        result = run_logged_command(command, label=action, cwd=gateway_root(), ui=self.ui)
        return result.ok

    def confirm_exit(self) -> bool:
        if not self.dirty:
            return True
        if self.confirm("Save changes before exit?"):
            return self.save_pending()
        return self.confirm("Discard unsaved changes and exit?")

    def config_summary(self) -> list[str]:
        retrieval = self.config.get("retrieval", {})
        models = self.config.get("models", {})
        return [
            f"obsidian_vault={self.config.get('obsidian_vault') or '(not set)'}",
            f"endnote_libraries={len(self.config.get('endnote_libraries', []))}",
            f"zotero_sqlite={self.config.get('zotero_sqlite') or '(not set)'}",
            f"folder_libraries={len(self.config.get('folder_libraries', []))}",
            f"profile_default={retrieval.get('profile_default')}",
            f"deep_device={models.get('deep_device')}",
            f"route_weights={len(retrieval.get('route_weights', {}))} routes",
        ]


def main() -> int:
    configure_output()
    return Wizard().run()
