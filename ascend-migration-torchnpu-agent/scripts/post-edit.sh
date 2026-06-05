#!/usr/bin/env bash
# ==============================================================================
# PostToolUse hook — validates CUDA→NPU changes after Write/Edit operations.
# Runs after file writes or edits in Claude Code.
#
# NOTE: This script receives no arguments in the current Claude Code hook
# model. It checks recently modified Python files in the project directory
# for common CUDA references that should have been migrated.
# ==============================================================================

# Find the project root (current working directory, or git root if available)
PROJECT_ROOT="${PWD}"
if git rev-parse --show-toplevel &>/dev/null; then
    PROJECT_ROOT="$(git rev-parse --show-toplevel)"
fi

echo "[ascend-migration] PostToolUse: scanning for residual CUDA references..."

# Find Python files modified in the last 5 minutes
if [[ "$(uname)" == "Darwin" ]]; then
    # macOS: use -mmin via stat (approximate)
    RECENT_FILES=$(find "$PROJECT_ROOT" -name "*.py" -newer "$PROJECT_ROOT" -mmin -5 2>/dev/null | head -20)
else
    # Linux
    RECENT_FILES=$(find "$PROJECT_ROOT" -name "*.py" -mmin -5 2>/dev/null | head -20)
fi

# Fallback: check all Python files if no recent ones found
if [ -z "$RECENT_FILES" ]; then
    RECENT_FILES=$(find "$PROJECT_ROOT" -name "*.py" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -50)
fi

WARNINGS=0

check_pattern() {
    local pattern="$1"
    local label="$2"
    local replacement="$3"

    for f in $RECENT_FILES; do
        if [ -f "$f" ] && grep -n "$pattern" "$f" 2>/dev/null | grep -v "^[[:space:]]*#" | grep -v "torch_npu" | grep -v "torch.npu" > /tmp/ascend_check_$$.tmp; then
            if [ -s /tmp/ascend_check_$$.tmp ]; then
                while IFS= read -r line; do
                    echo "  ⚠️  ${label} in ${f}: ${line}"
                    echo "     → should be: ${replacement}"
                    ((WARNINGS++)) || true
                done < /tmp/ascend_check_$$.tmp
            fi
        fi
    done
    rm -f /tmp/ascend_check_$$.tmp
}

check_pattern '\.cuda()'              '.cuda()'          '.npu()'
check_pattern 'torch\.cuda\.'         'torch.cuda.*'     'torch.npu.*'
check_pattern 'backend.*=.*"nccl"'    'backend="nccl"'   'backend="hccl"'
check_pattern 'DataParallel'          'DataParallel'     'DistributedDataParallel'
check_pattern 'torch\.backends\.cudnn' 'torch.backends.cudnn' 'remove/condition-skip'

if [ "$WARNINGS" -eq 0 ]; then
    echo "  ✅ No residual CUDA references detected."
else
    echo "  ⚠️  ${WARNINGS} potential issue(s) found. Review the warnings above."
fi

echo "[ascend-migration] PostToolUse check complete."
