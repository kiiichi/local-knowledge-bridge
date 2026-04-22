from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.cli_io import configure_output, print_json
from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.retrieval import build_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh the Local Knowledge Bridge index.")
    parser.add_argument("--folder", help="Optional Obsidian folder prefix to index.")
    return parser.parse_args()


def main() -> int:
    configure_output()
    args = parse_args()
    summary = build_index(load_config(), force=True, folder_prefix=args.folder)
    print_json(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
