from __future__ import annotations

import re

SECRET_ARG_RE = re.compile(r"(?i)(sshpass|expect\b|--password(?:=|\s+)\S+|password=\S+|token=\S+|api[_-]?key=\S+)")
RAW_REMOTE_RE = re.compile(r"(^|\s)(ssh|scp|sftp|rsync)\b")


def contains_secret_in_argv(command: str) -> bool:
    return bool(SECRET_ARG_RE.search(command))


def contains_raw_remote_transport(command: str) -> bool:
    return bool(RAW_REMOTE_RE.search(command))
