from __future__ import annotations

import shlex
import time
import uuid
from pathlib import PurePosixPath
from typing import Any

from .endpoint import Endpoint
from .errors import PathPolicyError
from .path_policy import join_under_root
from .result import make_result, utc_now_iso
from .ssh_transport import run_remote_python, run_script
from .state_store import atomic_write_json, ensure_endpoint_state

REMOTE_CODEX_PATCH_PY = r'''
import difflib
import hashlib
import json
import os
import pathlib
import sys
import tempfile

payload = json.loads(sys.stdin.read())
root = pathlib.Path(payload["root"]).resolve()
cwd = pathlib.Path(payload["cwd"]).resolve()
ops = payload["ops"]
DELETED = object()

def fail(status, error=None, **extra):
    data = {"status": status}
    if error:
        data["error"] = error
    data.update(extra)
    print(json.dumps(data, sort_keys=True))
    raise SystemExit(0)

def resolve_path(raw, *, parent_ok=False):
    p = pathlib.Path(raw)
    if not p.is_absolute():
        p = cwd / p
    try:
        if p.exists() or p.is_symlink():
            resolved = p.resolve()
        elif parent_ok:
            resolved = p.parent.resolve() / p.name
        else:
            resolved = p.resolve(strict=True)
    except FileNotFoundError:
        fail("not_found", f"remote path does not exist: {p}")
    if resolved != root and root not in resolved.parents:
        fail("path_outside_root", f"remote path is outside root: {resolved} not under {root}")
    return p

def sha(data):
    return hashlib.sha256(data).hexdigest()

def file_bytes(path):
    if path in virtual:
        data = virtual[path]
        return None if data is DELETED else data
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        fail("symlink_not_allowed" if path.is_symlink() else "not_file", f"refusing to patch non-regular file: {path}")
    return path.read_bytes()

def file_sha_bytes(data):
    return sha(data) if data is not None else None

def exists_in_virtual(path):
    data = file_bytes(path)
    return data is not None

def atomic_write(path, data, mode=None):
    if path.is_symlink():
        fail("symlink_not_allowed", f"refusing to patch symlink: {path}")
    if path.exists() and not path.is_file():
        fail("not_file", f"refusing to patch non-regular file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        if mode is not None:
            os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass

def snapshot_real(path):
    if not path.exists() and not path.is_symlink():
        return {"exists": False, "bytes": None, "mode": None}
    if path.is_symlink() or not path.is_file():
        fail("symlink_not_allowed" if path.is_symlink() else "not_file", f"refusing to patch non-regular file: {path}")
    st = path.stat()
    return {"exists": True, "bytes": path.read_bytes(), "mode": st.st_mode & 0o777}

def restore(before_state):
    restored = []
    failed = []
    for path, state in reversed(list(before_state.items())):
        try:
            if state["exists"]:
                atomic_write(path, state["bytes"], state["mode"])
            else:
                if path.exists() or path.is_symlink():
                    path.unlink()
            restored.append(str(path))
        except Exception as exc:  # noqa: BLE001
            failed.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
    return {"restored": restored, "failed": failed}

changed = []
diffs = []
virtual = {}
touched_paths = []
for op in ops:
    kind = op["kind"]
    path = resolve_path(op["path"], parent_ok=True)
    before_bytes = file_bytes(path)
    before_sha = file_sha_bytes(before_bytes)
    before_text = before_bytes.decode("utf-8", errors="replace") if before_bytes is not None else ""
    path_for_diff = path
    if kind == "add":
        if exists_in_virtual(path) or path.is_symlink():
            fail("file_exists", f"add file target already exists: {path}")
        after_text = op.get("content", "")
        virtual[path] = after_text.encode("utf-8")
    elif kind == "delete":
        if before_bytes is None:
            fail("not_found", f"delete target does not exist: {path}")
        virtual[path] = DELETED
        after_text = ""
    elif kind == "update":
        if before_bytes is None:
            fail("not_found", f"update target does not exist: {path}")
        target_path = resolve_path(op["move_to"], parent_ok=True) if op.get("move_to") else path
        if op.get("move_to"):
            if exists_in_virtual(target_path) or target_path.exists() or target_path.is_symlink():
                fail("file_exists", f"move target already exists: {target_path}")
        after_text = before_text
        for hunk_index, hunk in enumerate(op.get("hunks", [])):
            old = hunk["old"]
            new = hunk["new"]
            if old not in after_text:
                fail("context_mismatch", f"patch context not found in {path}; re-run remote.read before retrying", hunk_index=hunk_index)
            after_text = after_text.replace(old, new, 1)
        virtual[target_path] = after_text.encode("utf-8")
        if target_path != path:
            virtual[path] = DELETED
        path_for_diff = target_path
    else:
        fail("invalid_patch", f"unsupported patch op: {kind}")
    if path not in touched_paths:
        touched_paths.append(path)
    if path_for_diff not in touched_paths:
        touched_paths.append(path_for_diff)
    after_sha = file_sha_bytes(file_bytes(path_for_diff))
    diff = "".join(difflib.unified_diff(
        before_text.splitlines(keepends=True),
        after_text.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path_for_diff}",
        n=3,
    ))
    diffs.append(diff)
    changed.append({
        "path": str(path_for_diff),
        "old_path": str(path) if path_for_diff != path else None,
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "size": path_for_diff.stat().st_size if path_for_diff.exists() else 0,
        "op": "move" if kind == "update" and op.get("move_to") and not op.get("hunks") else kind,
    })

before_state = {path: snapshot_real(path) for path in touched_paths}
try:
    for path, data in virtual.items():
        if data is DELETED:
            continue
        mode = before_state.get(path, {}).get("mode")
        atomic_write(path, data, mode)
    for path, data in virtual.items():
        if data is DELETED and (path.exists() or path.is_symlink()):
            path.unlink()
except Exception as exc:  # noqa: BLE001
    rollback_status = restore(before_state)
    fail("commit_failed", f"{type(exc).__name__}: {exc}", rollback_status=rollback_status)

for item in changed:
    path = pathlib.Path(item["path"])
    item["after_sha256"] = sha(path.read_bytes()) if path.exists() and path.is_file() else None
    item["size"] = path.stat().st_size if path.exists() else 0
print(json.dumps({"status": "applied", "changed_files": changed, "diff_preview": "".join(diffs)[:16000]}, sort_keys=True))
'''


class PatchParseError(ValueError):
    pass


def _is_patch_boundary(line: str) -> bool:
    stripped = line.strip("\r\n")
    return (
        stripped == "*** End Patch"
        or stripped.startswith("*** Add File: ")
        or stripped.startswith("*** Delete File: ")
        or stripped.startswith("*** Update File: ")
    )


def parse_codex_patch(patch: str) -> list[dict[str, Any]]:
    lines = patch.splitlines(keepends=True)
    if not lines or lines[0].strip() != "*** Begin Patch":
        raise PatchParseError("Codex patch must start with *** Begin Patch")
    ops: list[dict[str, Any]] = []
    i = 1
    while i < len(lines):
        stripped = lines[i].strip("\r\n")
        if stripped == "*** End Patch":
            break
        if stripped.startswith("*** Add File: "):
            path = stripped.removeprefix("*** Add File: ").strip()
            i += 1
            content: list[str] = []
            while i < len(lines) and not lines[i].startswith("*** "):
                if not lines[i].startswith("+"):
                    raise PatchParseError(f"add file line must start with '+': {lines[i]!r}")
                content.append(lines[i][1:])
                i += 1
            ops.append({"kind": "add", "path": path, "content": "".join(content)})
            continue
        if stripped.startswith("*** Delete File: "):
            path = stripped.removeprefix("*** Delete File: ").strip()
            ops.append({"kind": "delete", "path": path})
            i += 1
            continue
        if stripped.startswith("*** Update File: "):
            path = stripped.removeprefix("*** Update File: ").strip()
            i += 1
            hunks: list[dict[str, str]] = []
            old_parts: list[str] = []
            new_parts: list[str] = []
            saw_hunk_line = False
            move_to: str | None = None
            while i < len(lines) and not _is_patch_boundary(lines[i]):
                line = lines[i]
                stripped_line = line.strip("\r\n")
                if stripped_line.startswith("*** Move to: "):
                    if move_to is not None:
                        raise PatchParseError(f"update patch for {path} has multiple move targets")
                    move_to = stripped_line.removeprefix("*** Move to: ").strip()
                    i += 1
                    continue
                if stripped_line == "*** End of File":
                    i += 1
                    continue
                if line.startswith("@@"):
                    if saw_hunk_line and (old_parts or new_parts):
                        hunks.append({"old": "".join(old_parts), "new": "".join(new_parts)})
                        old_parts = []
                        new_parts = []
                    saw_hunk_line = True
                    i += 1
                    continue
                if not line:
                    i += 1
                    continue
                prefix = line[0]
                body = line[1:] if prefix in {" ", "+", "-"} else line
                if prefix == " ":
                    old_parts.append(body)
                    new_parts.append(body)
                elif prefix == "-":
                    old_parts.append(body)
                elif prefix == "+":
                    new_parts.append(body)
                else:
                    raise PatchParseError(f"unsupported update patch line: {line!r}")
                saw_hunk_line = True
                i += 1
            if old_parts or new_parts:
                hunks.append({"old": "".join(old_parts), "new": "".join(new_parts)})
            if not hunks and not move_to:
                raise PatchParseError(f"update patch for {path} has no hunks")
            op: dict[str, Any] = {"kind": "update", "path": path, "hunks": hunks}
            if move_to:
                op["move_to"] = move_to
            ops.append(op)
            continue
        raise PatchParseError(f"unsupported patch directive: {stripped}")
    if not ops:
        raise PatchParseError("patch did not contain file operations")
    return ops


def parse_unified_patch_paths(patch: str) -> list[str]:
    paths: list[str] = []
    for line in patch.splitlines():
        path: str | None = None
        if line.startswith("+++ "):
            raw = line[4:].strip()
            if raw != "/dev/null":
                path = raw[2:] if raw.startswith("b/") else raw
        elif line.startswith("--- "):
            raw = line[4:].strip()
            if raw != "/dev/null":
                path = raw[2:] if raw.startswith("a/") else raw
        elif line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                raw = parts[3]
                path = raw[2:] if raw.startswith("b/") else raw
        if path and path not in paths:
            paths.append(path)
    if not paths:
        raise PatchParseError("unified diff did not contain file paths")
    return paths


def _duration_ms(start: float) -> int:
    return int(round((time.monotonic() - start) * 1000))


def remote_apply_patch(
    endpoint: Endpoint,
    *,
    patch: str | None = None,
    command: str | None = None,
    cwd: str | None = None,
    timeout_ms: int = 120000,
) -> dict[str, Any]:
    payload = patch if patch is not None else command
    if not payload:
        result = make_result(
            tool="remote.apply_patch",
            target=endpoint.to_result_target(),
            outcome="needs_input",
            status="patch_required",
            summary="RemoteApplyPatch requires patch or command.",
        )
        return {"text": result["summary"] + "\n", "result": result}
    started = utc_now_iso()
    start = time.monotonic()
    try:
        effective_cwd = join_under_root(endpoint.root, endpoint.effective_cwd, cwd or endpoint.effective_cwd)
    except PathPolicyError as exc:
        return _patch_failed(endpoint, started, start, "path_outside_root", str(exc), outcome="blocked")
    if payload.lstrip().startswith("*** Begin Patch"):
        try:
            ops = parse_codex_patch(payload)
            for op in ops:
                join_under_root(endpoint.root, effective_cwd, op["path"])
                if op.get("move_to"):
                    join_under_root(endpoint.root, effective_cwd, str(op["move_to"]))
        except PatchParseError as exc:
            return _patch_failed(endpoint, started, start, "invalid_patch", str(exc))
        except PathPolicyError as exc:
            return _patch_failed(endpoint, started, start, "path_outside_root", str(exc), outcome="blocked")
        data = run_remote_python(
            endpoint,
            REMOTE_CODEX_PATCH_PY,
            {"root": endpoint.root, "cwd": effective_cwd, "ops": ops},
            timeout_ms=timeout_ms,
        )
        return _patch_result(endpoint, started, start, effective_cwd, data)
    try:
        paths = parse_unified_patch_paths(payload)
        for path in paths:
            join_under_root(endpoint.root, effective_cwd, path)
    except PatchParseError as exc:
        return _patch_failed(endpoint, started, start, "invalid_patch", str(exc))
    except PathPolicyError as exc:
        return _patch_failed(endpoint, started, start, "path_outside_root", str(exc), outcome="blocked")
    return _apply_unified_patch(endpoint, payload, paths, effective_cwd, started, start, timeout_ms=timeout_ms)


def _apply_unified_patch(
    endpoint: Endpoint,
    patch: str,
    paths: list[str],
    cwd: str,
    started: str,
    start: float,
    *,
    timeout_ms: int,
) -> dict[str, Any]:
    delimiter = f"REMOTE_DEV_PATCH_{uuid.uuid4().hex}"
    path_args = " ".join(shlex.quote(path) for path in paths)
    script = "\n".join(
        [
            "set -e",
            f"cd {shlex.quote(cwd)}",
            "tmp=$(mktemp)",
            "tmp_before=\"$tmp.before\"",
            "tmp_stat=\"$tmp.stat\"",
            f"cat > \"$tmp\" <<'{delimiter}'",
            patch,
            delimiter,
            "python3 - \"$tmp_before\" " + shlex.quote(endpoint.root) + " " + shlex.quote(cwd) + " " + path_args + " <<'REMOTE_DEV_BEFORE'",
            "import hashlib, json, pathlib, sys",
            "def fail(status, error):",
            "    print(f'REMOTE_DEV_PATCH_PREFLIGHT {status}: {error}', file=sys.stderr)",
            "    raise SystemExit(72)",
            "root=pathlib.Path(sys.argv[2]).resolve()",
            "cwd=pathlib.Path(sys.argv[3]).resolve()",
            "before={}",
            "for raw in sys.argv[4:]:",
            "    p=pathlib.Path(raw)",
            "    if not p.is_absolute():",
            "        p=cwd / p",
            "    if p.exists() or p.is_symlink():",
            "        resolved=p.resolve()",
            "        if resolved != root and root not in resolved.parents:",
            "            fail('path_outside_root', f'{resolved} not under {root}')",
            "        if p.is_symlink():",
            "            fail('symlink_not_allowed', f'refusing to patch symlink: {p}')",
            "        if not p.is_file():",
            "            fail('not_file', f'refusing to patch non-regular file: {p}')",
            "        before[raw]=hashlib.sha256(p.read_bytes()).hexdigest()",
            "    else:",
            "        parent=p.parent.resolve()",
            "        if parent != root and root not in parent.parents:",
            "            fail('path_outside_root', f'{parent} not under {root}')",
            "        before[raw]=None",
            "pathlib.Path(sys.argv[1]).write_text(json.dumps(before), encoding='utf-8')",
            "REMOTE_DEV_BEFORE",
            "git apply --stat \"$tmp\" > \"$tmp_stat\" 2>&1 || true",
            "if ! git apply --check \"$tmp\" >/tmp/remote-dev-git-apply-check.out 2>&1; then",
            "  cat /tmp/remote-dev-git-apply-check.out >&2",
            "  rm -f \"$tmp\" \"$tmp_before\" \"$tmp_stat\" /tmp/remote-dev-git-apply-check.out",
            "  exit 73",
            "fi",
            "git apply \"$tmp\"",
            "python3 - \"$tmp_before\" \"$tmp_stat\" " + path_args + " <<'REMOTE_DEV_CHANGED'",
            "import hashlib, json, pathlib, sys",
            "before=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))",
            "diffstat=pathlib.Path(sys.argv[2]).read_text(encoding='utf-8')",
            "changed=[]",
            "for raw in sys.argv[3:]:",
            "    p=pathlib.Path(raw)",
            "    digest=None",
            "    size=0",
            "    if p.exists() and p.is_file():",
            "        data=p.read_bytes(); digest=hashlib.sha256(data).hexdigest(); size=len(data)",
            "    changed.append({'path': str(p), 'before_sha256': before.get(raw), 'after_sha256': digest, 'size': size})",
            "print(json.dumps({'status':'applied','changed_files':changed,'diffstat':diffstat}))",
            "REMOTE_DEV_CHANGED",
            "rm -f \"$tmp\" \"$tmp_before\" \"$tmp_stat\" /tmp/remote-dev-git-apply-check.out",
        ]
    )
    completed = run_script(endpoint, script, timeout_ms=timeout_ms)
    if completed.timed_out:
        return _patch_failed(endpoint, started, start, "timeout", "RemoteApplyPatch timed out", outcome="timeout")
    if completed.returncode == 72:
        error = completed.stderr[-4000:]
        status = "failed"
        for line in completed.stderr.splitlines():
            if line.startswith("REMOTE_DEV_PATCH_PREFLIGHT "):
                status = line.split(" ", 1)[1].split(":", 1)[0]
                break
        outcome = "blocked" if status in {"path_outside_root", "symlink_not_allowed", "not_file"} else "failed"
        return _patch_failed(endpoint, started, start, status, error, outcome=outcome)
    if completed.returncode == 73:
        return _patch_failed(endpoint, started, start, "context_mismatch", completed.stderr[-4000:])
    if completed.returncode != 0:
        return _patch_failed(endpoint, started, start, "failed", completed.stderr[-4000:])
    import json

    try:
        data = json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception as exc:  # noqa: BLE001
        return _patch_failed(endpoint, started, start, "failed", f"could not parse apply output: {exc}")
    return _patch_result(endpoint, started, start, cwd, data)


def _patch_failed(
    endpoint: Endpoint,
    started: str,
    start: float,
    status: str,
    error: str,
    *,
    outcome: str = "failed",
) -> dict[str, Any]:
    if status in {"path_outside_root", "context_mismatch"}:
        outcome = "blocked" if status == "path_outside_root" else "failed"
    result = make_result(
        tool="remote.apply_patch",
        target=endpoint.to_result_target(),
        outcome=outcome,  # type: ignore[arg-type]
        status=status,
        summary=f"RemoteApplyPatch {status}.",
        started_at=started,
        duration_ms=_duration_ms(start),
        preview={"stderr": error[-4000:]},
        extra={"error": error},
    )
    return {"text": result["summary"] + "\n" + error + "\n", "result": result}


def _patch_result(
    endpoint: Endpoint,
    started: str,
    start: float,
    cwd: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    status = str(data.get("status", "failed"))
    changed = data.get("changed_files", []) if isinstance(data.get("changed_files"), list) else []
    outcome = "success" if status == "applied" else ("blocked" if status in {"path_outside_root", "symlink_not_allowed", "not_file", "file_exists"} else "failed")
    patch_dir = ensure_endpoint_state(endpoint) / "patches"
    result = make_result(
        tool="remote.apply_patch",
        target={**endpoint.to_result_target(), "cwd": cwd},
        outcome=outcome,  # type: ignore[arg-type]
        status=status,
        summary=f"RemoteApplyPatch {status} on {endpoint.user}@{endpoint.host}:{endpoint.port}.",
        started_at=started,
        duration_ms=_duration_ms(start),
        preview={"diff": data.get("diff_preview", ""), "diffstat": data.get("diffstat", "")},
        changed_files=changed,
        extra={"error": data.get("error")},
    )
    ref_path = patch_dir / f"{result['invocation_id']}.json"
    result["refs"]["metadata"] = str(ref_path)
    atomic_write_json(ref_path, result)
    return {"text": _format_patch_text(endpoint, cwd, result), "result": result}


def _format_patch_text(endpoint: Endpoint, cwd: str, result: dict[str, Any]) -> str:
    lines = [
        f"RemoteApplyPatch {result['status']} on {endpoint.user}@{endpoint.host}:{endpoint.port}",
        f"cwd: {cwd}",
        "",
        "Changed:",
    ]
    for item in result.get("changed_files", []):
        lines.append(f"  M {item.get('path')}")
    preview = result.get("preview", {})
    if preview.get("diffstat"):
        lines.extend(["", "Diffstat:", str(preview["diffstat"])])
    if preview.get("diff"):
        lines.extend(["", "Diff preview:", str(preview["diff"])])
    if result.get("error"):
        lines.append(f"error: {result['error']}")
    return "\n".join(lines).rstrip() + "\n"
