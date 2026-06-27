"""Load the repo-root .env into the environment, once, for any entrypoint.

Import this for its side effect:  ``import core.env  # noqa: F401``
Degrades gracefully if python-dotenv isn't installed yet.
"""
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # python-dotenv not installed yet — env must be exported manually
    pass
