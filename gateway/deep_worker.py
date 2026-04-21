from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.reporting import build_answer_payload, build_report_payload
from local_knowledge_bridge.retrieval import search_local
from local_knowledge_bridge.service_models import AskRequest, ReportRequest, SearchRequest


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read().lstrip("\ufeff").strip()
    if not raw:
        raise ValueError("Missing worker payload.")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Worker payload must be a JSON object.")
    return payload


def main() -> int:
    payload = read_payload()
    config = load_config()
    operation = str(payload.get("operation", "")).strip().lower()

    if operation == "search":
        request = SearchRequest.from_mapping(payload)
        print(json.dumps(search_local(config, request), ensure_ascii=False))
        return 0
    if operation == "ask":
        request = AskRequest.from_mapping(payload)
        result = build_answer_payload(request.question or request.query, search_local(config, request))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if operation == "report":
        request = ReportRequest.from_mapping(payload)
        result = build_report_payload(request.query, search_local(config, request), request.read_top)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    raise ValueError(f"Unsupported worker operation: {operation}")


if __name__ == "__main__":
    raise SystemExit(main())
