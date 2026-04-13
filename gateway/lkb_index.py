from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.retrieval import build_index, index_status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or inspect the Local Knowledge Bridge index.")
    parser.add_argument("--folder", help="Optional Obsidian folder prefix to index.")
    parser.add_argument("--force", action="store_true", help="Force a full rebuild.")
    parser.add_argument("--status", action="store_true", help="Show index status.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    if args.status:
        print(json.dumps(index_status(config), ensure_ascii=False, indent=2))
        return 0
    summary = build_index(config, force=args.force, folder_prefix=args.folder)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
