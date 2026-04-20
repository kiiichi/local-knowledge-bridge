from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.reporting import search_results_text
from local_knowledge_bridge.retrieval import search_local
from local_knowledge_bridge.service_client import request_json
from local_knowledge_bridge.service_models import SearchRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search the Local Knowledge Bridge index.")
    parser.add_argument("target", choices=["both", "obsidian", "endnote"])
    parser.add_argument("query")
    parser.add_argument("--folder")
    parser.add_argument("--endnote-library")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--mode", default="hybrid")
    parser.add_argument("--years")
    parser.add_argument("--show-config", action="store_true")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--profile", default="balanced")
    parser.add_argument("--auto-refresh", action="store_true")
    parser.add_argument("--refresh-now", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-service", action="store_true")
    return parser.parse_args()


def build_request(args: argparse.Namespace) -> SearchRequest:
    return SearchRequest(
        query=args.query,
        target=args.target,
        profile=args.profile,
        mode=args.mode,
        folder=args.folder,
        endnote_library=args.endnote_library,
        years=args.years,
        limit=args.limit,
        explain=args.explain,
        auto_refresh=args.auto_refresh,
        refresh_now=args.refresh_now,
    )


def main() -> int:
    args = parse_args()
    config = load_config()
    if args.show_config:
        print(json.dumps(config, ensure_ascii=False, indent=2))

    request = build_request(args)
    request_payload = request.to_payload()
    if args.no_service:
        payload = search_local(config, request)
    else:
        payload = request_json(config, "/search", payload=request_payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(search_results_text(payload, explain=args.explain))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
