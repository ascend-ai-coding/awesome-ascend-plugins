from __future__ import annotations

MAX_TEXT_CHARS = 12000
MAX_READ_LINES = 500
MAX_JOB_TAIL_LINES = 500
MAX_GREP_MATCHES = 500
MAX_LINE_CHARS = 2000

DEFAULT_HEAD_CHARS = 4000
DEFAULT_TAIL_CHARS = 4000


def text_preview(
    value: str,
    *,
    head_chars: int = DEFAULT_HEAD_CHARS,
    tail_chars: int = DEFAULT_TAIL_CHARS,
) -> dict[str, object]:
    byte_count = len(value.encode("utf-8", errors="replace"))
    if len(value) <= head_chars + tail_chars:
        return {
            "text": value,
            "bytes": byte_count,
            "truncated": False,
            "head_chars": head_chars,
            "tail_chars": tail_chars,
        }
    return {
        "head": value[:head_chars],
        "tail": value[-tail_chars:],
        "bytes": byte_count,
        "truncated": True,
        "head_chars": head_chars,
        "tail_chars": tail_chars,
    }


def stdout_stderr_preview(stdout: str, stderr: str) -> dict[str, object]:
    return {
        "stdout": text_preview(stdout),
        "stderr": text_preview(stderr),
        "stdout_bytes": len(stdout.encode("utf-8", errors="replace")),
        "stderr_bytes": len(stderr.encode("utf-8", errors="replace")),
        "truncated": len(stdout) > DEFAULT_HEAD_CHARS + DEFAULT_TAIL_CHARS
        or len(stderr) > DEFAULT_HEAD_CHARS + DEFAULT_TAIL_CHARS,
        "head_chars": DEFAULT_HEAD_CHARS,
        "tail_chars": DEFAULT_TAIL_CHARS,
    }


def tail_text(value: str, limit: int = DEFAULT_TAIL_CHARS) -> str:
    return value if len(value) <= limit else value[-limit:]


def compact_text(value: str, *, limit: int = MAX_TEXT_CHARS) -> str:
    if len(value) <= limit:
        return value
    marker = "\n<remote-dev text truncated; full output is available via refs/resources>\n"
    keep = max(0, limit - len(marker))
    head = keep // 2
    tail = keep - head
    return value[:head] + marker + value[-tail:]
