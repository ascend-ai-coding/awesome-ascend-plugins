from __future__ import annotations

import time
from typing import Any

from .endpoint import Endpoint
from .result import make_result, utc_now_iso
from .ssh_transport import run_remote_python
from .state_store import atomic_write_json, ensure_endpoint_state

REMOTE_PROBE_PY = r'''
import importlib
import json
import os
import pathlib
import platform
import subprocess
import sys

payload = json.loads(sys.stdin.read())
root = pathlib.Path(payload["root"])

def run(cmd, timeout=8):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return {"returncode": proc.returncode, "stdout_tail": (proc.stdout or "")[-2000:], "stderr_tail": (proc.stderr or "")[-2000:]}
    except Exception as exc:
        return {"returncode": None, "error": str(exc)}

def module_info(name):
    try:
        module = importlib.import_module(name)
        return {"available": True, "version": str(getattr(module, "__version__", "unknown")), "file": str(getattr(module, "__file__", ""))}
    except BaseException as exc:
        return {"available": False, "error": repr(exc)}

summary = {
    "hostname": platform.node(),
    "python": sys.version.split()[0],
    "python_executable": sys.executable,
    "cwd": os.getcwd(),
    "root_exists": root.exists(),
    "git_root": run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], timeout=5),
    "root_head": run(["git", "-C", str(root), "rev-parse", "HEAD"], timeout=5),
    "vllm_head": run(["git", "-C", str(root / "vllm"), "rev-parse", "HEAD"], timeout=5) if (root / "vllm").exists() else None,
    "vllm_ascend_head": run(["git", "-C", str(root / "vllm-ascend"), "rev-parse", "HEAD"], timeout=5) if (root / "vllm-ascend").exists() else None,
    "modules": {name: module_info(name) for name in ("torch", "torch_npu", "vllm", "vllm_ascend")},
}
print(json.dumps({"status": "ok", "summary": summary}, sort_keys=True))
'''


def write_context_snapshot(endpoint: Endpoint, summary: dict[str, Any], full_probe: dict[str, Any] | None = None) -> dict[str, Any]:
    base = ensure_endpoint_state(endpoint) / "context"
    payload = {
        "schema_version": "remote-dev.context.v1",
        "endpoint": {
            "endpoint_id": endpoint.endpoint_id,
            "host": endpoint.host,
            "port": endpoint.port,
            "user": endpoint.user,
            "root": endpoint.root,
            "default_cwd": endpoint.effective_cwd,
        },
        "summary": summary,
        "volatility": {
            "endpoint": "stable",
            "git_state": "semi_stable",
            "service_state": "volatile",
            "job_state": "volatile",
            "npu_state": "volatile",
        },
        "refs": {},
        "created_at": utc_now_iso(),
        "ttl_seconds": 300,
    }
    stamp = payload["created_at"].replace(":", "").replace("-", "")
    full_path = base / f"context-{stamp}.json"
    atomic_write_json(full_path, payload if full_probe is None else {**payload, "full_probe": full_probe})
    atomic_write_json(base / "latest.json", payload)
    payload["refs"]["full_probe"] = str(full_path)
    return payload


def _duration_ms(start: float) -> int:
    return int(round((time.monotonic() - start) * 1000))


def remote_probe(endpoint: Endpoint, *, timeout_ms: int = 120000) -> dict[str, Any]:
    started = utc_now_iso()
    start = time.monotonic()
    data = run_remote_python(endpoint, REMOTE_PROBE_PY, {"root": endpoint.root}, timeout_ms=timeout_ms)
    status = str(data.get("status", "failed"))
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    snapshot = write_context_snapshot(endpoint, summary, data) if status == "ok" else None
    result = make_result(
        tool="remote.probe",
        target=endpoint.to_result_target(),
        outcome="success" if status == "ok" else ("timeout" if status == "timeout" else "failed"),
        status=status,
        summary="Remote probe completed." if status == "ok" else "Remote probe failed.",
        started_at=started,
        duration_ms=_duration_ms(start),
        preview={"summary": summary},
        refs=snapshot.get("refs", {}) if isinstance(snapshot, dict) else {},
        extra={"snapshot": snapshot, "error": data.get("error"), "probe": data},
    )
    text = "RemoteProbe {status} on {user}@{host}:{port}\n".format(
        status=status,
        user=endpoint.user,
        host=endpoint.host,
        port=endpoint.port,
    )
    if summary:
        text += "hostname: {hostname}\npython: {python}\n".format(
            hostname=summary.get("hostname", ""),
            python=summary.get("python", ""),
        )
    return {"text": text, "result": result}


def remote_context_snapshot(endpoint: Endpoint, *, timeout_ms: int = 120000, live_probe: bool = True) -> dict[str, Any]:
    if live_probe:
        payload = remote_probe(endpoint, timeout_ms=timeout_ms)
        payload["result"]["tool"] = "remote.context_snapshot"
        return payload
    snapshot = write_context_snapshot(endpoint, {"status": "ok", "note": "snapshot requested without live probe"})
    result = make_result(
        tool="remote.context_snapshot",
        target=endpoint.to_result_target(),
        outcome="success",
        status="ok",
        summary="Context snapshot written.",
        preview={"summary": snapshot["summary"]},
        refs=snapshot.get("refs", {}),
        extra={"snapshot": snapshot},
    )
    return {"text": "Remote context snapshot written.\n", "result": result}
