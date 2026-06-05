from __future__ import annotations

import hashlib
import os
import shlex
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import Any

from .endpoint import Endpoint
from .errors import PathPolicyError
from .path_policy import join_under_root
from .result import make_result, utc_now_iso
from .ssh_transport import run_bytes, run_remote_python
from .state_store import atomic_write_json, ensure_endpoint_state

REMOTE_MANIFEST_PY = r'''
import hashlib
import json
import os
import pathlib
import stat
import sys

payload = json.loads(sys.stdin.read())
root = pathlib.Path(payload["root"]).resolve()
target = pathlib.Path(payload["remote_path"])
if not target.is_absolute():
    target = pathlib.Path(payload.get("cwd") or payload["root"]) / target
try:
    resolved = target.resolve()
except FileNotFoundError:
    print(json.dumps({"status": "needs_input", "error": "remote path does not exist", "remote_path": str(target)}))
    raise SystemExit(0)
if resolved != root and root not in resolved.parents:
    print(json.dumps({"status": "blocked", "error": f"remote path is outside root: {resolved}", "remote_path": str(target)}))
    raise SystemExit(0)
if target.is_symlink():
    print(json.dumps({"status": "blocked", "error": "artifact symlinks are not allowed", "remote_path": str(target)}))
    raise SystemExit(0)

def sha256_file(path):
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size

files = []
paths = [target] if target.is_file() else sorted(pathlib.Path(target).rglob("*"))
for path in paths:
    if path.is_symlink():
        print(json.dumps({"status": "blocked", "error": f"artifact symlink is not allowed: {path}"}))
        raise SystemExit(0)
    if not path.is_file():
        continue
    digest, size = sha256_file(path)
    st = path.stat()
    files.append({
        "relpath": "." if path == target else str(path.relative_to(target)),
        "path": str(path),
        "size": size,
        "sha256": digest,
        "mode": stat.S_IMODE(st.st_mode),
        "mtime_ns": st.st_mtime_ns,
    })
print(json.dumps({
    "schema_version": "remote-dev.artifact_manifest.v1",
    "status": "ok",
    "root": str(target),
    "is_dir": target.is_dir(),
    "file_count": len(files),
    "total_bytes": sum(item["size"] for item in files),
    "files": files,
}, sort_keys=True))
'''


def _duration_ms(start: float) -> int:
    return int(round((time.monotonic() - start) * 1000))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _local_manifest(local_path: Path) -> dict[str, Any]:
    raw_path = local_path.expanduser()
    if raw_path.is_symlink():
        raise ValueError(f"local artifact symlinks are not allowed: {raw_path}")
    resolved = raw_path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"local artifact path does not exist: {resolved}")
    files: list[dict[str, Any]] = []
    roots = [resolved] if resolved.is_file() else sorted(path for path in resolved.rglob("*") if path.is_file())
    for path in roots:
        if path.is_symlink():
            raise ValueError(f"local artifact symlinks are not allowed: {path}")
        stat = path.stat()
        files.append({
            "relpath": "." if path == resolved else str(path.relative_to(resolved)),
            "path": str(path),
            "size": stat.st_size,
            "sha256": _sha256_file(path),
            "mtime_ns": stat.st_mtime_ns,
        })
    return {
        "schema_version": "remote-dev.local_artifact_manifest.v1",
        "status": "ok",
        "local_path": str(resolved),
        "is_dir": resolved.is_dir(),
        "file_count": len(files),
        "total_bytes": sum(item["size"] for item in files),
        "files": files,
    }


def _safe_local_artifact_path(base: Path, relpath: str) -> Path:
    if relpath == ".":
        relpath = "artifact"
    rel = PurePosixPath(relpath)
    if rel.is_absolute() or any(part in {"..", ""} for part in rel.parts):
        raise ValueError(f"unsafe artifact relpath: {relpath}")
    candidate = base.joinpath(*rel.parts)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    base_resolved = base.resolve()
    parent_resolved = candidate.parent.resolve()
    if parent_resolved != base_resolved and base_resolved not in parent_resolved.parents:
        raise ValueError(f"artifact relpath escapes local dir: {relpath}")
    if candidate.is_symlink():
        raise ValueError(f"refusing to overwrite local symlink: {candidate}")
    return candidate


def remote_artifact_manifest(endpoint: Endpoint, *, remote_path: str, timeout_ms: int = 120000) -> dict[str, Any]:
    started = utc_now_iso()
    start = time.monotonic()
    try:
        path = join_under_root(endpoint.root, endpoint.effective_cwd, remote_path)
    except PathPolicyError as exc:
        result = make_result(
            tool="remote.artifact_manifest",
            target=endpoint.to_result_target(),
            outcome="blocked",
            status="path_outside_root",
            summary=f"Remote artifact manifest blocked for {remote_path}.",
            started_at=started,
            duration_ms=_duration_ms(start),
            preview={"stderr": str(exc)},
            extra={"error": str(exc)},
        )
        return {"text": result["summary"] + "\n" + str(exc) + "\n", "result": result}
    data = run_remote_python(
        endpoint,
        REMOTE_MANIFEST_PY,
        {"root": endpoint.root, "cwd": endpoint.effective_cwd, "remote_path": path},
        timeout_ms=timeout_ms,
    )
    if isinstance(data, dict) and data.get("status") == "ok":
        data["endpoint_id"] = endpoint.endpoint_id
        artifact_id = f"manifest-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        data["artifact_id"] = artifact_id
        manifest_path = ensure_endpoint_state(endpoint) / "artifacts" / artifact_id / "manifest.json"
        atomic_write_json(manifest_path, data)
    else:
        manifest_path = None
    status = str(data.get("status", "failed"))
    result = make_result(
        tool="remote.artifact_manifest",
        target=endpoint.to_result_target(),
        outcome="success" if status == "ok" else ("blocked" if status == "blocked" else "failed"),
        status=status,
        summary=f"Remote artifact manifest {status} for {path}.",
        started_at=started,
        duration_ms=_duration_ms(start),
        refs={"local_manifest": str(manifest_path)} if manifest_path else {},
        artifacts=[data] if status == "ok" else [],
        extra={"manifest": data, "error": data.get("error")},
    )
    return {"text": f"RemoteArtifactManifest {status}: {path}\nfiles: {data.get('file_count', 0)}\n", "result": result}


def remote_artifact_pull(
    endpoint: Endpoint,
    *,
    remote_path: str,
    local_dir: str | None = None,
    timeout_ms: int = 120000,
) -> dict[str, Any]:
    started = utc_now_iso()
    start = time.monotonic()
    manifest_payload = remote_artifact_manifest(endpoint, remote_path=remote_path, timeout_ms=timeout_ms)
    manifest = manifest_payload["result"].get("manifest", {})
    if manifest.get("status") != "ok":
        return manifest_payload
    base = Path(local_dir) if local_dir else ensure_endpoint_state(endpoint) / "artifacts" / str(int(time.time()))
    base.mkdir(parents=True, exist_ok=True)
    pulled = []
    skipped = []
    for item in manifest.get("files", []):
        relpath = item["relpath"]
        try:
            local_path = _safe_local_artifact_path(base, str(relpath))
        except ValueError as exc:
            result = make_result(
                tool="remote.artifact_pull",
                target=endpoint.to_result_target(),
                outcome="blocked",
                status="path_traversal",
                summary=f"Blocked unsafe artifact path {relpath}.",
                started_at=started,
                duration_ms=_duration_ms(start),
                artifacts=[{"manifest": manifest, "pulled": pulled, "skipped": skipped}],
                preview={"stderr": str(exc)},
                extra={"error": str(exc)},
            )
            return {"text": result["summary"] + "\n" + str(exc) + "\n", "result": result}
        if local_path.exists() and _sha256_file(local_path) == item["sha256"]:
            skipped.append({"relpath": relpath, "local_path": str(local_path), "reason": "hash-match"})
            continue
        proc = run_bytes(endpoint, f"cat {shlex.quote(item['path'])}", timeout_ms=timeout_ms)
        if proc.returncode != 0:
            result = make_result(
                tool="remote.artifact_pull",
                target=endpoint.to_result_target(),
                outcome="failed",
                status="failed",
                summary=f"Failed to pull remote artifact {item['path']}.",
                started_at=started,
                duration_ms=_duration_ms(start),
                preview={"stderr": proc.stderr.decode("utf-8", errors="replace")[-4000:]},
                artifacts=[{"manifest": manifest, "pulled": pulled, "skipped": skipped}],
            )
            return {"text": result["summary"] + "\n", "result": result}
        tmp = local_path.with_suffix(local_path.suffix + ".tmp")
        tmp.write_bytes(proc.stdout)
        observed = _sha256_file(tmp)
        if observed != item["sha256"]:
            tmp.unlink(missing_ok=True)
            result = make_result(
                tool="remote.artifact_pull",
                target=endpoint.to_result_target(),
                outcome="failed",
                status="hash_mismatch",
                summary=f"Hash mismatch pulling {item['path']}.",
                started_at=started,
                duration_ms=_duration_ms(start),
                artifacts=[{"manifest": manifest, "pulled": pulled, "skipped": skipped}],
                extra={"expected_sha256": item["sha256"], "observed_sha256": observed},
            )
            return {"text": result["summary"] + "\n", "result": result}
        os.replace(tmp, local_path)
        pulled.append({"relpath": relpath, "local_path": str(local_path), "sha256": observed, "size": item["size"]})
    manifest_path = base / "manifest.json"
    atomic_write_json(manifest_path, manifest)
    result = make_result(
        tool="remote.artifact_pull",
        target=endpoint.to_result_target(),
        outcome="success",
        status="ok",
        summary=f"Pulled {len(pulled)} files from {remote_path}.",
        started_at=started,
        duration_ms=_duration_ms(start),
        refs={"local_manifest": str(manifest_path)},
        artifacts=[{"remote_path": remote_path, "local_dir": str(base), "manifest": manifest, "pulled": pulled, "skipped": skipped}],
    )
    return {"text": f"RemoteArtifactPull completed\nlocal_dir: {base}\npulled: {len(pulled)}\nskipped: {len(skipped)}\n", "result": result}


def remote_artifact_push(
    endpoint: Endpoint,
    *,
    local_path: str,
    remote_path: str,
    timeout_ms: int = 120000,
) -> dict[str, Any]:
    started = utc_now_iso()
    start = time.monotonic()
    try:
        remote_base = join_under_root(endpoint.root, endpoint.effective_cwd, remote_path)
    except PathPolicyError as exc:
        result = make_result(
            tool="remote.artifact_push",
            target=endpoint.to_result_target(),
            outcome="blocked",
            status="path_outside_root",
            summary=f"Remote artifact push blocked for {remote_path}.",
            started_at=started,
            duration_ms=_duration_ms(start),
            preview={"stderr": str(exc)},
            extra={"error": str(exc)},
        )
        return {"text": result["summary"] + "\n" + str(exc) + "\n", "result": result}
    try:
        manifest = _local_manifest(Path(local_path))
    except (FileNotFoundError, ValueError) as exc:
        result = make_result(
            tool="remote.artifact_push",
            target=endpoint.to_result_target(),
            outcome="blocked" if isinstance(exc, ValueError) else "needs_input",
            status="symlink_not_allowed" if isinstance(exc, ValueError) else "local_path_not_found",
            summary="Remote artifact push could not read local artifact.",
            started_at=started,
            duration_ms=_duration_ms(start),
            preview={"stderr": str(exc)},
            extra={"error": str(exc)},
        )
        return {"text": result["summary"] + "\n" + str(exc) + "\n", "result": result}

    pushed: list[dict[str, Any]] = []
    for item in manifest["files"]:
        relpath = str(item["relpath"])
        remote_file = remote_base if relpath == "." else str(PurePosixPath(remote_base) / PurePosixPath(relpath))
        try:
            remote_file = join_under_root(endpoint.root, endpoint.effective_cwd, remote_file)
        except PathPolicyError as exc:
            result = make_result(
                tool="remote.artifact_push",
                target=endpoint.to_result_target(),
                outcome="blocked",
                status="path_outside_root",
                summary=f"Remote artifact push blocked for {remote_file}.",
                started_at=started,
                duration_ms=_duration_ms(start),
                artifacts=[{"manifest": manifest, "pushed": pushed}],
                preview={"stderr": str(exc)},
                extra={"error": str(exc)},
            )
            return {"text": result["summary"] + "\n" + str(exc) + "\n", "result": result}
        remote_tmp = f"{remote_file}.tmp-{uuid.uuid4().hex[:8]}"
        remote_parent = str(PurePosixPath(remote_file).parent)
        command = "\n".join(
            [
                "set -e",
                f"mkdir -p {shlex.quote(remote_parent)}",
                f"cat > {shlex.quote(remote_tmp)}",
                "observed=$(python3 - " + shlex.quote(remote_tmp) + " <<'PY'",
                "import hashlib, pathlib, sys",
                "path = pathlib.Path(sys.argv[1])",
                "h = hashlib.sha256()",
                "with path.open('rb') as fh:",
                "    for chunk in iter(lambda: fh.read(1024 * 1024), b''):",
                "        h.update(chunk)",
                "print(h.hexdigest())",
                "PY",
                ")",
                f"if [ \"$observed\" != {shlex.quote(str(item['sha256']))} ]; then rm -f {shlex.quote(remote_tmp)}; printf '%s\\n' \"$observed\"; exit 74; fi",
                f"mv -f {shlex.quote(remote_tmp)} {shlex.quote(remote_file)}",
                'printf \'%s\\n\' "$observed"',
            ]
        )
        proc = run_bytes(endpoint, command, stdin=Path(item["path"]).read_bytes(), timeout_ms=timeout_ms)
        observed = proc.stdout.decode("utf-8", errors="replace").strip().splitlines()[-1:] or [""]
        if proc.returncode != 0 or observed[0] != item["sha256"]:
            result = make_result(
                tool="remote.artifact_push",
                target=endpoint.to_result_target(),
                outcome="failed",
                status="hash_mismatch" if proc.returncode == 74 else "failed",
                summary=f"Failed to push local artifact {item['path']}.",
                started_at=started,
                duration_ms=_duration_ms(start),
                artifacts=[{"manifest": manifest, "pushed": pushed}],
                preview={"stderr": proc.stderr.decode("utf-8", errors="replace")[-4000:]},
                extra={"expected_sha256": item["sha256"], "observed_sha256": observed[0], "exit_code": proc.returncode},
            )
            return {"text": result["summary"] + "\n", "result": result}
        pushed.append({
            "relpath": relpath,
            "local_path": item["path"],
            "remote_path": remote_file,
            "sha256": observed[0],
            "size": item["size"],
        })
    result = make_result(
        tool="remote.artifact_push",
        target=endpoint.to_result_target(),
        outcome="success",
        status="ok",
        summary=f"Pushed {len(pushed)} files to {remote_base}.",
        started_at=started,
        duration_ms=_duration_ms(start),
        artifacts=[{"remote_path": remote_base, "manifest": manifest, "pushed": pushed}],
    )
    return {"text": f"RemoteArtifactPush completed\nremote_path: {remote_base}\npushed: {len(pushed)}\n", "result": result}
