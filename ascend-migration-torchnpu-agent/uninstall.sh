#!/usr/bin/env bash
# ==============================================================================
# Ascend Migration torch_npu Agent — Uninstaller
# ==============================================================================
# Convenience wrapper around: install.sh --uninstall
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/install.sh" --uninstall "$@"
