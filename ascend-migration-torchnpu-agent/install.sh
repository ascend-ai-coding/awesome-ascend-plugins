#!/usr/bin/env bash
# ==============================================================================
# Ascend Migration torch_npu Agent — Installer
# ==============================================================================
# Installs this plugin for Claude Code and/or OpenCode.
# Safe to run multiple times (idempotent).
#
# Usage:
#   ./install.sh              # Auto-detect available tools, install for all
#   ./install.sh --claude     # Install for Claude Code only
#   ./install.sh --opencode   # Install for OpenCode only
#   ./install.sh --uninstall  # Remove all installed components
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_NAME="ascend-migration-torchnpu-agent"
INSTALL_DIR="${HOME}/.claude/plugins-installed/${PLUGIN_NAME}"

# ---- colour helpers ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { printf "${GREEN}[INFO]${NC}  %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
err()   { printf "${RED}[ERR]${NC}   %s\n" "$*"; }
step()  { printf "${CYAN}[STEP]${NC}  %s\n" "$*"; }

# ---- detect available tools ----
detect_tools() {
    TOOLS=()
    if command -v claude &>/dev/null; then
        TOOLS+=("claude")
        info "Claude Code detected: $(claude --version 2>&1 | head -1)"
    fi
    if [ -d "${HOME}/.config/opencode" ] || command -v opencode &>/dev/null; then
        TOOLS+=("opencode")
        info "OpenCode detected"
    fi
    if [ ${#TOOLS[@]} -eq 0 ]; then
        err "Neither Claude Code nor OpenCode detected."
        err "Please install one of them first:"
        err "  Claude Code: https://docs.anthropic.com/en/docs/claude-code/overview"
        err "  OpenCode:    https://github.com/opencode-ai/opencode"
        exit 1
    fi
}

# ---- install for Claude Code ----
install_claude() {
    step "Installing for Claude Code..."

    # 1. Copy agent definition
    mkdir -p "${HOME}/.claude/agents"
    cp "${SCRIPT_DIR}/agents/${PLUGIN_NAME}.md" "${HOME}/.claude/agents/"
    info "  Agent → ~/.claude/agents/${PLUGIN_NAME}.md"

    # 2. Copy skills
    mkdir -p "${HOME}/.claude/skills"
    for skill_dir in "${SCRIPT_DIR}/skills/"*/; do
        skill_name="$(basename "$skill_dir")"
        if [ -f "${skill_dir}SKILL.md" ]; then
            rm -rf "${HOME}/.claude/skills/${skill_name}"
            cp -r "$skill_dir" "${HOME}/.claude/skills/${skill_name}"
            info "  Skill  → ~/.claude/skills/${skill_name}/"
        fi
    done

    # 3. Install plugin scripts to a fixed location
    mkdir -p "${INSTALL_DIR}/scripts"
    cp "${SCRIPT_DIR}/scripts/"*.sh "${INSTALL_DIR}/scripts/"
    chmod +x "${INSTALL_DIR}/scripts/"*.sh
    mkdir -p "${INSTALL_DIR}/templates"
    cp "${SCRIPT_DIR}/templates/"* "${INSTALL_DIR}/templates/" 2>/dev/null || true
    info "  Scripts → ${INSTALL_DIR}/scripts/"

    # 4. Merge hooks into settings.json
    _merge_hooks_claude

    info "Claude Code installation complete."
}

_merge_hooks_claude() {
    local settings_file="${HOME}/.claude/settings.json"
    local hooks_json="${SCRIPT_DIR}/hooks/hooks.json"

    step "Configuring hooks in ~/.claude/settings.json..."

    # Ensure settings.json exists
    if [ ! -f "$settings_file" ]; then
        echo '{}' > "$settings_file"
    fi

    # Use python for reliable JSON merging (available on both macOS and Linux)
    python3 - "$settings_file" "$INSTALL_DIR" "$PLUGIN_NAME" <<'PYEOF'
import sys, json, os

settings_path = sys.argv[1]
install_dir   = sys.argv[2]
plugin_name   = sys.argv[3]

with open(settings_path, 'r') as f:
    settings = json.load(f)

# Hooks to inject (using absolute paths, not ${CLAUDE_PLUGIN_ROOT})
new_hooks = {
    "SessionStart": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": f"{install_dir}/scripts/session-start.sh",
                    "timeout": 30
                }
            ]
        }
    ],
    "PostToolUse": [
        {
            "matcher": "Write|Edit",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{install_dir}/scripts/post-edit.sh",
                    "timeout": 15
                }
            ]
        }
    ]
}

# Ensure 'hooks' key exists
if "hooks" not in settings:
    settings["hooks"] = {}

existing = settings["hooks"]

# Helper: check if a hook entry is already present
def hook_exists(hook_list, new_entry):
    for entry in hook_list:
        for h in entry.get("hooks", []):
            for nh in new_entry.get("hooks", []):
                if h.get("command") == nh.get("command"):
                    return True
    return False

# Merge SessionStart hooks
if "SessionStart" not in existing:
    existing["SessionStart"] = []
for entry in new_hooks.get("SessionStart", []):
    if not hook_exists(existing["SessionStart"], entry):
        existing["SessionStart"].append(entry)

# Merge PostToolUse hooks
if "PostToolUse" not in existing:
    existing["PostToolUse"] = []
for entry in new_hooks.get("PostToolUse", []):
    if not hook_exists(existing["PostToolUse"], entry):
        existing["PostToolUse"].append(entry)

with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print(f"  Hooks merged into {settings_path}")
print(f"  NOTE: Restart Claude Code for hooks to take effect.")
PYEOF
}

# ---- install for OpenCode ----
install_opencode() {
    step "Installing for OpenCode..."

    local skills_dst="${HOME}/.config/opencode/skills"
    local agents_dst="${HOME}/.config/opencode/agents"

    mkdir -p "$skills_dst"
    mkdir -p "$agents_dst"

    # Copy skills
    for skill_dir in "${SCRIPT_DIR}/skills/"*/; do
        skill_name="$(basename "$skill_dir")"
        if [ -f "${skill_dir}SKILL.md" ]; then
            rm -rf "${skills_dst}/${skill_name}"
            cp -r "$skill_dir" "${skills_dst}/${skill_name}"
            info "  Skill  → ${skills_dst}/${skill_name}/"
        fi
    done

    # Copy agent
    cp "${SCRIPT_DIR}/agents/${PLUGIN_NAME}.md" "${agents_dst}/"
    info "  Agent  → ${agents_dst}/${PLUGIN_NAME}.md"

    info "OpenCode installation complete."
}

# ---- uninstall ----
do_uninstall() {
    step "Uninstalling ${PLUGIN_NAME}..."

    # Remove Claude Code components
    rm -f "${HOME}/.claude/agents/${PLUGIN_NAME}.md"
    for skill_dir in "${SCRIPT_DIR}/skills/"*/; do
        skill_name="$(basename "$skill_dir")"
        rm -rf "${HOME}/.claude/skills/${skill_name}" 2>/dev/null || true
    done
    rm -rf "${INSTALL_DIR}"

    # Remove OpenCode components
    rm -f "${HOME}/.config/opencode/agents/${PLUGIN_NAME}.md"
    for skill_dir in "${SCRIPT_DIR}/skills/"*/; do
        skill_name="$(basename "$skill_dir")"
        rm -rf "${HOME}/.config/opencode/skills/${skill_name}" 2>/dev/null || true
    done

    # Remove hooks from settings.json (best-effort)
    local settings_file="${HOME}/.claude/settings.json"
    if [ -f "$settings_file" ]; then
        python3 - "$settings_file" "$INSTALL_DIR" <<'PYEOF'
import sys, json

settings_path = sys.argv[1]
install_dir   = sys.argv[2]

with open(settings_path, 'r') as f:
    settings = json.load(f)

if "hooks" in settings:
    hooks = settings["hooks"]

    # Remove SessionStart entries that reference our scripts
    for key in ("SessionStart", "PostToolUse"):
        if key in hooks:
            hooks[key] = [
                entry for entry in hooks[key]
                if not any(
                    install_dir in h.get("command", "")
                    for h in entry.get("hooks", [])
                )
            ]
            if not hooks[key]:
                del hooks[key]

    # Remove empty hooks
    if not hooks:
        del settings["hooks"]

with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
print("  Hooks removed from settings.json")
PYEOF
    fi

    info "Uninstallation complete."
    info "NOTE: You may want to restart Claude Code for changes to take effect."
}

# ---- validate installation ----
validate() {
    step "Validating installation..."

    local errors=0

    if [[ " ${TOOLS[*]} " =~ " claude " ]]; then
        # Check agent
        if [ -f "${HOME}/.claude/agents/${PLUGIN_NAME}.md" ]; then
            info "  ✅ Agent installed"
        else
            err "  ❌ Agent missing: ~/.claude/agents/${PLUGIN_NAME}.md"
            ((errors++))
        fi

        # Check at least one skill
        if ls "${HOME}/.claude/skills/migration-ascend-torchnpu-skills/SKILL.md" &>/dev/null; then
            info "  ✅ Skills installed"
        else
            err "  ❌ Skills missing"
            ((errors++))
        fi

        # Check scripts
        if [ -x "${INSTALL_DIR}/scripts/session-start.sh" ]; then
            info "  ✅ Scripts installed"
        else
            err "  ❌ Scripts missing or not executable"
            ((errors++))
        fi

        # Check hooks in settings.json
        if grep -q "ascend-migration" "${HOME}/.claude/settings.json" 2>/dev/null; then
            info "  ✅ Hooks configured"
        else
            warn "  ⚠️  Hooks may not be in settings.json (check manually)"
        fi
    fi

    if [[ " ${TOOLS[*]} " =~ " opencode " ]]; then
        if [ -f "${HOME}/.config/opencode/agents/${PLUGIN_NAME}.md" ]; then
            info "  ✅ OpenCode agent installed"
        else
            warn "  ⚠️  OpenCode agent missing"
        fi
    fi

    if [ $errors -gt 0 ]; then
        err "Validation found ${errors} error(s). Re-run ./install.sh to fix."
        return 1
    fi

    info "All validations passed!"
    echo ""
    info "Usage: after restarting Claude Code, try:"
    echo "    /ascend-migration-torchnpu-agent"
    echo "  or say: 'migrate this model to run on Ascend NPU'"
}

# ---- main ----
main() {
    echo ""
    echo "============================================"
    echo "  Ascend Migration torch_npu Agent"
    echo "  Installer v2.0.0"
    echo "============================================"
    echo ""

    # Parse arguments
    DO_CLAUDE=false
    DO_OPENCODE=false
    DO_UNINSTALL=false

    if [ $# -eq 0 ]; then
        # Default: auto-detect and install for all
        detect_tools
        DO_CLAUDE=true
        DO_OPENCODE=true
    else
        for arg in "$@"; do
            case "$arg" in
                --claude)   DO_CLAUDE=true ;;
                --opencode) DO_OPENCODE=true ;;
                --uninstall) DO_UNINSTALL=true ;;
                --help|-h)
                    echo "Usage: $0 [--claude] [--opencode] [--uninstall]"
                    exit 0
                    ;;
                *)
                    err "Unknown option: $arg"
                    echo "Usage: $0 [--claude] [--opencode] [--uninstall]"
                    exit 1
                    ;;
            esac
        done
        detect_tools
    fi

    if [ "$DO_UNINSTALL" = true ]; then
        do_uninstall
        exit 0
    fi

    # Install
    if [ "$DO_CLAUDE" = true ] && [[ " ${TOOLS[*]} " =~ " claude " ]]; then
        install_claude
    fi

    if [ "$DO_OPENCODE" = true ] && [[ " ${TOOLS[*]} " =~ " opencode " ]]; then
        install_opencode
    fi

    echo ""
    validate
}

main "$@"
