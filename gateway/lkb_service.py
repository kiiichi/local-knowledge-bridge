from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.config import load_config, selected_profile
from local_knowledge_bridge.reporting import build_answer_payload, build_report_payload
from local_knowledge_bridge.retrieval import search_local
from local_knowledge_bridge.service_client import _preferred_python, hidden_subprocess_kwargs
from local_knowledge_bridge.service_models import AskRequest, ReportRequest, SearchRequest

DEEP_REQUEST_LOCK = threading.Lock()


class DeepWorkerBusyError(RuntimeError):
    pass


class DeepWorkerTimeoutError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Local Knowledge Bridge HTTP service.")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    return parser.parse_args()


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _deep_worker_script() -> Path:
    return Path(__file__).resolve().parent / "deep_worker.py"


def _run_deep_worker(config: dict, payload: dict[str, Any]) -> dict[str, Any]:
    if not DEEP_REQUEST_LOCK.acquire(blocking=False):
        raise DeepWorkerBusyError("Deep analysis is busy. Retry after the current deep request finishes.")

    try:
        timeout_seconds = int(config.get("service", {}).get("request_timeout_seconds", 600))
        completed = subprocess.run(
            [str(_preferred_python(config)), str(_deep_worker_script())],
            input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(_deep_worker_script().parent),
            timeout=timeout_seconds,
            check=False,
            **hidden_subprocess_kwargs(),
        )
    except subprocess.TimeoutExpired as exc:
        raise DeepWorkerTimeoutError(
            f"Deep worker timed out after {int(config.get('service', {}).get('request_timeout_seconds', 600))} seconds."
        ) from exc
    finally:
        DEEP_REQUEST_LOCK.release()

    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip() or completed.stdout.decode(
            "utf-8", errors="replace"
        ).strip()
        raise RuntimeError(message or f"deep_worker exited with code {completed.returncode}")

    raw = completed.stdout.decode("utf-8", errors="replace").strip()
    if not raw:
        raise RuntimeError("deep_worker produced no output.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"deep_worker returned invalid JSON: {raw[:200]}") from exc


def _search_payload(config: dict, request: SearchRequest) -> dict[str, Any]:
    if selected_profile(config, request.profile) == "deep":
        return _run_deep_worker(config, {"operation": "search", **request.to_payload()})
    return search_local(config, request)


def _ask_payload(config: dict, request: AskRequest) -> dict[str, Any]:
    if selected_profile(config, request.profile) == "deep":
        return _run_deep_worker(config, {"operation": "ask", **request.to_payload()})
    return build_answer_payload(request.question or request.query, search_local(config, request))


def _report_payload(config: dict, request: ReportRequest) -> dict[str, Any]:
    if selected_profile(config, request.profile) == "deep":
        return _run_deep_worker(config, {"operation": "report", **request.to_payload()})
    return build_report_payload(request.query, search_local(config, request), request.read_top)


def main() -> int:
    config = load_config()
    args = parse_args()
    if args.host:
        config.setdefault("service", {})["host"] = args.host
    if args.port:
        config.setdefault("service", {})["port"] = args.port

    service_host = str(config.get("service", {}).get("host", "127.0.0.1"))
    service_port = int(config.get("service", {}).get("port", 53744))
    started_at = time.time()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                _json_response(
                    self,
                    200,
                    {
                        "running": True,
                        "service": {"host": service_host, "port": service_port},
                        "started_at": started_at,
                    },
                )
                return
            _json_response(self, 404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            raw_length = self.headers.get("Content-Length") or "0"
            length = int(raw_length)
            raw_body = self.rfile.read(length) if length else b"{}"
            body = json.loads(raw_body.decode("utf-8") or "{}")
            try:
                if self.path == "/search":
                    request = SearchRequest.from_mapping(body)
                    _json_response(self, 200, _search_payload(config, request))
                    return
                if self.path == "/ask":
                    request = AskRequest.from_mapping(body)
                    _json_response(self, 200, _ask_payload(config, request))
                    return
                if self.path == "/report":
                    request = ReportRequest.from_mapping(body)
                    _json_response(self, 200, _report_payload(config, request))
                    return
                if self.path == "/shutdown":
                    _json_response(self, 200, {"ok": True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                _json_response(self, 404, {"error": "not_found"})
            except DeepWorkerBusyError as exc:
                _json_response(self, 429, {"error": str(exc)})
            except DeepWorkerTimeoutError as exc:
                _json_response(self, 504, {"error": str(exc)})
            except SystemExit as exc:
                _json_response(self, 400, {"error": str(exc)})
            except Exception as exc:  # pragma: no cover
                _json_response(self, 500, {"error": str(exc)})

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer((service_host, service_port), Handler)
    print(f"Local Knowledge Bridge service listening on {service_host}:{service_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
