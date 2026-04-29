from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .cli_io import configure_output
from .config import load_config, save_config
from .paths import gateway_root, requirements_deep, requirements_runtime, runtime_python, runtime_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap Local Knowledge Bridge runtime.")
    parser.add_argument("--include-deep", action="store_true", help="Install deep-mode dependencies.")
    parser.add_argument("--force-recreate", action="store_true", help="Recreate the runtime virtual environment.")
    parser.add_argument(
        "--prefetch-models",
        action="store_true",
        help="Download deep models into gateway/.models using the embedded runtime.",
    )
    return parser.parse_args()


def _run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def _run_streamed(args: list[str], *, cwd: Path | None = None, failure_message: str) -> None:
    completed = subprocess.run(
        args,
        check=False,
        cwd=str(cwd) if cwd is not None else None,
    )
    if completed.returncode != 0:
        raise SystemExit(f"{failure_message} Exit code: {completed.returncode}")


def _is_usable_python(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        completed = subprocess.run(
            [str(path), "-c", "import sys"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except Exception:
        return False
    return completed.returncode == 0


def _python_source_root() -> Path | None:
    candidates = [
        Path(sys.base_prefix),
        Path(sys.exec_prefix),
        Path(sys.executable).resolve().parent,
    ]
    for candidate in candidates:
        if (candidate / "python.exe").exists() and (candidate / "Lib").exists():
            return candidate
    return None


def _copy_portable_runtime(force_recreate: bool) -> bool:
    root = runtime_root()
    if root.exists() and _is_usable_python(runtime_python()) and not force_recreate:
        return True
    source_root = _python_source_root()
    if source_root is None or source_root.resolve() == root.resolve():
        return False
    if force_recreate and root.exists():
        shutil.rmtree(root)
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(
        source_root,
        root,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    pyvenv_cfg = root / "pyvenv.cfg"
    if pyvenv_cfg.exists():
        pyvenv_cfg.unlink()
    return True


def _create_runtime(force_recreate: bool) -> None:
    root = runtime_root()
    root.parent.mkdir(parents=True, exist_ok=True)
    if _copy_portable_runtime(force_recreate):
        if _is_usable_python(runtime_python()):
            return
        raise RuntimeError(f"Copied runtime exists but is not executable: {runtime_python()}")

    if force_recreate and root.exists():
        shutil.rmtree(root)
    if root.exists() and _is_usable_python(runtime_python()):
        return
    import venv
    builder = venv.EnvBuilder(with_pip=True, clear=force_recreate)
    builder.create(str(root))
    if not _is_usable_python(runtime_python()):
        raise RuntimeError(
            "Local Knowledge Bridge runtime was created, but its Python launcher is not executable. "
            "This usually means the runtime is a venv bound to a base interpreter outside the current sandbox."
        )


def _install_requirements(include_deep: bool) -> None:
    python = str(runtime_python())
    print("Installing/updating base runtime dependencies...", flush=True)
    _run([python, "-m", "pip", "install", "--upgrade", "pip", "wheel"])
    _run([python, "-m", "pip", "install", "-r", str(requirements_runtime())])
    if include_deep and requirements_deep().exists():
        print("Installing deep retrieval dependencies...", flush=True)
        _run([python, "-m", "pip", "install", "-r", str(requirements_deep())])


def _update_config() -> None:
    config = load_config()
    config.setdefault("runtime", {})
    config["runtime"]["python_home"] = str(runtime_root())
    save_config(config)


def _prefetch_models() -> None:
    print("Prefetching deep models. Hugging Face will show file progress and download speed below.", flush=True)
    python = str(runtime_python())
    src_root = gateway_root() / "src"
    command = [
        python,
        "-c",
        (
            "import sys; "
            f"sys.path.insert(0, {json.dumps(str(src_root))}); "
            "from local_knowledge_bridge.config import load_config; "
            "from local_knowledge_bridge.deep_models import prefetch_models; "
            "import json; "
            "status = prefetch_models(load_config()); "
            "print('Deep model prefetch status:'); "
            "print(json.dumps(status, ensure_ascii=True, indent=2))"
        ),
    ]
    _run_streamed(
        command,
        cwd=gateway_root(),
        failure_message="Deep model prefetch failed.",
    )


def main() -> int:
    configure_output()
    args = parse_args()
    include_deep = bool(args.include_deep or args.prefetch_models)
    _create_runtime(args.force_recreate)
    _install_requirements(include_deep)
    _update_config()
    if args.prefetch_models:
        _prefetch_models()
    print("Local Knowledge Bridge runtime is ready.")
    print(f"  runtime: {runtime_root()}")
    print(f"  python : {runtime_python()}")
    return 0
