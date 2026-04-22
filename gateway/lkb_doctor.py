from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.cli_io import configure_output, print_json, print_text
from local_knowledge_bridge.config import load_config
from local_knowledge_bridge.doctor import doctor_report, render_doctor
from local_knowledge_bridge.service_client import service_health


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check LKB version, source compatibility, and index freshness.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    parser.add_argument("--refresh", action="store_true", help="Force refreshing version and source checks")
    return parser.parse_args()


def main() -> int:
    configure_output()
    args = parse_args()
    config = load_config()
    health = service_health(config, timeout=1.0)
    report = doctor_report(config, service_health=health, force_refresh=args.refresh)
    if args.json:
        print_json(report)
    else:
        print_text(render_doctor(report, service_health=health))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
