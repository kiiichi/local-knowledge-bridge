from __future__ import annotations

import json
import sys
from typing import Any


def configure_output() -> None:
    """Avoid Windows console crashes on characters outside the active code page."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(errors="replace")
        except (TypeError, ValueError):
            pass


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=True, indent=2))


def print_text(value: str) -> None:
    print(value)
