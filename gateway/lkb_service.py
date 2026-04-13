from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.reporting import build_answer_payload, build_report_payload
from local_knowledge_bridge.retrieval import search_local
from local_knowledge_bridge.service_models import AskRequest, ReportRequest, SearchRequest


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
                    _json_response(self, 200, search_local(config, request))
                    return
                if self.path == "/ask":
                    request = AskRequest.from_mapping(body)
                    payload = build_answer_payload(request.question or request.query, search_local(config, request))
                    _json_response(self, 200, payload)
                    return
                if self.path == "/report":
                    request = ReportRequest.from_mapping(body)
                    payload = build_report_payload(request.query, search_local(config, request), request.read_top)
                    _json_response(self, 200, payload)
                    return
                if self.path == "/shutdown":
                    _json_response(self, 200, {"ok": True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                _json_response(self, 404, {"error": "not_found"})
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
