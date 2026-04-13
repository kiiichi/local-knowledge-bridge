from __future__ import annotations

import argparse
import shutil
import subprocess
import venv

from .config import load_config, save_config
from .paths import requirements_deep, requirements_runtime, runtime_python, runtime_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap Local Knowledge Bridge runtime.")
    parser.add_argument("--include-deep", action="store_true", help="Install deep-mode dependencies.")
    parser.add_argument("--force-recreate", action="store_true", help="Recreate the runtime virtual environment.")
    return parser.parse_args()


def _run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def _create_runtime(force_recreate: bool) -> None:
    root = runtime_root()
    if force_recreate and root.exists():
        shutil.rmtree(root)
    if root.exists() and runtime_python().exists():
        return
    root.parent.mkdir(parents=True, exist_ok=True)
    builder = venv.EnvBuilder(with_pip=True, clear=force_recreate)
    builder.create(str(root))


def _install_requirements(include_deep: bool) -> None:
    python = str(runtime_python())
    _run([python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
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
