from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from .config import load_config, save_config
from .paths import requirements_deep, requirements_runtime, runtime_python, runtime_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap Local Knowledge Bridge runtime.")
    parser.add_argument("--include-deep", action="store_true", help="Install deep-mode dependencies.")
    parser.add_argument("--force-recreate", action="store_true", help="Recreate the runtime virtual environment.")
    return parser.parse_args()


def _run(args: list[str]) -> None:
    subprocess.run(args, check=True)


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
    _run([python, "-m", "pip", "install", "--upgrade", "pip", "wheel"])
    _run([python, "-m", "pip", "install", "-r", str(requirements_runtime())])
    if include_deep and requirements_deep().exists():
        _run([python, "-m", "pip", "install", "-r", str(requirements_deep())])


def _update_config() -> None:
    config = load_config()
    config.setdefault("runtime", {})
    config["runtime"]["python_home"] = str(runtime_root())
    save_config(config)


def main() -> int:
    args = parse_args()
    _create_runtime(args.force_recreate)
    _install_requirements(args.include_deep)
    _update_config()
    print("Local Knowledge Bridge runtime is ready.")
    print(f"  runtime: {runtime_root()}")
    print(f"  python : {runtime_python()}")
    return 0
