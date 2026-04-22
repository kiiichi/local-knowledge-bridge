from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from local_knowledge_bridge.cli_io import print_json


class CliIoTests(unittest.TestCase):
    def test_print_json_escapes_non_ascii_for_windows_console_safety(self) -> None:
        stream = io.StringIO()

        with redirect_stdout(stream):
            print_json({"text": "bad \ufffd 中文"})

        output = stream.getvalue()
        self.assertIn("\\ufffd", output)
        self.assertIn("\\u4e2d\\u6587", output)


if __name__ == "__main__":
    unittest.main()
