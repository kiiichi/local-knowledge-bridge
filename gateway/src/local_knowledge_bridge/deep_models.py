from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any

from .paths import models_root

_EMBED_MODELS: dict[tuple[str, str], Any] = {}
_RERANK_MODELS: dict[tuple[str, str], Any] = {}


def _models_config(config: dict) -> dict:
    return config.get("models", {})


def _model_id(config: dict, key: str, default: str) -> str:
    value = str(_models_config(config).get(key, default) or default).strip()
    if not value:
        raise SystemExit(f"Missing deep model configuration: models.{key}")
    return value


def embedding_model_id(config: dict) -> str:
    return _model_id(config, "embedding", "BAAI/bge-m3")


def reranker_model_id(config: dict) -> str:
    return _model_id(config, "reranker", "BAAI/bge-reranker-v2-m3")


def prepare_model_environment() -> Path:
    root = models_root()
    cache_root = root / "hf"
    sentence_root = root / "sentence_transformers"
    root.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)
    sentence_root.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_root)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(cache_root / "hub")
    os.environ["TRANSFORMERS_CACHE"] = str(cache_root / "transformers")
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(sentence_root)
    return root


def model_storage_path(model_id: str) -> Path:
    return prepare_model_environment() / model_id.replace("/", "__")


def _import_optional(name: str) -> Any | None:
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        return None


def _require_deep_dependencies() -> tuple[Any, Any]:
    sentence_transformers = _import_optional("sentence_transformers")
    torch = _import_optional("torch")
    if sentence_transformers is None or torch is None:
        raise SystemExit(
            "Deep dependencies are not installed. "
            "Run lkb_bootstrap_runtime --include-deep --prefetch-models."
        )
    return sentence_transformers, torch


def resolve_deep_device(config: dict) -> str:
    configured = str(
        _models_config(config).get(
            "deep_device",
            _models_config(config).get("default_device", "cpu"),
        )
        or "cpu"
    ).strip()
    if configured != "cuda_if_available":
        return configured
    torch = _import_optional("torch")
    if torch is not None and bool(getattr(getattr(torch, "cuda", None), "is_available", lambda: False)()):
        return "cuda"
    return "cpu"


def deep_dependencies_installed() -> bool:
    return _import_optional("sentence_transformers") is not None and _import_optional("torch") is not None


def models_cached(config: dict) -> bool:
    return model_storage_path(embedding_model_id(config)).exists() and model_storage_path(reranker_model_id(config)).exists()


def inspect_deep_status(config: dict) -> dict[str, Any]:
    deps_installed = deep_dependencies_installed()
    cached = models_cached(config)
    detail = ""
    if not deps_installed:
        detail = "Run lkb_bootstrap_runtime --include-deep --prefetch-models to install deep dependencies."
    elif not cached:
        detail = "Deep models are not cached under gateway/.models. Run lkb_bootstrap_runtime --prefetch-models."
    return {
        "deps_installed": deps_installed,
        "embedding_model": embedding_model_id(config),
        "reranker_model": reranker_model_id(config),
        "models_cached": cached,
        "resolved_device": resolve_deep_device(config),
        "ready": deps_installed and cached,
        "models_root": str(models_root()),
        "detail": detail,
    }


def _load_sentence_transformer(model_path: Path, *, device: str) -> Any:
    sentence_transformers, _ = _require_deep_dependencies()
    model_class = getattr(sentence_transformers, "SentenceTransformer")
    return model_class(str(model_path), device=device)


def _load_cross_encoder(model_path: Path, *, device: str) -> Any:
    sentence_transformers, _ = _require_deep_dependencies()
    model_class = getattr(sentence_transformers, "CrossEncoder")
    try:
        return model_class(str(model_path), device=device)
    except TypeError:
        return model_class(str(model_path))


def load_embedding_model(config: dict) -> Any:
    model_id = embedding_model_id(config)
    model_path = model_storage_path(model_id)
    if not model_path.exists():
        raise SystemExit(
            f"Deep embedding model is missing: {model_path}. "
            "Run lkb_bootstrap_runtime --prefetch-models."
        )
    device = resolve_deep_device(config)
    key = (str(model_path), device)
    if key not in _EMBED_MODELS:
        _EMBED_MODELS[key] = _load_sentence_transformer(model_path, device=device)
    return _EMBED_MODELS[key]


def load_reranker_model(config: dict) -> Any:
    model_id = reranker_model_id(config)
    model_path = model_storage_path(model_id)
    if not model_path.exists():
        raise SystemExit(
            f"Deep reranker model is missing: {model_path}. "
            "Run lkb_bootstrap_runtime --prefetch-models."
        )
    device = resolve_deep_device(config)
    key = (str(model_path), device)
    if key not in _RERANK_MODELS:
        _RERANK_MODELS[key] = _load_cross_encoder(model_path, device=device)
    return _RERANK_MODELS[key]


def prefetch_models(config: dict) -> dict[str, Any]:
    prepare_model_environment()
    _require_deep_dependencies()
    huggingface_hub = _import_optional("huggingface_hub")
    if huggingface_hub is None or not hasattr(huggingface_hub, "snapshot_download"):
        raise SystemExit(
            "huggingface_hub is unavailable in the embedded runtime. "
            "Run lkb_bootstrap_runtime --include-deep first."
        )

    for model_id in [embedding_model_id(config), reranker_model_id(config)]:
        target_path = model_storage_path(model_id)
        print(f"Prefetching deep model: {model_id}", flush=True)
        print(f"  target: {target_path}", flush=True)
        try:
            huggingface_hub.snapshot_download(
                repo_id=model_id,
                local_dir=str(target_path),
            )
        except Exception as exc:  # pragma: no cover - exercised in live bootstrap flows
            raise SystemExit(
                f"Failed to prefetch {model_id} into {target_path}. "
                f"Check network access to Hugging Face and retry. Details: {exc}"
            ) from exc
        print(f"Finished deep model: {model_id}", flush=True)

    try:
        print("Verifying deep models can be loaded...", flush=True)
        load_embedding_model(config)
        load_reranker_model(config)
    except Exception as exc:  # pragma: no cover - exercised in live bootstrap flows
        raise SystemExit(f"Deep models were downloaded but could not be loaded. Details: {exc}") from exc
    return inspect_deep_status(config)


def clear_model_caches() -> None:
    _EMBED_MODELS.clear()
    _RERANK_MODELS.clear()
