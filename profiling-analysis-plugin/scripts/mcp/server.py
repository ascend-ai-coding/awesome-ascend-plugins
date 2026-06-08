#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

os.environ.setdefault("REMOTE_DEV_SESSION_ID", f"mcp-{os.getpid()}-{uuid.uuid4().hex[:8]}")

SUBSTRATE_ROOT = Path(__file__).resolve().parents[1]
if str(SUBSTRATE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUBSTRATE_ROOT))

from mcp.tools import call_tool, list_resources, list_tools, read_resource  # noqa: E402


def encode_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def send(payload: dict[str, Any], *, framed: bool = False) -> None:
    encoded = encode_payload(payload)
    if framed:
        sys.stdout.buffer.write(f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii"))
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
    else:
        sys.stdout.write(encoded.decode("utf-8") + "\n")
        sys.stdout.flush()


def result(request_id: Any, value: dict[str, Any], *, framed: bool = False) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "result": value}, framed=framed)


def error(request_id: Any, code: int, message: str, data: Any | None = None, *, framed: bool = False) -> None:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
    if data is not None:
        payload["error"]["data"] = data
    send(payload, framed=framed)


def handle(message: dict[str, Any], *, framed: bool = False) -> None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}
    if request_id is None and method and method.startswith("notifications/"):
        return
    try:
        if method == "initialize":
            result(
                request_id,
                {
                    "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": "remote-dev", "version": "0.1.0"},
                },
                framed=framed,
            )
        elif method == "tools/list":
            result(request_id, {"tools": list_tools()}, framed=framed)
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if not isinstance(name, str):
                raise ValueError("tools/call requires string name")
            if not isinstance(arguments, dict):
                raise ValueError("tools/call arguments must be an object")
            payload = call_tool(name, arguments)
            result(
                request_id,
                {
                    "content": [{"type": "text", "text": payload.get("text", "")}],
                    "structuredContent": payload.get("result", {}),
                    "isError": payload.get("result", {}).get("outcome") not in {"success", "cancelled"},
                },
                framed=framed,
            )
        elif method == "resources/list":
            result(request_id, {"resources": list_resources()}, framed=framed)
        elif method == "resources/read":
            content = read_resource(str(params.get("uri", "remote://endpoints")))
            result(request_id, {"contents": [content]}, framed=framed)
        else:
            error(request_id, -32601, f"method not found: {method}", framed=framed)
    except Exception as exc:  # noqa: BLE001
        error(request_id, -32000, str(exc), {"type": type(exc).__name__}, framed=framed)


def read_framed_messages() -> int:
    while True:
        headers: dict[str, str] = {}
        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                return 0
            if line in {b"\r\n", b"\n"}:
                break
            text = line.decode("ascii", errors="replace").strip()
            if ":" in text:
                key, value = text.split(":", 1)
                headers[key.lower()] = value.strip()
        length_text = headers.get("content-length")
        if not length_text:
            error(None, -32600, "missing Content-Length header", framed=True)
            continue
        body = sys.stdin.buffer.read(int(length_text))
        try:
            message = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            error(None, -32700, f"parse error: {exc}", framed=True)
            continue
        if isinstance(message, dict):
            handle(message, framed=True)
        else:
            error(None, -32600, "request must be an object", framed=True)


def read_line_messages() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            error(None, -32700, f"parse error: {exc}")
            continue
        if isinstance(message, dict):
            handle(message)
        else:
            error(None, -32600, "request must be an object")
    return 0


def main() -> int:
    try:
        peeked = sys.stdin.buffer.peek(16)
    except AttributeError:
        peeked = b""
    if peeked.startswith(b"Content-Length:"):
        return read_framed_messages()
    return read_line_messages()


if __name__ == "__main__":
    raise SystemExit(main())
