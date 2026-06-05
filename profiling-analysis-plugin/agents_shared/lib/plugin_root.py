#!/usr/bin/env python3
"""Centralized path anchors for the profiling-analysis plugin.

All skill scripts should import from this module instead of computing
``Path(__file__).resolve().parents[N]`` independently. This ensures
correct path resolution regardless of the installation layout.
"""
from __future__ import annotations

import os
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]

LIB_DIR = PLUGIN_ROOT / "agents_shared" / "lib"
INVENTORY_DIR = PLUGIN_ROOT / "agents_shared" / "inventory"
SKILLS_DIR = PLUGIN_ROOT / "skills"
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"

VAWS_LOCAL_DIRNAME = ".vaws-local"


def project_root() -> Path:
    """Return the user's project root for runtime state.

    Prefers the ``CLAUDE_PROJECT_ROOT`` environment variable. Falls back
    to the current working directory.
    """
    env = os.environ.get("CLAUDE_PROJECT_ROOT")
    if env:
        return Path(env)
    return Path.cwd()


def vaws_local_dir() -> Path:
    return project_root() / VAWS_LOCAL_DIRNAME
