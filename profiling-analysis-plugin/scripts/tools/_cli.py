from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _bootstrap import add_substrate_to_path

add_substrate_to_path()

from core.artifact_ops import remote_artifact_manifest, remote_artifact_pull, remote_artifact_push  # noqa: E402
from core.context_snapshot import remote_context_snapshot, remote_probe  # noqa: E402
from core.endpoint import EndpointError, resolve_endpoint  # noqa: E402
from core.file_ops import remote_edit, remote_ls, remote_multi_edit, remote_read, remote_write  # noqa: E402
from core.job_ops import remote_job_status, remote_job_stop, remote_job_tail  # noqa: E402
from core.patch_ops import remote_apply_patch  # noqa: E402
from core.result import make_result  # noqa: E402
from core.search_ops import remote_glob, remote_grep  # noqa: E402
from core.shell_ops import remote_bash  # noqa: E402


def add_endpoint_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--user", default=None)
    parser.add_argument("--root", default=None)
    parser.add_argument("--cwd", default=None)
    parser.add_argument("--runtime-env", dest="runtime_env", action="store_true", default=None)
    parser.add_argument("--no-runtime-env", dest="runtime_env", action="store_false")
    parser.add_argument("--identity-file")
    parser.add_argument("--connect-timeout-ms", type=int)
    parser.add_argument("--alias")
    parser.add_argument("--session-id")
    parser.add_argument("--session-file")
    parser.add_argument("--machine")


def endpoint_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in (
        "host",
        "port",
        "user",
        "root",
        "cwd",
        "runtime_env",
        "identity_file",
        "connect_timeout_ms",
        "alias",
        "session_id",
        "session_file",
        "machine",
    ):
        value = getattr(args, key, None)
        if value is not None:
            payload[key] = value
    return payload


def parse_env(items: list[str] | None) -> dict[str, str]:
    env: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"bad --env item {item!r}; expected KEY=VALUE")
        key, value = item.split("=", 1)
        env[key] = value
    return env


def print_payload(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("result", {}).get("outcome") in {"success", "cancelled"} else 1


def error_payload(tool: str, *, outcome: str, status: str, error: str) -> dict[str, Any]:
    result = make_result(
        tool=f"remote.{tool}",
        target={"kind": "unresolved"},
        outcome=outcome,  # type: ignore[arg-type]
        status=status,
        summary=f"remote.{tool} {status}.",
        preview={"stderr": error[-4000:]},
        extra={"error": error},
    )
    return {"text": result["summary"] + "\n" + error + "\n", "result": result}


def build_parser(tool: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=f"remote-{tool.replace('_', '-')}")
    add_endpoint_args(parser)
    parser.add_argument("--input-json", help="Read complete tool arguments from a JSON file, or '-' for stdin.")
    parser.add_argument("--timeout-ms", type=int, default=120000)
    parser.add_argument("--client-context-id")
    if tool == "bash":
        parser.add_argument("--command", required=False)
        parser.add_argument("--description")
        parser.add_argument("--run-in-background", action="store_true")
        parser.add_argument("--env", action="append")
    elif tool == "read":
        parser.add_argument("--file-path", required=False)
        parser.add_argument("--offset", type=int, default=1)
        parser.add_argument("--limit", type=int, default=200)
        parser.add_argument("--allow-symlink", action="store_true")
    elif tool == "ls":
        parser.add_argument("--path")
        parser.add_argument("--limit", type=int, default=200)
        parser.add_argument("--all", action="store_true")
    elif tool == "write":
        parser.add_argument("--file-path", required=False)
        parser.add_argument("--content")
        parser.add_argument("--content-file")
        parser.add_argument("--overwrite", action="store_true")
        parser.add_argument("--create-dirs", action="store_true")
    elif tool == "edit":
        parser.add_argument("--file-path", required=False)
        parser.add_argument("--old-string")
        parser.add_argument("--new-string")
        parser.add_argument("--replace-all", action="store_true")
    elif tool == "multi_edit":
        parser.add_argument("--file-path", required=False)
        parser.add_argument("--edits-json")
    elif tool == "glob":
        parser.add_argument("--pattern", required=False)
        parser.add_argument("--path")
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--respect-gitignore", action="store_true")
    elif tool == "grep":
        parser.add_argument("--pattern", required=False)
        parser.add_argument("--path")
        parser.add_argument("--glob")
        parser.add_argument("--type")
        parser.add_argument("--output-mode", default="files_with_matches", choices=["files_with_matches", "content", "count"])
        parser.add_argument("--multiline", action="store_true")
        parser.add_argument("--limit", type=int, default=100)
    elif tool == "apply_patch":
        parser.add_argument("--patch")
        parser.add_argument("--patch-file")
        parser.add_argument("--command")
    elif tool in {"job_status", "job_tail", "job_stop"}:
        parser.add_argument("--job-id", required=False)
        if tool == "job_tail":
            parser.add_argument("--lines", type=int, default=80)
            parser.add_argument("--stream", default="both", choices=["stdout", "stderr", "both"])
        if tool == "job_stop":
            parser.add_argument("--force", action="store_true")
    elif tool in {"artifact_manifest", "artifact_pull", "artifact_push"}:
        parser.add_argument("--remote-path", required=False)
        if tool == "artifact_pull":
            parser.add_argument("--local-dir")
        if tool == "artifact_push":
            parser.add_argument("--local-path")
    elif tool == "monitor":
        parser.add_argument("--command", required=False)
        parser.add_argument("--description")
        parser.add_argument("--pattern")
        parser.add_argument("--env", action="append")
    elif tool == "context_snapshot":
        parser.add_argument("--no-live-probe", action="store_true")
    elif tool == "probe":
        pass
    return parser


def load_input_json(path: str) -> dict[str, Any]:
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("--input-json must be a JSON object")
    return data


def run_tool(tool: str, args: argparse.Namespace) -> dict[str, Any]:
    data = load_input_json(args.input_json) if args.input_json else {}
    data = {**endpoint_payload(args), **data}
    endpoint = None
    if tool not in {"job_status", "job_tail", "job_stop"} or any(data.get(k) for k in ("host", "port", "alias", "session_id", "session_file", "machine")):
        endpoint = resolve_endpoint(data)
    timeout_ms = int(data.get("timeout_ms") or args.timeout_ms)
    if tool == "bash":
        assert endpoint is not None
        return remote_bash(endpoint, command=data.get("command") or args.command or "", cwd=data.get("cwd"), description=data.get("description") or args.description, timeout_ms=timeout_ms, run_in_background=bool(data.get("run_in_background", args.run_in_background)), runtime_env=data.get("runtime_env"), env=data.get("env") if isinstance(data.get("env"), dict) else parse_env(args.env))
    if tool == "monitor":
        assert endpoint is not None
        return remote_bash(endpoint, command=data.get("command") or args.command or "", cwd=data.get("cwd"), description=data.get("description") or args.description, timeout_ms=timeout_ms, run_in_background=True, runtime_env=data.get("runtime_env"), env=data.get("env") if isinstance(data.get("env"), dict) else parse_env(args.env))
    if tool == "read":
        assert endpoint is not None
        return remote_read(endpoint, file_path=data.get("file_path") or args.file_path, offset=int(data.get("offset", args.offset)), limit=int(data.get("limit", args.limit)), allow_symlink=bool(data.get("allow_symlink", args.allow_symlink)), client_context_id=data.get("client_context_id") or args.client_context_id, timeout_ms=timeout_ms)
    if tool == "ls":
        assert endpoint is not None
        return remote_ls(endpoint, path=data.get("path") or args.path, limit=int(data.get("limit", args.limit)), all=bool(data.get("all", args.all)), timeout_ms=timeout_ms)
    if tool == "write":
        assert endpoint is not None
        content = data.get("content")
        if content is None and args.content_file:
            content = Path(args.content_file).read_text(encoding="utf-8")
        return remote_write(endpoint, file_path=data.get("file_path") or args.file_path, content=str(content or ""), overwrite=bool(data.get("overwrite", args.overwrite)), create_dirs=bool(data.get("create_dirs", args.create_dirs)), client_context_id=data.get("client_context_id") or args.client_context_id, timeout_ms=timeout_ms)
    if tool == "edit":
        assert endpoint is not None
        return remote_edit(endpoint, file_path=data.get("file_path") or args.file_path, old_string=data.get("old_string") if data.get("old_string") is not None else args.old_string, new_string=data.get("new_string") if data.get("new_string") is not None else args.new_string, replace_all=bool(data.get("replace_all", args.replace_all)), client_context_id=data.get("client_context_id") or args.client_context_id, timeout_ms=timeout_ms)
    if tool == "multi_edit":
        assert endpoint is not None
        edits = data.get("edits")
        if edits is None and args.edits_json:
            edits = json.loads(args.edits_json)
        return remote_multi_edit(endpoint, file_path=data.get("file_path") or args.file_path, edits=edits or [], client_context_id=data.get("client_context_id") or args.client_context_id, timeout_ms=timeout_ms)
    if tool == "glob":
        assert endpoint is not None
        return remote_glob(endpoint, pattern=data.get("pattern") or args.pattern or "*", path=data.get("path") or args.path, limit=int(data.get("limit", args.limit)), respect_gitignore=bool(data.get("respect_gitignore", args.respect_gitignore)), timeout_ms=timeout_ms)
    if tool == "grep":
        assert endpoint is not None
        return remote_grep(endpoint, pattern=data.get("pattern") or args.pattern or "", path=data.get("path") or args.path, glob=data.get("glob") or args.glob, type=data.get("type") or args.type, output_mode=data.get("output_mode") or args.output_mode, multiline=bool(data.get("multiline", args.multiline)), limit=int(data.get("limit", args.limit)), timeout_ms=timeout_ms)
    if tool == "apply_patch":
        assert endpoint is not None
        patch = data.get("patch") or args.patch
        if patch is None and args.patch_file:
            patch = Path(args.patch_file).read_text(encoding="utf-8")
        return remote_apply_patch(endpoint, patch=patch, command=data.get("command") or args.command, cwd=data.get("cwd"), timeout_ms=timeout_ms)
    if tool == "job_status":
        return remote_job_status(endpoint, job_id=data.get("job_id") or args.job_id)
    if tool == "job_tail":
        return remote_job_tail(endpoint, job_id=data.get("job_id") or args.job_id, lines=int(data.get("lines", args.lines)), stream=data.get("stream") or args.stream)
    if tool == "job_stop":
        return remote_job_stop(endpoint, job_id=data.get("job_id") or args.job_id, force=bool(data.get("force", args.force)))
    if tool == "artifact_manifest":
        assert endpoint is not None
        return remote_artifact_manifest(endpoint, remote_path=data.get("remote_path") or args.remote_path, timeout_ms=timeout_ms)
    if tool == "artifact_pull":
        assert endpoint is not None
        return remote_artifact_pull(endpoint, remote_path=data.get("remote_path") or args.remote_path, local_dir=data.get("local_dir") or args.local_dir, timeout_ms=timeout_ms)
    if tool == "artifact_push":
        assert endpoint is not None
        return remote_artifact_push(endpoint, local_path=data.get("local_path") or args.local_path, remote_path=data.get("remote_path") or args.remote_path, timeout_ms=timeout_ms)
    if tool == "context_snapshot":
        assert endpoint is not None
        return remote_context_snapshot(endpoint, timeout_ms=timeout_ms, live_probe=not bool(data.get("no_live_probe", args.no_live_probe)))
    if tool == "probe":
        assert endpoint is not None
        return remote_probe(endpoint, timeout_ms=timeout_ms)
    raise ValueError(f"unsupported tool: {tool}")


def main(tool: str) -> int:
    parser = build_parser(tool)
    args = parser.parse_args()
    try:
        return print_payload(run_tool(tool, args))
    except EndpointError as exc:
        return print_payload(error_payload(tool, outcome="needs_input", status="endpoint_required", error=str(exc)))
    except FileNotFoundError as exc:
        return print_payload(error_payload(tool, outcome="needs_input", status="not_found", error=str(exc)))
    except ValueError as exc:
        return print_payload(error_payload(tool, outcome="needs_input", status="invalid_input", error=str(exc)))
    except Exception as exc:  # noqa: BLE001
        return print_payload(error_payload(tool, outcome="failed", status="exception", error=f"{type(exc).__name__}: {exc}"))
