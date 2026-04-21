from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = GATEWAY_ROOT / ".tmp" / "tests"


@contextmanager
def scratch_dir(case_name: str):
    root = TMP_ROOT / case_name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)
