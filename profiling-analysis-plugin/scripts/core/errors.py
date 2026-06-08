from __future__ import annotations


class RemoteDevError(RuntimeError):
    """Base class for deterministic remote-dev failures."""


class EndpointError(RemoteDevError):
    """Raised when an endpoint cannot be resolved."""


class PathPolicyError(RemoteDevError):
    """Raised when a remote path violates root/cwd policy."""


class RemoteExecutionError(RemoteDevError):
    """Raised when a remote command cannot be launched cleanly."""
