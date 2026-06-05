from __future__ import annotations

from pathlib import Path
from typing import Any

from .endpoint import Endpoint
from .state_store import load_read_ledger, read_ledger_path, write_read_ledger


def ledger_path(endpoint: Endpoint, file_path: str, client_context_id: str | None = None) -> Path:
    return read_ledger_path(endpoint, file_path, client_context_id)


def record_read(endpoint: Endpoint, file_info: dict[str, Any], client_context_id: str | None = None) -> Path:
    return write_read_ledger(endpoint, file_info, client_context_id)


def load_read(endpoint: Endpoint, file_path: str, client_context_id: str | None = None) -> dict[str, Any] | None:
    return load_read_ledger(endpoint, file_path, client_context_id)
