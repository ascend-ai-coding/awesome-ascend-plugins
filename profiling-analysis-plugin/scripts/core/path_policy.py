from __future__ import annotations

import posixpath

from .errors import PathPolicyError


def normalize_remote_path(path: str) -> str:
    if not isinstance(path, str) or not path:
        raise PathPolicyError("remote path must be a non-empty string")
    normalized = posixpath.normpath(path)
    if not normalized.startswith("/"):
        raise PathPolicyError(f"remote path must be absolute: {path!r}")
    return normalized


def assert_under_root(path: str, root: str) -> str:
    normalized = normalize_remote_path(path)
    normalized_root = normalize_remote_path(root)
    if normalized == normalized_root:
        return normalized
    if not normalized.startswith(normalized_root.rstrip("/") + "/"):
        raise PathPolicyError(f"remote path is outside root: {normalized} not under {normalized_root}")
    return normalized


def join_under_root(root: str, cwd: str, rel_or_abs: str) -> str:
    candidate = rel_or_abs if rel_or_abs.startswith("/") else posixpath.join(cwd, rel_or_abs)
    return assert_under_root(candidate, root)


def path_fingerprint(path: str) -> str:
    import hashlib

    return hashlib.sha256(normalize_remote_path(path).encode("utf-8")).hexdigest()[:24]
