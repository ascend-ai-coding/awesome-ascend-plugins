from __future__ import annotations

import sys
from pathlib import Path


def add_substrate_to_path() -> Path:
    substrate = Path(__file__).resolve().parents[1]
    if str(substrate) not in sys.path:
        sys.path.insert(0, str(substrate))
    return substrate
