from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from local_knowledge_bridge import bootstrap_runtime, service_client
from support import scratch_dir


class ServiceClientRuntimeTests(unittest.TestCase):
    def test_preferred_python_uses_embedded_runtime_root_when_usable(self) -> None:
        with scratch_dir("preferred_python_usable") as runtime_home:
            embedded_python = runtime_home / "python.exe"
            embedded_python.write_text("", encoding="utf-8")

            with patch("local_knowledge_bridge.service_client.subprocess.run") as run:
                run.return_value.returncode = 0
                result = service_client._preferred_python({"runtime": {"python_home": str(runtime_home)}})

            self.assertEqual(result, str(embedded_python))

    def test_preferred_python_raises_on_broken_embedded_runtime(self) -> None:
        with scratch_dir("preferred_python_broken") as runtime_home:
            embedded_python = runtime_home / "Scripts" / "python.exe"
            embedded_python.parent.mkdir(parents=True, exist_ok=True)
            embedded_python.write_text("", encoding="utf-8")

            with patch("local_knowledge_bridge.service_client.subprocess.run", side_effect=PermissionError):
                with self.assertRaises(SystemExit):
                    service_client._preferred_python({"runtime": {"python_home": str(runtime_home)}})

    def test_start_service_redirects_stdout_and_stderr_to_service_log(self) -> None:
        with scratch_dir("service_log_redirect") as temp_root:
            service_script = temp_root / "lkb_service.py"
            service_script.write_text("", encoding="utf-8")
            log_path = temp_root / ".logs" / "service.log"

            with (
                patch("local_knowledge_bridge.service_client.service_health", return_value=None),
                patch("local_knowledge_bridge.service_client._preferred_python", return_value="python.exe"),
                patch("local_knowledge_bridge.service_client.gateway_script_path", return_value=service_script),
                patch("local_knowledge_bridge.service_client.service_log_path", return_value=log_path),
                patch("local_knowledge_bridge.service_client.subprocess.Popen") as popen,
            ):
                service_client.start_service({"service": {"host": "127.0.0.1", "port": 53744}})

            self.assertTrue(log_path.exists())
            kwargs = popen.call_args.kwargs
            self.assertEqual(Path(kwargs["stdout"].name), log_path)
            self.assertIs(kwargs["stdout"], kwargs["stderr"])
            self.assertEqual(kwargs["cwd"], str(service_script.parent))


class BootstrapRuntimeTests(unittest.TestCase):
    def test_copy_portable_runtime_clones_source_and_removes_pyvenv_cfg(self) -> None:
        with scratch_dir("runtime_source") as source_root, scratch_dir("runtime_target") as target_base:
            target_root = target_base / "py311"
            (source_root / "python.exe").write_text("", encoding="utf-8")
            (source_root / "Lib").mkdir()
            (source_root / "Scripts").mkdir()
            (source_root / "pyvenv.cfg").write_text("old", encoding="utf-8")

            with (
                patch("local_knowledge_bridge.bootstrap_runtime.runtime_root", return_value=target_root),
                patch("local_knowledge_bridge.bootstrap_runtime.runtime_python", side_effect=lambda: target_root / "python.exe"),
                patch("local_knowledge_bridge.bootstrap_runtime._python_source_root", return_value=source_root),
                patch("local_knowledge_bridge.bootstrap_runtime._is_usable_python", return_value=True),
            ):
                copied = bootstrap_runtime._copy_portable_runtime(force_recreate=True)

            self.assertTrue(copied)
            self.assertTrue((target_root / "python.exe").exists())
            self.assertFalse((target_root / "pyvenv.cfg").exists())
            self.assertTrue((target_root / "Lib").exists())

    def test_install_script_wires_prefetch_models_flag(self) -> None:
        install_script = GATEWAY_ROOT.parent / "scripts" / "install_windows.ps1"
        text = install_script.read_text(encoding="utf-8")
        self.assertIn("[switch]$PrefetchModels", text)
        self.assertIn("--prefetch-models", text)

    def test_prefetch_models_invokes_embedded_runtime_with_src_path(self) -> None:
        with scratch_dir("prefetch_runtime") as runtime_home:
            embedded_python = runtime_home / "python.exe"
            embedded_python.write_text("", encoding="utf-8")
            with (
                patch("local_knowledge_bridge.bootstrap_runtime.runtime_python", return_value=embedded_python),
                patch("local_knowledge_bridge.bootstrap_runtime.gateway_root", return_value=GATEWAY_ROOT),
                patch("local_knowledge_bridge.bootstrap_runtime.subprocess.run") as run,
            ):
                run.return_value.returncode = 0
                run.return_value.stdout = ""
                run.return_value.stderr = ""
                bootstrap_runtime._prefetch_models()

        command = run.call_args.args[0]
        self.assertEqual(command[0], str(embedded_python))
        self.assertIn("sys.path.insert(0", command[2])


if __name__ == "__main__":
    unittest.main()
