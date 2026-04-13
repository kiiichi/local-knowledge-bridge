from __future__ import annotations

from pathlib import Path


def gateway_root() -> Path:
    return Path(__file__).resolve().parents[2]


def config_path() -> Path:
    return gateway_root() / "lkb_config.json"


def config_template_path() -> Path:
    return gateway_root() / "templates" / "lkb_config.template.json"


def runtime_root() -> Path:
    return gateway_root() / "runtime" / "py311"


def runtime_python() -> Path:
    scripts_python = runtime_root() / "Scripts" / "python.exe"
    if scripts_python.exists():
        return scripts_python
    return runtime_root() / "python.exe"


def requirements_runtime() -> Path:
    return gateway_root() / "requirements.runtime.txt"


def requirements_deep() -> Path:
    return gateway_root() / "requirements.deep.txt"
