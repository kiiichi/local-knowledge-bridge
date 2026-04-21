from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from local_knowledge_bridge import doctor
from local_knowledge_bridge.service_models import AskRequest, SearchRequest


def load_script_module(script_name: str):
    module_name = f"test_{script_name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, GATEWAY_ROOT / f"{script_name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DeepServiceTests(unittest.TestCase):
    def test_search_payload_routes_deep_profile_into_worker(self) -> None:
        module = load_script_module("lkb_service")
        request = SearchRequest(query="passive linear optics", profile="deep")
        with (
            patch.object(module, "selected_profile", return_value="deep"),
            patch.object(module, "_run_deep_worker", return_value={"hits": []}) as run_deep_worker,
        ):
            payload = module._search_payload({}, request)

        self.assertEqual(payload, {"hits": []})
        run_deep_worker.assert_called_once_with({}, {"operation": "search", **request.to_payload()})

    def test_ask_payload_keeps_non_deep_requests_in_process(self) -> None:
        module = load_script_module("lkb_service")
        request = AskRequest(query="What is passive linear optics?", question="What is passive linear optics?", profile="fast")
        with (
            patch.object(module, "selected_profile", return_value="fast"),
            patch.object(module, "search_local", return_value={"hits": []}) as search_local,
            patch.object(module, "build_answer_payload", return_value={"answer_markdown": "answer"}) as build_answer_payload,
        ):
            payload = module._ask_payload({}, request)

        self.assertEqual(payload["answer_markdown"], "answer")
        search_local.assert_called_once()
        build_answer_payload.assert_called_once()

    def test_run_deep_worker_raises_busy_error_when_lock_is_held(self) -> None:
        module = load_script_module("lkb_service")
        acquired = module.DEEP_REQUEST_LOCK.acquire(blocking=False)
        self.assertTrue(acquired)
        try:
            with self.assertRaises(module.DeepWorkerBusyError):
                module._run_deep_worker({}, {"operation": "search"})
        finally:
            module.DEEP_REQUEST_LOCK.release()

    def test_run_deep_worker_maps_timeout(self) -> None:
        module = load_script_module("lkb_service")
        with (
            patch.object(module, "_preferred_python", return_value="python.exe"),
            patch.object(module, "subprocess") as subprocess_module,
        ):
            subprocess_module.PIPE = subprocess.PIPE
            subprocess_module.TimeoutExpired = subprocess.TimeoutExpired
            subprocess_module.run.side_effect = subprocess.TimeoutExpired(cmd=["python.exe"], timeout=3)
            with self.assertRaises(module.DeepWorkerTimeoutError):
                module._run_deep_worker({"service": {"request_timeout_seconds": 3}}, {"operation": "search"})


class DoctorDeepStatusTests(unittest.TestCase):
    def test_diagnose_gateway_includes_deep_status(self) -> None:
        with (
            patch.object(doctor, "load_app_version", return_value="0.1.0"),
            patch.object(doctor, "get_version_status", return_value={"update_available": False}),
            patch.object(doctor, "get_source_compatibility_status", return_value={"obsidian": {}, "endnote": {}}),
            patch.object(
                doctor,
                "_endnote_source_status",
                return_value=(
                    {"configured": False, "available": False, "compatible": False, "suggest_update": False, "authorized": True},
                    {"authorized": True, "status": "not_applicable", "detail": ""},
                ),
            ),
            patch.object(doctor, "_normalized_index_status", return_value={"counts": {}}),
            patch.object(doctor, "inspect_deep_status", return_value={"ready": True, "deps_installed": True}),
            patch.object(doctor, "enabled_endnote_libraries", return_value=[]),
        ):
            report = doctor.diagnose_gateway({"obsidian_vault": ""})

        self.assertTrue(report["deep_status"]["ready"])


if __name__ == "__main__":
    unittest.main()
