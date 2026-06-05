from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any

from .endpoint import Endpoint


@dataclass
class RemoteCompleted:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool = False


def ssh_base_cmd(endpoint: Endpoint) -> list[str]:
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "LogLevel=ERROR",
        "-o",
        f"ConnectTimeout={max(1, int(endpoint.connect_timeout_ms / 1000))}",
    ]
    if endpoint.identity_file:
        cmd.extend(["-i", endpoint.identity_file])
    cmd.extend(["-p", str(endpoint.port), endpoint.destination()])
    return cmd


def run_script(endpoint: Endpoint, script: str, *, timeout_ms: int | None = None) -> RemoteCompleted:
    timeout = None if timeout_ms is None else timeout_ms / 1000
    try:
        proc = subprocess.run(
            [*ssh_base_cmd(endpoint), "bash", "-s"],
            input=script,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return RemoteCompleted(proc.returncode, proc.stdout or "", proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        stdout = _decode_stream(exc.stdout)
        stderr = _decode_stream(exc.stderr)
        return RemoteCompleted(None, stdout, stderr, timed_out=True)


def run_bytes(
    endpoint: Endpoint,
    remote_command: str,
    *,
    stdin: bytes | None = None,
    timeout_ms: int | None = None,
) -> subprocess.CompletedProcess[bytes]:
    timeout = None if timeout_ms is None else timeout_ms / 1000
    return subprocess.run(
        [*ssh_base_cmd(endpoint), f"bash -c {shlex.quote(remote_command)}"],
        input=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def run_remote_python(
    endpoint: Endpoint,
    code: str,
    payload: dict[str, Any],
    *,
    timeout_ms: int | None = None,
) -> dict[str, Any]:
    timeout = None if timeout_ms is None else timeout_ms / 1000
    try:
        proc = subprocess.run(
            [*ssh_base_cmd(endpoint), f"python3 -c {shlex.quote(code)}"],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "error": f"remote python timed out after {timeout_ms} ms",
            "stdout_tail": _decode_stream(exc.stdout)[-4000:],
            "stderr_tail": _decode_stream(exc.stderr)[-4000:],
        }
    if proc.returncode != 0:
        return {
            "status": "failed",
            "error": "remote python failed",
            "exit_code": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-4000:],
            "stderr_tail": (proc.stderr or "")[-4000:],
        }
    try:
        data = json.loads((proc.stdout or "").strip())
    except json.JSONDecodeError as exc:
        return {
            "status": "failed",
            "error": f"remote python returned non-JSON: {exc}",
            "stdout_tail": (proc.stdout or "")[-4000:],
            "stderr_tail": (proc.stderr or "")[-4000:],
        }
    return data if isinstance(data, dict) else {"status": "failed", "error": "remote python JSON was not an object"}


def _decode_stream(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
