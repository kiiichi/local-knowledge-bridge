from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.cli_io import configure_output, print_json, print_text
from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.evals import evaluate_cases, render_eval


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate LKB retrieval quality on local regression cases.")
    parser.add_argument("--profile", choices=["fast", "balanced", "deep"], default="balanced")
    parser.add_argument("--baseline", action="store_true", help="Use the lexical baseline profile for comparison")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    return parser.parse_args()


def main() -> int:
    configure_output()
    args = parse_args()
    metrics = evaluate_cases(load_config(), profile=args.profile, baseline=args.baseline)
    if args.json:
        print_json(metrics)
    else:
        print_text(render_eval(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
