from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(__file__).resolve().parent
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from local_knowledge_bridge import terminal_ui, wizard
from local_knowledge_bridge.constants import DEFAULT_ROUTE_WEIGHTS
from support import scratch_dir


def load_script_module(script_name: str):
    module_name = f"test_{script_name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, GATEWAY_ROOT / f"{script_name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WizardPresetTests(unittest.TestCase):
    def test_default_weight_preset_restores_all_default_routes(self) -> None:
        config = {"retrieval": {"route_weights": {"obsidian_notes": 2.0}}}

        wizard.apply_weight_preset(config, "default")

        self.assertEqual(config["retrieval"]["route_weights"], DEFAULT_ROUTE_WEIGHTS)

    def test_weight_presets_return_complete_clamped_route_maps(self) -> None:
        for preset in wizard.WEIGHT_PRESETS:
            with self.subTest(preset=preset):
                weights = wizard.route_weight_preset(preset)
                self.assertEqual(set(weights), set(DEFAULT_ROUTE_WEIGHTS))
                self.assertTrue(all(0.5 <= value <= 2.0 for value in weights.values()))

        notes = wizard.route_weight_preset("notes_first")
        self.assertEqual(notes["obsidian_notes"], round(DEFAULT_ROUTE_WEIGHTS["obsidian_notes"] * 1.2, 3))
        self.assertEqual(notes["endnote_fulltext"], round(DEFAULT_ROUTE_WEIGHTS["endnote_fulltext"] * 0.9, 3))

        folder = wizard.route_weight_preset("folder_first")
        self.assertEqual(folder["folder_chunks"], round(DEFAULT_ROUTE_WEIGHTS["folder_chunks"] * 1.35, 3))
        self.assertEqual(folder["zotero_docs"], round(DEFAULT_ROUTE_WEIGHTS["zotero_docs"] * 0.9, 3))


class WizardSourceTests(unittest.TestCase):
    def test_folder_add_validates_path_and_remove_only_changes_config(self) -> None:
        config = {"folder_libraries": []}
        with patch.object(wizard, "validate_folder_library", return_value=Path("C:/sources/papers")) as validate:
            wizard.add_or_update_folder_library(config, "C:/sources/papers", "Papers")

        validate.assert_called_once_with("C:/sources/papers")
        self.assertEqual(config["folder_libraries"][0]["name"], "Papers")
        self.assertEqual(config["folder_libraries"][0]["enabled"], True)

        removed = wizard.remove_library(config, "folder_libraries", "Papers")

        self.assertTrue(removed)
        self.assertEqual(config["folder_libraries"], [])

    def test_endnote_add_validates_components_and_preserves_max_limit(self) -> None:
        config = {"endnote_libraries": [], "endnote_library": ""}
        with patch.object(
            wizard,
            "resolve_endnote_components",
            return_value={"library": Path("C:/EndNote/Main.enl")},
        ) as resolve:
            wizard.add_or_update_endnote_library(config, "C:/EndNote/Main.enl", "Main")

        resolve.assert_called_once_with("C:/EndNote/Main.enl")
        self.assertEqual(config["endnote_library"], "C:\\EndNote\\Main.enl")
        self.assertEqual(config["endnote_libraries"][0]["id"], "main")

    def test_set_source_paths_call_validators(self) -> None:
        inputs = iter(["1", "C:/Notes"])
        app = wizard.Wizard(config={}, input_func=lambda prompt: next(inputs), print_func=lambda *args, **kwargs: None)

        with patch.object(wizard, "validate_obsidian_vault", return_value=Path("C:/Notes")) as validate:
            app.manage_obsidian()

        validate.assert_called_once_with("C:/Notes")
        self.assertEqual(app.config["obsidian_vault"], "C:\\Notes")
        self.assertTrue(app.dirty)

        inputs = iter(["1", "C:/Zotero/zotero.sqlite"])
        app = wizard.Wizard(config={}, input_func=lambda prompt: next(inputs), print_func=lambda *args, **kwargs: None)
        with patch.object(wizard, "validate_zotero_sqlite", return_value=Path("C:/Zotero/zotero.sqlite")) as validate:
            app.manage_zotero()

        validate.assert_called_once_with("C:/Zotero/zotero.sqlite")
        self.assertEqual(app.config["zotero_sqlite"], "C:\\Zotero\\zotero.sqlite")


class WizardDeepAndActionTests(unittest.TestCase):
    def test_deep_device_and_default_profile_are_preset_only_config_changes(self) -> None:
        config = {}

        wizard.set_deep_device(config, "cuda_if_available")
        wizard.set_default_profile(config, "deep")

        self.assertEqual(config["models"]["deep_device"], "cuda_if_available")
        self.assertEqual(config["retrieval"]["profile_default"], "deep")

    def test_deep_setup_requires_confirmation_before_subprocess(self) -> None:
        app = wizard.Wizard(config={}, input_func=lambda prompt: "n", print_func=lambda *args, **kwargs: None)

        with patch.object(wizard, "run_logged_command") as run:
            self.assertFalse(app.run_deep_setup())

        run.assert_not_called()

    def test_index_rebuild_requires_confirmation_before_subprocess(self) -> None:
        app = wizard.Wizard(config={}, input_func=lambda prompt: "n", print_func=lambda *args, **kwargs: None)

        with patch.object(wizard, "run_logged_command") as run:
            self.assertFalse(app.run_index(force=True))

        run.assert_not_called()

    def test_pending_config_is_saved_before_rebuild(self) -> None:
        with scratch_dir("wizard_rebuild") as root:
            runtime = root / "python.exe"
            runtime.write_text("", encoding="utf-8")
            answers = iter(["y", "y"])
            app = wizard.Wizard(
                config={"retrieval": {}, "models": {}},
                input_func=lambda prompt: next(answers),
                print_func=lambda *args, **kwargs: None,
            )
            app.config["obsidian_vault"] = "C:/Notes"
            app.dirty = True

            with (
                patch.object(wizard, "save_config") as save_config,
                patch.object(wizard, "runtime_python", return_value=runtime),
                patch.object(wizard, "gateway_root", return_value=root),
                patch.object(
                    wizard,
                    "run_logged_command",
                    return_value=terminal_ui.CommandResult(args=[], returncode=0, elapsed_seconds=0.0, log_path=root / "wizard.log"),
                ) as run,
            ):
                self.assertTrue(app.run_index(force=True))

        save_config.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(command[0], str(runtime))
        self.assertIn("--force", command)
        self.assertFalse(app.dirty)

    def test_deep_setup_uses_logged_command_runner(self) -> None:
        app = wizard.Wizard(config={}, input_func=lambda prompt: "y", print_func=lambda *args, **kwargs: None)
        with scratch_dir("wizard_deep_setup") as root:
            with (
                patch.object(wizard, "gateway_root", return_value=root),
                patch.object(
                    wizard,
                    "run_logged_command",
                    return_value=terminal_ui.CommandResult(args=[], returncode=0, elapsed_seconds=0.0, log_path=root / "wizard.log"),
                ) as run,
            ):
                self.assertTrue(app.run_deep_setup())

        command = run.call_args.args[0]
        self.assertIn("--include-deep", command)
        self.assertIn("--prefetch-models", command)


class WizardInteractionTests(unittest.TestCase):
    def test_validator_error_returns_to_menu_without_saving(self) -> None:
        answers = iter(["1", "1", "1", "bad-path", "q"])
        printed: list[str] = []
        app = wizard.Wizard(
            config={},
            input_func=lambda prompt: next(answers),
            print_func=lambda *args, **kwargs: printed.append(" ".join(str(arg) for arg in args)),
        )

        with (
            patch.object(wizard, "diagnose_gateway", return_value={"source_status": {}, "index_status": {}, "deep_status": {}}),
            patch.object(wizard, "validate_obsidian_vault", side_effect=SystemExit("missing vault")),
            patch.object(wizard, "save_config") as save_config,
        ):
            self.assertEqual(app.run(), 0)

        save_config.assert_not_called()
        self.assertTrue(any("missing vault" in line for line in printed))


class TerminalUITests(unittest.TestCase):
    def test_run_task_prints_running_and_done_messages(self) -> None:
        printed: list[str] = []
        ui = terminal_ui.TerminalUI(print_func=lambda *args, **kwargs: printed.append(" ".join(str(arg) for arg in args)))

        result = ui.run_task("Short task", lambda: "ok")

        self.assertEqual(result, "ok")
        self.assertTrue(any("[RUNNING] Short task" in line for line in printed))
        self.assertTrue(any("[DONE] Short task" in line for line in printed))

    def test_logged_command_writes_log_and_returns_exit_status(self) -> None:
        printed: list[str] = []
        ui = terminal_ui.TerminalUI(print_func=lambda *args, **kwargs: printed.append(" ".join(str(arg) for arg in args)))
        with scratch_dir("wizard_logged_command") as root:
            log_path = root / "wizard.log"
            with patch.object(terminal_ui.subprocess, "run") as run:
                run.return_value.returncode = 7
                result = terminal_ui.run_logged_command(
                    ["python", "--version"],
                    label="Version check",
                    cwd=root,
                    log_path=log_path,
                    ui=ui,
                )
            log_text = log_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 7)
        self.assertIn("$ python --version", log_text)
        self.assertTrue(any("[FAILED] Version check" in line for line in printed))


class WizardWrapperTests(unittest.TestCase):
    def test_lkb_wizard_script_imports_main(self) -> None:
        module = load_script_module("lkb_wizard")
        self.assertTrue(callable(module.main))

    def test_powershell_wrapper_allows_python_fallback(self) -> None:
        text = (GATEWAY_ROOT / "lkb_wizard.ps1").read_text(encoding="utf-8")
        self.assertIn("-AllowPythonFallback", text)

    def test_repo_setup_script_selects_deploy_or_opens_maintenance_wizard(self) -> None:
        text = (GATEWAY_ROOT.parent / "scripts" / "lkb_setup.ps1").read_text(encoding="utf-8")
        self.assertIn("install_windows.ps1", text)
        self.assertIn("Configure existing deployment", text)
        self.assertIn("Install or redeploy", text)
        self.assertIn("lkb_wizard.cmd", text)
        self.assertIn("-IncludeDeepDeps", text)
        self.assertIn("-PrefetchModels", text)
        self.assertIn("Open LKB maintenance wizard", text)

    def test_repo_setup_cmd_launches_script_with_bypass_and_pause_on_failure(self) -> None:
        text = (GATEWAY_ROOT.parent / "lkb_setup.cmd").read_text(encoding="utf-8")
        self.assertIn('cd /d "%~dp0"', text)
        self.assertIn("-ExecutionPolicy Bypass", text)
        self.assertIn('scripts\\lkb_setup.ps1', text)
        self.assertIn("pause", text.lower())


if __name__ == "__main__":
    unittest.main()
