from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.reporting import build_report_payload
from local_knowledge_bridge.retrieval import search_local
from local_knowledge_bridge.service_client import request_json
from local_knowledge_bridge.service_models import SearchRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a structured Local Knowledge Bridge report.")
    parser.add_argument("query")
    parser.add_argument("--target", default="both", choices=["both", "obsidian", "endnote"])
    parser.add_argument("--years")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--folder")
    parser.add_argument("--endnote-library")
    parser.add_argument("--mode", default="hybrid")
    parser.add_argument("--read-top", type=int, default=3)
    parser.add_argument("--profile", default="balanced")
    parser.add_argument("--auto-refresh", action="store_true")
    parser.add_argument("--refresh-now", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-service", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    request = SearchRequest(
        query=args.query,
        target=args.target,
        profile=args.profile,
        folder=args.folder,
        endnote_library=args.endnote_library,
        years=args.years,
        limit=args.limit,
        auto_refresh=args.auto_refresh,
        refresh_now=args.refresh_now,
    )
    if args.no_service:
        payload = build_report_payload(args.query, search_local(config, request), args.read_top)
    else:
        payload = request_json(
            config,
            "/report",
            payload={
                "query": args.query,
                "target": args.target,
                "profile": args.profile,
                "folder": args.folder,
                "endnote_library": args.endnote_library,
                "years": args.years,
                "limit": args.limit,
                "read_top": args.read_top,
                "auto_refresh": args.auto_refresh,
                "refresh_now": args.refresh_now,
            },
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
