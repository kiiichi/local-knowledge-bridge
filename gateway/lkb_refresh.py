from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from local_knowledge_bridge.stub_cli import run_stub


if __name__ == "__main__":
run_stub("lkb_refresh")
