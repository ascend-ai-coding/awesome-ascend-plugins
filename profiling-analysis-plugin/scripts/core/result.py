from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

Outcome = Literal["success", "needs_input", "blocked", "failed", "timeout", "cancelled"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_invocation_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def make_result(
    *,
    tool: str,
    target: dict[str, Any],
    outcome: Outcome,
    status: str,
    summary: str,
    invocation_id: str | None = None,
    started_at: str | None = None,
    duration_ms: int | None = None,
    preview: dict[str, Any] | None = None,
    refs: dict[str, Any] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
    changed_files: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
    next: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "remote-dev.result.v1",
        "tool": tool,
        "invocation_id": invocation_id or new_invocation_id(),
        "target": target,
        "outcome": outcome,
        "status": status,
        "summary": summary,
        "started_at": started_at or utc_now_iso(),
        "duration_ms": duration_ms,
        "preview": preview or {},
        "refs": refs or {},
        "artifacts": artifacts or [],
        "changed_files": changed_files or [],
        "warnings": warnings or [],
        "next": next,
    }
    if extra:
        payload.update(extra)
    return payload


def dumps(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
