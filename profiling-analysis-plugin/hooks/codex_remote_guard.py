#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
if str(HOOK_DIR) not in sys.path:
    sys.path.insert(0, str(HOOK_DIR))

from guard_common import codex_response, inspect_payload, read_hook_payload  # noqa: E402


def main() -> int:
    decision = inspect_payload(read_hook_payload())
    sys.stdout.write(json.dumps(codex_response(decision), ensure_ascii=False) + "\n")
    return 2 if decision.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
