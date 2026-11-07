"""Resolve the shared dataset directory for local and container deployments."""
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("TOURISM_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
