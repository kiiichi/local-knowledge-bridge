from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.cli_io import configure_output, print_json, print_text
from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.reporting import build_answer_payload
from local_knowledge_bridge.retrieval import search_local
from local_knowledge_bridge.service_client import request_json
from local_knowledge_bridge.service_models import AskRequest


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


def build_request(args: argparse.Namespace) -> AskRequest:
    return AskRequest(
        query=args.question,
        question=args.question,
        target=args.target,
        profile=args.profile,
        mode=args.mode,
        folder=args.folder,
        endnote_library=args.endnote_library,
        years=args.years,
        limit=args.limit,
        auto_refresh=args.auto_refresh,
        refresh_now=args.refresh_now,
    )


def main() -> int:
    configure_output()
    args = parse_args()
    config = load_config()
    request = build_request(args)
    request_payload = request.to_payload()
    if args.no_service:
        payload = build_answer_payload(request.question or request.query, search_local(config, request))
    else:
        payload = request_json(config, "/ask", payload=request_payload)
    if args.json:
        print_json(payload)
    else:
        print_text(payload["answer_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
