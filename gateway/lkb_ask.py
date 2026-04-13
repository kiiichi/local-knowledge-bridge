from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.reporting import build_answer_payload
from local_knowledge_bridge.retrieval import search_local
from local_knowledge_bridge.service_client import request_json
from local_knowledge_bridge.service_models import SearchRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Answer from the Local Knowledge Bridge index.")
    parser.add_argument("question")
    parser.add_argument("--target", default="both", choices=["both", "obsidian", "endnote"])
    parser.add_argument("--profile", default="fast")
    parser.add_argument("--folder")
    parser.add_argument("--endnote-library")
    parser.add_argument("--years")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--mode", default="hybrid")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--auto-refresh", action="store_true")
    parser.add_argument("--refresh-now", action="store_true")
    parser.add_argument("--no-service", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    request = SearchRequest(
        query=args.question,
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
        payload = build_answer_payload(args.question, search_local(config, request))
    else:
        payload = request_json(
            config,
            "/ask",
            payload={
                "question": args.question,
                "query": args.question,
                "target": args.target,
                "profile": args.profile,
                "folder": args.folder,
                "endnote_library": args.endnote_library,
                "years": args.years,
                "limit": args.limit,
                "auto_refresh": args.auto_refresh,
                "refresh_now": args.refresh_now,
            },
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["answer_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
