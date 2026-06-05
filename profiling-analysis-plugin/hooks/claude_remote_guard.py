#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
if str(HOOK_DIR) not in sys.path:
    sys.path.insert(0, str(HOOK_DIR))

from guard_common import inspect_payload, read_hook_payload  # noqa: E402


def main() -> int:
    decision = inspect_payload(read_hook_payload())
    if decision.blocked:
        sys.stderr.write((decision.reason or "blocked by remote-dev guard") + "\n")
        return 2
    if decision.additional_context:
        sys.stdout.write(decision.additional_context + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
