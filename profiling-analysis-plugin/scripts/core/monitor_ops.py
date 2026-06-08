from __future__ import annotations

from typing import Any

from .endpoint import Endpoint
from .shell_ops import remote_bash


def remote_monitor(
    endpoint: Endpoint,
    *,
    command: str,
    cwd: str | None = None,
    description: str | None = None,
    timeout_ms: int | None = 600000,
    pattern: str | None = None,
    env: dict[str, str] | None = None,
    runtime_env: bool | None = None,
) -> dict[str, Any]:
    monitor_description = description or "Remote monitor"
    if pattern:
        monitor_description = f"{monitor_description}; pattern={pattern}"
    return remote_bash(
        endpoint,
        command=command,
        cwd=cwd,
        description=monitor_description,
        timeout_ms=timeout_ms,
        run_in_background=True,
        runtime_env=runtime_env,
        env=env or {},
    )
