from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from local_knowledge_bridge import deep_models
from support import scratch_dir


class DeepModelTests(unittest.TestCase):
    def tearDown(self) -> None:
        deep_models.clear_model_caches()

    def test_resolve_deep_device_falls_back_to_cpu_when_cuda_is_unavailable(self) -> None:
        fake_torch = types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=lambda: False))
        with patch.object(deep_models, "_import_optional", side_effect=lambda name: fake_torch if name == "torch" else object()):
            resolved = deep_models.resolve_deep_device({"models": {"deep_device": "cuda_if_available"}})
        self.assertEqual(resolved, "cpu")

    def test_prefetch_models_downloads_both_models_into_gateway_models(self) -> None:
        def fake_snapshot_download(*, repo_id: str, local_dir: str) -> None:
            local_path = Path(local_dir)
            local_path.mkdir(parents=True, exist_ok=True)
            (local_path / "config.json").write_text(repo_id, encoding="utf-8")

        fake_hub = types.SimpleNamespace(snapshot_download=fake_snapshot_download)
        fake_sentence_transformers = object()
        fake_torch = types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=lambda: False))

        def fake_import(name: str):
            if name == "huggingface_hub":
                return fake_hub
            if name == "sentence_transformers":
                return fake_sentence_transformers
            if name == "torch":
                return fake_torch
            return None

        with scratch_dir("deep_prefetch") as root:
            with (
                patch.object(deep_models, "models_root", return_value=root),
                patch.object(deep_models, "_import_optional", side_effect=fake_import),
                patch.object(deep_models, "_require_deep_dependencies", return_value=(fake_sentence_transformers, fake_torch)),
                patch.object(deep_models, "load_embedding_model", return_value=object()),
                patch.object(deep_models, "load_reranker_model", return_value=object()),
            ):
                status = deep_models.prefetch_models({})
                self.assertTrue((root / "BAAI__bge-m3" / "config.json").exists())
                self.assertTrue((root / "BAAI__bge-reranker-v2-m3" / "config.json").exists())

        self.assertTrue(status["models_cached"])

    def test_load_embedding_model_requires_prefetched_model(self) -> None:
        fake_sentence_transformers = types.SimpleNamespace(SentenceTransformer=lambda *args, **kwargs: object())
        fake_torch = types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=lambda: False))
        with scratch_dir("deep_missing_model") as root:
            with (
                patch.object(deep_models, "models_root", return_value=root),
                patch.object(deep_models, "_require_deep_dependencies", return_value=(fake_sentence_transformers, fake_torch)),
            ):
                with self.assertRaises(SystemExit):
                    deep_models.load_embedding_model({})


if __name__ == "__main__":
    unittest.main()
