from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from local_knowledge_bridge import bootstrap_runtime, service_client


class ServiceClientRuntimeTests(unittest.TestCase):
    def test_preferred_python_uses_embedded_runtime_root_when_usable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_home = Path(temp_dir)
            embedded_python = runtime_home / "python.exe"
            embedded_python.write_text("", encoding="utf-8")

            with patch("local_knowledge_bridge.service_client.subprocess.run") as run:
                run.return_value.returncode = 0
                result = service_client._preferred_python({"runtime": {"python_home": str(runtime_home)}})

            self.assertEqual(result, str(embedded_python))

    def test_preferred_python_raises_on_broken_embedded_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_home = Path(temp_dir)
            embedded_python = runtime_home / "Scripts" / "python.exe"
            embedded_python.parent.mkdir(parents=True, exist_ok=True)
            embedded_python.write_text("", encoding="utf-8")

            with patch("local_knowledge_bridge.service_client.subprocess.run", side_effect=PermissionError):
                with self.assertRaises(SystemExit):
                    service_client._preferred_python({"runtime": {"python_home": str(runtime_home)}})


class BootstrapRuntimeTests(unittest.TestCase):
    def test_copy_portable_runtime_clones_source_and_removes_pyvenv_cfg(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as target_dir:
            source_root = Path(source_dir)
            target_root = Path(target_dir) / "py311"
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


if __name__ == "__main__":
    unittest.main()
