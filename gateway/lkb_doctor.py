from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.doctor import doctor_report
from local_knowledge_bridge.service_client import service_health


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose Local Knowledge Bridge state.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    health = service_health(config, timeout=1.0)
    report = doctor_report(config, service_health=health)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
