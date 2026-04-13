from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .paths import gateway_script_path, runtime_python


def _base_url(config: dict) -> str:
    service = config.get("service", {})
    host = service.get("host", "127.0.0.1")
    port = int(service.get("port", 53744))
    return f"http://{host}:{port}"


def _preferred_python(config: dict) -> str:
    python_home = str(config.get("runtime", {}).get("python_home", "") or "")
    if python_home:
        for suffix in ["python.exe", "Scripts/python.exe"]:
            candidate = Path(python_home) / suffix
            if candidate.exists():
                return str(candidate)
    runtime_candidate = runtime_python()
    if runtime_candidate.exists():
        return str(runtime_candidate)
    return sys.executable


def service_health(config: dict, timeout: float = 1.5) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(f"{_base_url(config)}/health", timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def start_service(config: dict) -> None:
    if service_health(config):
        return
    command = [
        _preferred_python(config),
        str(gateway_script_path("lkb_service.py")),
        "--host",
        str(config.get("service", {}).get("host", "127.0.0.1")),
        "--port",
        str(config.get("service", {}).get("port", 53744)),
    ]
    creationflags = 0
    if hasattr(subprocess, "DETACHED_PROCESS"):
        creationflags |= int(subprocess.DETACHED_PROCESS)
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        creationflags |= int(subprocess.CREATE_NEW_PROCESS_GROUP)
    subprocess.Popen(
        command,
        cwd=str(gateway_script_path("lkb_service.py").parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def ensure_service(config: dict) -> dict[str, Any]:
    health = service_health(config)
    if health:
        return health

    start_service(config)
    timeout_seconds = int(config.get("service", {}).get("startup_timeout_seconds", 240))
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        health = service_health(config)
        if health:
            return health
        time.sleep(0.25)
    raise SystemExit("Local Knowledge Bridge service did not become healthy in time.")


def request_json(
    config: dict,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    auto_start: bool = True,
) -> dict[str, Any]:
    if auto_start:
        ensure_service(config)
    url = f"{_base_url(config)}{path}"
    timeout = int(config.get("service", {}).get("request_timeout_seconds", 600))
    request = urllib.request.Request(url, method="POST" if payload is not None else "GET")
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            with urllib.request.urlopen(request, data=body, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="ignore")
            raise SystemExit(f"Service request failed: {exc.code} {error_body}") from exc
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
