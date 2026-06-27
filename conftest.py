"""Ensure the repo root is importable in tests (so `import core`, `connectors`, ... work)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
