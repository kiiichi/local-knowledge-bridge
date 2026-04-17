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


def cache_root() -> Path:
    return gateway_root() / ".cache"


def index_root() -> Path:
    return gateway_root() / ".index"


def logs_root() -> Path:
    return gateway_root() / ".logs"


def models_root() -> Path:
    return gateway_root() / ".models"


def default_index_db_path() -> Path:
    return index_root() / "lkb_index.sqlite"


def service_log_path() -> Path:
    return logs_root() / "service.log"


def requirements_runtime() -> Path:
    return gateway_root() / "requirements.runtime.txt"


def requirements_deep() -> Path:
    return gateway_root() / "requirements.deep.txt"


def gateway_script_path(script_name: str) -> Path:
    return gateway_root() / script_name


def version_path() -> Path:
    return gateway_root() / "VERSION"


def version_prefix_path() -> Path:
    return gateway_root() / "VERSION_PREFIX"


def eval_root() -> Path:
    return gateway_root() / "eval"


def eval_cases_path() -> Path:
    return eval_root() / "cases.jsonl"
