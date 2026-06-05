# Changelog

All notable changes to the Ascend Migration torch_npu Agent plugin.

## [2.0.0] — 2026-06-05

### Added
- **`install.sh`** — One-command cross-platform installer with auto-detection of Claude Code and OpenCode
- **`uninstall.sh`** — Convenience wrapper for clean removal
- **`README.zh-CN.md`** — Complete Chinese documentation
- **`CHANGELOG.md`** — This file
- **`.gitignore`** — Proper open-source .gitignore for privacy protection
- **Idempotent installation** — Safe to run `install.sh` multiple times
- **Hooks merging** — Uses Python-based JSON merge to preserve existing user hooks
- **Installation validation** — Post-install verification of all components
- **`--claude` / `--opencode` flags** — Tool-specific installation options
- **Marketplace-ready `plugin.json`** — Updated metadata with repository URL, keywords, min version

### Changed
- **`README.md`** — Rewritten with correct installation steps, troubleshooting, and manual fallback
- **`hooks/hooks.json`** — Added `manual_setup` section documenting the settings.json snippet for users who can't use install.sh; removed dependency on `${CLAUDE_PLUGIN_ROOT}` at runtime (resolved at install time)
- **`scripts/session-start.sh`** — Added error handling, cross-platform compatibility, and doc comment explaining hook behaviour
- **`scripts/post-edit.sh`** — Rewritten to scan recent Python files rather than relying on unconfirmed `$1` argument; added macOS/Linux compatibility

### Fixed
- **Installation instructions** — `claude plugins install .` doesn't work in Claude Code 2.x (only marketplace installs supported); now using `./install.sh`
- **`${CLAUDE_PLUGIN_ROOT}` variable** — Resolved to absolute paths at install time instead of relying on an undefined env var
- **SessionStart context injection** — Documented that `command`-type hooks display to terminal, not inject context; the primary mechanism is the agent/skills system

### Removed
- Nothing removed; all original skills and agent definitions preserved

## [1.0.0] — Original Release

- Initial release by Gongdayao
- 5 skills: workflow orchestration, migration execution, environment setup, API reference, troubleshooting
- 1 agent: ascend-migration-torchnpu-agent
- 2 hooks: SessionStart + PostToolUse
- Migration report template
- Basic `claude plugins install .` instruction (does not work in Claude Code 2.x)
